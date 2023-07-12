from datetime import datetime, time, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg, FloatField, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import Fleets_drivers_vehicles_rate, CarEfficiency, Payments, Driver, SummaryReport, DriverManager, \
    Vehicle
from auto_bot.handlers.driver_manager.static_text import no_drivers_text
from auto_bot.main import bot
from selenium_ninja.uagps_sync import UaGpsSynchronizer


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
        start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
        end = yesterday
    total_values = {}
    day_values = {}
    manager = DriverManager.get_by_chat_id(manager_id)
    drivers = Driver.objects.filter(manager=manager)
    if drivers:
        for driver in Driver.objects.filter(manager=manager):
            day_values[driver] = calculate_reports(yesterday, yesterday, driver)[1]
            total_values[driver] = calculate_reports(start, end, driver)[1]
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        return sort_report, day_values


def get_car_efficiency(licence_plate, day):
    efficiency = CarEfficiency.objects.filter(report_from=day,
                                              licence_plate=licence_plate)
    if not efficiency:
        total_km, vehicle = UaGpsSynchronizer().total_per_day(licence_plate, day)
        if total_km:
            drivers = Driver.objects.filter(vehicle=vehicle)
            total_kasa = 0
            for driver in drivers:
                report = SummaryReport.objects.filter(report_from=day,
                                                      full_name=driver).first()
                total_kasa += report.total_amount_without_fee
            result = Decimal(total_kasa)/Decimal(total_km)
        else:
            result = 0
        CarEfficiency.objects.create(report_from=day,
                                     licence_plate=licence_plate,
                                     mileage=total_km or 0,
                                     efficiency=result)


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


def send_efficiency(manager_id=None, start=None, end=None):
    effective_driver = {}
    effective_report = {}
    for vehicle in Vehicle.objects.all():
        effect = calculate_efficiency(vehicle.licence_plate, start, end)
        effective_driver[vehicle.licence_plate] = {'Середня ефективність(грн/км)': effect[0],
                                                   'Ефективність(грн/км)': effect[1],
                                                   'КМ за тиждень': effect[2],
                                                   'КМ учора': effect[3]}

    sorted_effective_driver = dict(sorted(effective_driver.items(),
                                   key=lambda x: x[1]['Середня ефективність(грн/км)'],
                                   reverse=True))

    for k, v in sorted_effective_driver.items():
        effective_report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
    effect_message = [f'{k}:\n' + ''.join(v) for k, v in effective_report.items()]
    return effect_message
