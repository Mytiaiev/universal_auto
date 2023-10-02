from datetime import datetime, timedelta

from _decimal import Decimal
from django.db.models import Sum, Avg, DecimalField, ExpressionWrapper, F
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import CarEfficiency, Driver, SummaryReport, Manager, \
    Vehicle, RentInformation, ParkSettings, DriverEfficiency, Partner, Role, DriverSchemaRate, SalaryCalculation


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


def validate_sum(sum_str):
    try:
        float(sum_str)
        return True
    except (ValueError, TypeError):
        return False


def get_drivers_vehicles_list(chat_id, cls):
    objects = []
    rent = 0
    user = Manager.get_by_chat_id(chat_id)
    if not user:
        user = Partner.get_by_chat_id(chat_id)
    if user:
        if user.role == Role.DRIVER_MANAGER:
            objects = cls.objects.filter(manager=user.pk)
            rent = int(ParkSettings.get_value('RENT_PRICE', 15, partner=user.partner.pk))
        elif user.role == Role.OWNER:
            objects = cls.objects.filter(partner=user.pk)
            rent = int(ParkSettings.get_value('RENT_PRICE', 15, partner=user.pk))
    return objects, rent, user


def calculate_rent(start, end, driver):
    end_time = datetime.combine(end, datetime.max.time())
    rent_report = RentInformation.objects.filter(
        rent_distance__gt=int(ParkSettings.get_value("FREE_RENT", 15, partner=driver.partner.pk)),
        report_from__range=(start, end_time),
        driver=driver)
    if rent_report:
        overall_rent = ExpressionWrapper(F('rent_distance')
                                         - int(ParkSettings.get_value("FREE_RENT", 15, partner=driver.partner.pk)),
                                         output_field=DecimalField())
        total_rent = rent_report.aggregate(distance=Sum(overall_rent))['distance']
    else:
        total_rent = 0
    return total_rent


def calculate_daily_reports(start, end, driver):
    driver_report = SummaryReport.objects.filter(report_from__range=(start, end),
                                                 full_name=driver)
    if driver_report:
        kasa = driver_report.aggregate(
            kasa=Coalesce(Sum('total_amount_without_fee'), 0, output_field=DecimalField()))['kasa']
        rent = calculate_rent(start, end, driver)
        return kasa, rent


def calculate_by_rate(driver, kasa):
    rate_tiers = DriverSchemaRate.get_rate_tier(period=driver.salary_calculation)
    driver_spending = 0
    tier = 0
    rates = rate_tiers[2:] if kasa >= driver.plan else rate_tiers
    for tier_kasa, rate in rates:
        tier_kasa -= tier
        if kasa > tier_kasa:
            driver_spending += tier_kasa * rate
            kasa -= tier_kasa
            tier += tier_kasa
        else:
            driver_spending += kasa * rate
            break
    return driver_spending


