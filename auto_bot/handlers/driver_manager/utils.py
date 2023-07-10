from datetime import datetime, time, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg
from django.utils import timezone

from app.models import Fleets_drivers_vehicles_rate, CarEfficiency, Payments, Driver, SummaryReport
from auto.tasks import logger
from selenium_ninja.uagps_sync import UaGpsSynchronizer


def calculate_reports(fleet_reports):
    totals = {}
    salary = {}
    reports = {}
    for driver in Driver.objects.all():
        r = list((r for r in fleet_reports if r.driver_id == driver.get_driver_external_id(r.vendor_name)))
        if r:
            r = r[0]
            name = driver.full_name()
            reports[name] = reports.get(name, '') + r.report_text(name, float(rate.driver.rate)) + '\n'
            totals[name] = totals.get(name, 0) + r.kassa()
            salary[name] = salary.get(name, 0) + r.total_drivers_amount(float(rate.driver.rate))

    totals = {k: v for k, v in totals.items() if v != 0.0}
    return totals, salary, reports


def send_weekly_report(manager_id):
    owner = {"Fleet Owner": 0}
    end = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday() + 1)
    start = end - timedelta(days=6)
    for driver in Driver.objects.all():
        driver_report = SummaryReport.objects.filter(report_from__date__range=(start, end),
                                                     full_name=driver)






        message = f"Загальна каса {driver}: %.2f\n" % driver_report.kassa()
    totals = {k: f'Загальна каса {k}: %.2f\n' % v for k, v in totals.items()}
    totals = {k: v + reports[k] for k, v in totals.items()}
    for k, v in totals.items():
        for driver in Driver.objects.all():
            if driver.full_name() == k and driver.schema == 'RENT':
                totals[
                    k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]} - Оренда ({'%.2f' % -driver.rental}) = {'%.2f' % (salary[k] - driver.rental)}\n" + "-" * 39
                owner["Fleet Owner"] += driver.rental
            elif driver.full_name() == k and driver.schema == 'HALF':
                if plan[k] < driver.plan:
                    owner["Fleet Owner"] += driver.rental
                    incomplete = (driver.plan - plan[k]) * float(1 - driver.rate)
                    totals[
                        k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]} - План ({'%.2f' % -incomplete}) = {'%.2f' % (salary[k] - incomplete)}\n" + "-" * 39
                else:
                    owner["Fleet Owner"] += plan[k] * float(1 - driver.rate)
                    totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]}\n" + "-" * 39
            else:
                pass
    return owner, totals, plan, manager_id


def get_car_efficiency(driver, day=None):
    efficiency = CarEfficiency.objects.filter(start_report=timezone.localize(datetime.combine(day, time.min)),
                                              end_report=timezone.localize(datetime.combine(day, time.max)),
                                              driver=driver)
    if not efficiency:
        try:
            total_km = UaGpsSynchronizer().total_per_day(driver, day)
            reports = Payments.objects.filter(report_from__date=day)
            total_kasa = calculate_reports(reports)[0]
            if total_km and total_kasa.get(driver.full_name()):
                result = Decimal(total_kasa[driver.full_name()])/Decimal(total_km)
                CarEfficiency.objects.create(start_report=day,
                                             end_report=day,
                                             driver=driver,
                                             mileage=total_km,
                                             efficiency=result)
            else:
                CarEfficiency.objects.create(start_report=day,
                                             end_report=day,
                                             driver=driver,
                                             mileage=total_km or 0,
                                             efficiency=0)
        except Exception as e:
            logger.info(e)


def calculate_efficiency(driver, start, end):
    current_date = start
    while current_date <= end:
        get_car_efficiency(driver, current_date)
        current_date += timedelta(days=1)
    end_period = timezone.localtime() - timedelta(days=1)
    all_objects = CarEfficiency.objects.filter(start_report__range=[start, end],
                                               driver=driver)
    efficiency_objects = all_objects.exclude(efficiency=0)
    yesterday_efficiency = CarEfficiency.objects.filter(start_report=end_period,
                                                        driver=driver).first()
    efficiency = float(yesterday_efficiency.efficiency) if yesterday_efficiency else 0
    distance = float(yesterday_efficiency.mileage) if yesterday_efficiency else 0
    average_efficiency = efficiency_objects.aggregate(avg_efficiency=Avg('efficiency'))['avg_efficiency']
    total_distance = efficiency_objects.aggregate(total_distance=Sum('mileage'))['total_distance']
    formatted_efficiency = float('{:.2f}'.format(average_efficiency)) if average_efficiency is not None else 0.00
    formatted_distance = float('{:.2f}'.format(total_distance)) if total_distance is not None else 0.00
    return formatted_efficiency, efficiency, formatted_distance, distance


def send_efficiency_report(self, start=None, end=None):
    try:
        total_values = {}
        report_values = {}
        effective_driver = {}
        effective_report = {}
        day_reports = Payments.objects.filter(report_from__date=start)
        day_totals = calculate_reports(day_reports)[0]
        if start and end:
            reports = Payments.objects.filter(report_from__date__range=(start, end))
        else:
            start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
            end = timezone.localtime().date()
            reports = Payments.objects.filter(report_from__date__range=(start, end))
        kassa = calculate_reports(reports)[0]
        for key, value in kassa.items():
            total_values[key] = total_values.get(key, 0) + value
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        for key in sort_report:
            report_values[key] = "Всього: {:.2f} Учора: (+{:.2f})".format(sort_report[key], day_totals.get(key, 0))
        for driver in Driver.objects.filter(vehicle__isnull=False):
            effect = calculate_efficiency(driver, start, end)
            effective_driver[driver.full_name()] = {'Середня ефективність(грн/км)': effect[0],
                                                    'Ефективність(грн/км)': effect[1],
                                                    'КМ за тиждень': effect[2],
                                                    'КМ учора': effect[3]}
        sorted_effective_driver = dict(sorted(effective_driver.items(),
                                       key=lambda x: x[1]['Середня ефективність(грн/км)'],
                                       reverse=True))
        message = [f'{k}:\n{v}' for k, v in report_values.items()]
        for k, v in sorted_effective_driver.items():
            effective_report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
        effect_message = [f'{k}:\n' + ''.join(v) for k, v in effective_report.items()]
        return message, effect_message
    except Exception as e:
        logger.error(e)
