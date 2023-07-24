from datetime import datetime, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg,  DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import CarEfficiency, Driver, SummaryReport, DriverManager, \
    Vehicle


def validate_date(date_str):
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.today() - timedelta(days=1)
        if check_date > today:
            return False
        else:
            return True
    except ValueError:
        return False


def calculate_reports(start, end, driver):
    incomplete = 0
    balance = 0
    salary = 0
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
    return balance, kasa, cash, salary, '%.2f' % incomplete


def get_daily_report(manager_id=None, start=None, end=None):
    yesterday = timezone.localtime().date() - timedelta(days=1)
    if not start and not end:
        if timezone.localtime().weekday():
            start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
        else:
            start = timezone.localtime().date() - timedelta(weeks=1)
        end = yesterday
    total_values = {}
    day_values = {}
    manager = DriverManager.get_by_chat_id(manager_id)
    drivers = Driver.objects.filter(manager=manager)
    if drivers:
        for driver in drivers:
            day_values[driver] = calculate_reports(yesterday, yesterday, driver)[1]
            total_values[driver] = calculate_reports(start, end, driver)[1]
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        return sort_report, day_values


def calculate_efficiency(licence_plate, start, end):
    efficiency_objects = CarEfficiency.objects.filter(report_from__range=(start, end),
                                                      licence_plate=licence_plate)
    total_kasa = efficiency_objects.aggregate(kasa=Sum('total_kasa'))['kasa']
    total_distance = efficiency_objects.aggregate(total_distance=Sum('mileage'))['total_distance']
    efficiency = 0
    if total_distance:
        efficiency = float('{:.2f}'.format(total_kasa/total_distance))
    formatted_distance = float('{:.2f}'.format(total_distance)) if total_distance is not None else 0.00
    return efficiency, formatted_distance


def get_efficiency(manager_id=None, start=None, end=None):
    yesterday = timezone.localtime().date() - timedelta(days=1)
    if not start and not end:
        if timezone.localtime().weekday():
            start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
        else:
            start = timezone.localtime().date() - timedelta(weeks=1)
        end = yesterday
    effective_vehicle = {}
    report = {}
    manager = DriverManager.get_by_chat_id(manager_id)
    vehicles = Vehicle.objects.filter(manager=manager)
    if vehicles:
        for vehicle in vehicles:
            effect = calculate_efficiency(vehicle.licence_plate, start, end)
            if end == yesterday:
                yesterday_efficiency = CarEfficiency.objects.filter(report_from=yesterday,
                                                                    licence_plate=vehicle.licence_plate).first()
                efficiency = float(yesterday_efficiency.efficiency) if yesterday_efficiency else 0
                distance = float(yesterday_efficiency.mileage) if yesterday_efficiency else 0
                effective_vehicle[vehicle.licence_plate] = {'Середня ефективність(грн/км)': effect[0],
                                                            'Ефективність(грн/км)': efficiency,
                                                            'КМ всього': effect[1],
                                                            'КМ учора': distance}
            else:
                effective_vehicle[vehicle.licence_plate] = {'Середня ефективність(грн/км)': effect[0],
                                                            'КМ всього': effect[1]}
        sorted_effective_driver = dict(sorted(effective_vehicle.items(),
                                       key=lambda x: x[1]['Середня ефективність(грн/км)'],
                                       reverse=True))
        for k, v in sorted_effective_driver.items():
            report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
        return report