def calculate_weekly_reports(start, end, driver):
    incomplete = 0
    driver_report = SummaryReport.objects.filter(report_from__range=(start, end),
                                                 full_name=driver)
    if driver_report:
        cash = driver_report.aggregate(
            cash=Coalesce(Sum('total_amount_cash'), 0, output_field=DecimalField()))['cash']
        kasa = driver_report.aggregate(
            kasa=Coalesce(Sum('total_amount_without_fee'), 0, output_field=DecimalField()))['kasa']
        rent = calculate_rent(start, end, driver)
        rent_value = rent * int(ParkSettings.get_value('RENT_PRICE', 15, partner=driver.partner.pk))
        if kasa:
            if driver.schema.title == "DYNAMIC":
                driver_spending = calculate_by_rate(driver, kasa)
                balance = rent_value + kasa - driver_spending
                salary = '%.2f' % (driver_spending - cash - rent_value)
            elif driver.schema.title in ("HALF", "CUSTOM"):
                if kasa < driver.plan:
                    balance = driver.rental + rent_value
                    incomplete = (driver.plan - kasa) * Decimal(1 - driver.rate)
                    salary = '%.2f' % (kasa * driver.rate - cash - incomplete - rent_value)
                else:
                    balance = kasa * driver.rate + rent_value
                    salary = '%.2f' % (kasa * driver.rate - cash - rent_value)
            else:
                rent = 0
                efficiency_obj = DriverEfficiency.objects.filter(report_from__range=(start, end),
                                                                 driver=driver)
                overall_distance = efficiency_obj.aggregate(
                    distance=Coalesce(Sum('mileage'), 0, output_field=DecimalField()))['distance']
                driver_overall = overall_distance - int(ParkSettings.get_value(
                    "TOTAL_KM_PER_WEEK", 2000, partner=driver.partner.pk))
                rent_value = max(driver_overall * int(ParkSettings.get_value(
                    "OVERALL_KM_PRICE", 6, partner=driver.partner.pk)), 0)
                balance = driver.rental + rent_value
                salary = '%.2f' % (kasa * driver.rate - cash - driver.rental - rent_value)
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
    drivers = get_drivers_vehicles_list(manager_id, Driver)[0]
    for driver in drivers:
        daily_report = calculate_daily_reports(yesterday, yesterday, driver)
        if daily_report:
            day_values[driver],  rent_daily[driver] = daily_report
        total_report = calculate_daily_reports(start, end, driver)
        if total_report:
            total_values[driver], total_rent[driver] = total_report
    sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
    return sort_report, day_values, total_rent, rent_daily


def generate_message_weekly(chat_id):
    end = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday() + 1)
    start = end - timedelta(days=6)
    message = ''
    drivers_dict = {}
    balance = 0
    drivers, rent, user = get_drivers_vehicles_list(chat_id, Driver)
    for driver in drivers.filter(salary_calculation=SalaryCalculation.WEEK):
        driver_message = ''
        result = calculate_weekly_reports(start, end, driver)
        if result:
            balance += result[0]
            driver_message += f"{driver} каса: {result[1]}\n"
            if result[5]:
                driver_message += "Оренда авто: {0} * {1} = {2}\n".format(result[5], rent, result[6])
            if driver.schema.title in ("HALF", "DYNAMIC" "CUSTOM"):
                driver_message += 'Зарплата {0} * {1} - Готівка {2}'.format(
                    result[1], driver.rate, result[2])
                if result[4]:
                    driver_message += " - План {:.2f}".format(result[4])
            else:
                driver_message += 'Зарплата {0} * {1} - Готівка {2} - Абонплата {3}'.format(
                    result[1], driver.rate, result[2], driver.rental)
            if result[6]:
                driver_message += f" - Оренда {result[6]}"
            driver_message += f" = {result[3]}\n"
            if driver.chat_id:
                drivers_dict[driver.chat_id] = driver_message
            message += driver_message
        if driver_message:
            message += "*" * 39 + '\n'
    manager_message = f'Ваш баланс:%.2f\n' % balance
    manager_message += message
    if user:
        drivers_dict[user.chat_id] = manager_message
    return drivers_dict


def calculate_efficiency(vehicle, start, end):
    efficiency_objects = CarEfficiency.objects.filter(report_from__range=(start, end),
                                                      vehicle=vehicle)
    if efficiency_objects:
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
    vehicles = get_drivers_vehicles_list(manager_id, Vehicle)[0]
    for vehicle in vehicles:
        effect = calculate_efficiency(vehicle, start, end)
        if effect:
            if end == yesterday:
                yesterday_efficiency = CarEfficiency.objects.filter(report_from=yesterday,
                                                                    vehicle=vehicle).first()
                efficiency = float(yesterday_efficiency.efficiency) if yesterday_efficiency else 0
                distance = float(yesterday_efficiency.mileage) if yesterday_efficiency else 0
                effective_vehicle[vehicle.licence_plate] = {'Середня ефективність(грн/км)': effect[0],
                                                            'Ефективність(грн/км)': efficiency,
                                                            'КМ всього': effect[1],
                                                            'КМ учора': distance}
            else:
                effective_vehicle[vehicle.licence_plate] = {'Середня ефективність(грн/км)': effect[0],
                                                            'КМ всього': effect[1]}
    try:
        sorted_effective_driver = dict(sorted(effective_vehicle.items(),
                                       key=lambda x: x[1]['Середня ефективність(грн/км)'],
                                       reverse=True))
        for k, v in sorted_effective_driver.items():
            report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
        return report
    except:
        pass


