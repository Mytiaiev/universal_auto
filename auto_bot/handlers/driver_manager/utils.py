from datetime import datetime, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg, DecimalField, ExpressionWrapper, F
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import CarEfficiency, Driver, SummaryReport, DriverManager, \
    Vehicle, RentInformation, ParkSettings


def validate_date(date_str):
    try:
        check_date = datetime.strptime(date_str, '%d.%m.%Y')
        today = datetime.today() - timedelta(days=1)
        if check_date > today:
            return False
        else:
            return True
    except ValueError:
        return False


def calculate_rent(start, end, driver):
    end_time = datetime.combine(end, datetime.max.time())
    rent_report = RentInformation.objects.filter(
        rent_distance__gt=int(ParkSettings.get_value("FREE_RENT", partner=driver.partner.pk)),
        created_at__range=(start, end_time),
        driver=driver)
    overall_rent = ExpressionWrapper(F('rent_distance')
                                     - int(ParkSettings.get_value("FREE_RENT", partner=driver.partner.pk)),
                                     output_field=DecimalField())
    total_rent = rent_report.aggregate(distance=Sum(overall_rent))['distance']

    return total_rent


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
    rent = calculate_rent(start, end, driver) or 0
    rent_value = rent * int(ParkSettings.get_value('RENT_PRICE', partner=driver.partner.pk))
    if kasa:
        if driver.schema == "HALF":
            if kasa < driver.plan:
                balance = driver.rental + rent_value
                incomplete = (driver.plan - kasa) * Decimal(1 - driver.rate)
                salary = '%.2f' % (kasa * driver.rate - cash - incomplete - rent_value)
            else:
                balance = kasa * driver.rate + rent_value
                salary = '%.2f' % (kasa * driver.rate - cash - rent_value)
        elif driver.schema == "RENT":
            balance = driver.rental + rent_value
            salary = '%.2f' % (kasa * driver.rate - cash - driver.rental - rent_value)
        else:
            pass
    return balance, kasa, cash, salary, incomplete, rent, rent_value


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
    rent_daily = {}
    total_rent = {}
    manager = DriverManager.get_by_chat_id(manager_id)
    drivers = Driver.objects.filter(manager=manager)
    if drivers:
        for driver in drivers:
            daily_report = calculate_reports(yesterday, yesterday, driver)
            total_report = calculate_reports(start, end, driver)
            day_values[driver],  rent_daily[driver] = daily_report[1], daily_report[5]
            total_values[driver], total_rent[driver] = total_report[1], total_report[5]
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        return sort_report, day_values, total_rent, rent_daily


def generate_message_weekly(partner_pk):
    end = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday() + 1)
    start = end - timedelta(days=6)
    drivers_dict = {}
    balance = 0
    rent = int(ParkSettings.get_value('RENT_PRICE', partner=partner_pk))
    for manager in DriverManager.objects.filter(partner=partner_pk):
        message = ''
        drivers = Driver.objects.filter(manager=manager)
        if drivers:
            for driver in drivers:
                driver_message = ''
                result = calculate_reports(start, end, driver)
                balance += result[0]
                driver_message += f"{driver} каса: {result[1]}\n"
                if result[5]:
                    driver_message += "Оренда авто: {0} * {1} = {2}\n".format(result[5], rent, result[6])
                if driver.schema == "HALF":
                    driver_message += 'Зарплата за тиждень {0} * {1} - Готівка {2}'.format(
                        result[1], driver.rate, result[2])
                    if result[4]:
                        driver_message += " - План {:.2f}".format(result[4])
                    if result[6]:
                        driver_message += f" - Оренда {result[6]}"
                elif driver.schema == "RENT":
                    driver_message += 'Зарплата за тиждень {0} * {1} - Готівка {2} - Абонплата {3}'.format(
                        result[1], driver.rate, result[2], driver.rental)
                    if result[6]:
                        driver_message += f" - Оренда {result[6]}"
                else:
                    pass
                driver_message += f" = {result[3]}\n"
                if driver.chat_id:
                    drivers_dict[driver.chat_id] = driver_message
                message += driver_message
                message += "*" * 39 + '\n'
            manager_message = f'Ваш тижневий баланс:%.2f\n' % balance
            manager_message += message
            drivers_dict[manager.chat_id] = manager_message
    return drivers_dict


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
