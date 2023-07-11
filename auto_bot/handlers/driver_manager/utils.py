from datetime import datetime, time, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg, FloatField, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import Fleets_drivers_vehicles_rate, CarEfficiency, Payments, Driver, SummaryReport
from selenium_ninja.uagps_sync import UaGpsSynchronizer


def calculate_reports(start, end, driver):
    incomplete = 0
    driver_report = SummaryReport.objects.filter(report_from__range=(start, end),
                                                 full_name=driver)
    kasa = driver_report.aggregate(
        kasa=Coalesce(Sum('total_amount_without_fee'), 0, output_field=DecimalField()))['kasa']
    cash = driver_report.aggregate(
        cash=Coalesce(Sum('total_amount_cash'), 0, output_field=DecimalField()))['cash']
    if kasa:
        if driver.schema == "HALF":
            if kasa < driver.plan:
                balance = driver.rental
                incomplete = (driver.plan - kasa) * Decimal(1 - driver.rate)
                salary = '%.2f' % (kasa * driver.rate - cash - incomplete)
            else:
                balance = kasa * driver.rate
                salary = '%.2f' % (kasa * driver.rate - cash)
        elif driver.schema == "RENT":
            balance = driver.rental
            salary = '%.2f' % (kasa * driver.rate - cash - driver.rental)
        else:
            pass
        return balance, kasa, cash, salary, incomplete


def get_car_efficiency(driver, day=None):
    efficiency = CarEfficiency.objects.filter(start_report=timezone.localize(datetime.combine(day, time.min)),
                                              end_report=timezone.localize(datetime.combine(day, time.max)),
                                              driver=driver)
    if not efficiency:
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