def calculate_efficiency_driver(driver, start, end):
    efficiency_objects = DriverEfficiency.objects.filter(report_from__range=(start, end),
                                                         driver=driver)
    if efficiency_objects:
        efficiency = 0
        accept_percent = 0
        avg_price = 0
        aggregations = efficiency_objects.aggregate(
            total_kasa=Sum('total_kasa'),
            total_distance=Sum('mileage'),
            total_orders=Sum('total_orders'),
            total_hours=Sum('road_time')
        )
        if aggregations['total_orders']:
            accept_percent = float('{:.2f}'.format(efficiency_objects.exclude(accept_percent=0).aggregate(
                accept=Avg('accept_percent'))['accept']))
            avg_price = float('{:.2f}'.format(aggregations['total_kasa'] / aggregations['total_orders']))
        if aggregations['total_distance']:
            efficiency = float('{:.2f}'.format(aggregations['total_kasa'] / aggregations['total_distance']))
        return (efficiency, aggregations['total_orders'], accept_percent,
                avg_price, aggregations['total_distance'], aggregations['total_hours'])


def get_driver_efficiency_report(manager_id=None, start=None, end=None):
    yesterday = timezone.localtime().date() - timedelta(days=1)
    if not start and not end:
        if timezone.localtime().weekday():
            start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
        else:
            start = timezone.localtime().date() - timedelta(weeks=1)
        end = yesterday
    effective_driver = {}
    report = {}
    drivers = get_drivers_vehicles_list(manager_id, Driver)[0]
    for driver in drivers:
        effect = calculate_efficiency_driver(driver, start, end)
        if effect:
            if end == yesterday:
                efficiency = 0
                orders = 0
                accept_percent = 0
                average_price = 0
                distance = 0
                road_time = timedelta()
                yesterday_efficiency = DriverEfficiency.objects.filter(report_from=yesterday,
                                                                       driver=driver).first()
                if yesterday_efficiency:
                    efficiency = float(yesterday_efficiency.efficiency)
                    orders = yesterday_efficiency.total_orders
                    accept_percent = yesterday_efficiency.accept_percent
                    average_price = yesterday_efficiency.average_price
                    distance = yesterday_efficiency.mileage
                    road_time = yesterday_efficiency.road_time
                effective_driver[driver] = {'Ефективність(грн/км)': f"{effect[0]} (+{efficiency})",
                                            'Кількість замовлень': f"{effect[1]} (+{orders})",
                                            'Прийнято замовлень %': f"{effect[2]} ({accept_percent})",
                                            'Cередній чек грн': f"{effect[3]} ({average_price})",
                                            'Пробіг, км': f"{effect[4]} ({distance})",
                                            'Час в дорозі': f"{effect[5]}({road_time})"
                                            }
            else:
                effective_driver[driver] = {'Ефективність(грн/км)': f"{effect[0]}",
                                            'Кількість замовлень': f"{effect[1]}",
                                            'Прийнято замовлень %': f"{effect[2]}",
                                            'Cередній чек грн': f"{effect[3]}",
                                            'Пробіг, км': f"{effect[4]}",
                                            'Час в дорозі': f"{effect[5]}"
                                            }
    sorted_effective_driver = dict(sorted(effective_driver.items(),
                                   key=lambda x: float(x[1]['Ефективність(грн/км)'].split()[0]),
                                   reverse=True))
    for k, v in sorted_effective_driver.items():
        report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
    return report

