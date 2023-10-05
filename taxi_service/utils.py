import json
import random
import secrets
from datetime import timedelta, date, datetime

from django.db.models import Sum, Q, Avg, F, Count, Prefetch
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from app.models import (Driver, UseOfCars, VehicleGPS, Order, RentInformation,
                        SummaryReport, CarEfficiency, Partner, ParkSettings,
                        Manager, Investor, Vehicle, VehicleSpending, DriverEfficiency, )
from selenium_ninja.driver import SeleniumTools
from scripts.redis_conn import get_logger
from collections import defaultdict


def active_vehicles_gps():
    vehicles_gps = []
    active_drivers = Driver.objects.filter(driver_status=Driver.ACTIVE, vehicle__isnull=False)
    for driver in active_drivers:
        vehicle = {'licence_plate': driver.vehicle.licence_plate,
                   'lat': driver.vehicle.lat,
                   'lon': driver.vehicle.lon
                   }
        vehicles_gps.append(vehicle)
    json_data = json.dumps(vehicles_gps, cls=DjangoJSONEncoder)
    return json_data


def order_confirm(id_order):
    order = Order.objects.get(id=id_order)
    car_delivery_price = order.car_delivery_price
    driver = order.driver
    vehicle = UseOfCars.objects.filter(user_vehicle=driver).first()
    if vehicle is not None:
        vehicle_gps = VehicleGPS.objects.filter(
            vehicle__licence_plate=vehicle.licence_plate
        ).values('vehicle__licence_plate', 'lat', 'lon')
        data = {
            'vehicle_gps': list(vehicle_gps),
            'car_delivery_price': car_delivery_price
        }
        json_data = json.dumps(data, cls=DjangoJSONEncoder)
        return json_data
    else:
        return "[]"


def update_order_sum_or_status(id_order, action):
    if action == 'user_opt_out':
        order = Order.objects.get(id=id_order)
        order.status_order = Order.CANCELED
        order.save()


def restart_order(id_order, car_delivery_price, action):
    if action == 'increase_price':
        order = Order.objects.get(id=id_order)
        order.car_delivery_price = car_delivery_price
        order.checked = False
        order.save()

    if action == 'continue_search':
        order = Order.objects.get(id=id_order)
        order.checked = False
        order.save()


# Робота з dashboard.html


def get_dates(period=None):
    current_date = timezone.now().date()

    if period == 'yesterday':
        previous_date = current_date - timedelta(days=1)
        start_date = previous_date
        end_date = current_date

    elif period == 'current_week':
        weekday = current_date.weekday()
        start_date = current_date - timedelta(days=weekday)
        end_date = start_date + timedelta(days=6)

    elif period == 'current_month':
        start_date = current_date.replace(day=1)
        next_month = current_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)

    elif period == 'current_quarter':
        current_month = current_date.month
        current_quarter = (current_month - 1) // 3 + 1

        if current_quarter == 1:
            start_date = date(current_date.year, 1, 1)
            end_date = date(current_date.year, 3, 31)
        elif current_quarter == 2:
            start_date = date(current_date.year, 4, 1)
            end_date = date(current_date.year, 6, 30)
        elif current_quarter == 3:
            start_date = date(current_date.year, 7, 1)
            end_date = date(current_date.year, 9, 30)
        else:
            start_date = date(current_date.year, 10, 1)
            end_date = date(current_date.year, 12, 31)

    elif period == 'last_week':
        start_date = current_date - timedelta(
            days=current_date.weekday() + 7)
        end_date = start_date + timedelta(days=6)

    elif period == 'last_month':
        last_month = current_date.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = last_month

    elif period == 'last_quarter':
        current_month = current_date.month
        current_quarter = (current_month - 4) // 3 + 1

        if current_quarter == 1:
            start_date = date(current_date.year, 1, 1)
            end_date = date(current_date.year, 3, 31)
        elif current_quarter == 2:
            start_date = date(current_date.year, 4, 1)
            end_date = date(current_date.year, 6, 30)
        elif current_quarter == 3:
            start_date = date(current_date.year, 7, 1)
            end_date = date(current_date.year, 9, 30)
        else:
            start_date = date(current_date.year, 10, 1)
            end_date = date(current_date.year, 12, 31)

    else:
        weekday = current_date.weekday()
        if weekday == 0:
            start_date = current_date - timedelta(days=7)
        else:
            start_date = current_date - timedelta(days=weekday)
        end_date = current_date

    return start_date, end_date


def manager_total_earnings(period, user_id, start_date=None, end_date=None):
    total = {}
    total_amount = 0
    total_distance = 0

    if start_date and end_date:
        start_period = datetime.strptime(start_date, '%Y-%m-%d')
        end_period = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_period, end_period = get_dates(period)

    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    manager = Manager.objects.filter(user_id=user_id).first()

    if manager:
        total_distance = RentInformation.objects.filter(
            report_from__range=(start_period, end_period), driver__manager=manager).aggregate(total_distance=Sum('rent_distance'))['total_distance'] or 0

    reports = SummaryReport.objects.filter(report_from__range=(start_period, end_period))

    for driver in Driver.objects.filter(manager=manager):
        total[driver.full_name()] = reports.filter(full_name=driver).aggregate(
            clean_kasa=Sum('total_amount_without_fee'))['clean_kasa'] or 0
        if total.get(driver.full_name()):
            total_amount += total[driver.full_name()]

    vehicles = Vehicle.objects.filter(manager=manager)
    vehicle = CarEfficiency.objects.filter(report_from__range=(start_period, end_period), vehicle__in=vehicles)
    effective = 0
    if vehicle:
        mileage = vehicle.aggregate(Sum('mileage'))['mileage__sum']
        total_kasa = vehicle.aggregate(Sum('total_kasa'))['total_kasa__sum'] or 0
        effective = total_kasa / mileage
        effective = float('{:.2f}'.format(effective))

    return total, total_amount, total_distance, start_date_formatted, end_date_formatted, effective


def partner_total_earnings(period, user_id, start_date=None, end_date=None):
    total = {}
    total_amount = 0

    if start_date and end_date:
        start_period = datetime.strptime(start_date, '%Y-%m-%d')
        end_period = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_period, end_period = get_dates(period)

    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    partner = Partner.objects.filter(user_id=user_id).first()
    reports = SummaryReport.objects.filter(report_from__range=(start_period, end_period))
    total_distance = RentInformation.objects.filter(
        report_from__range=(start_period, end_period), partner=partner).aggregate(
        total_distance=Sum('rent_distance'))['total_distance'] or 0
    for driver in Driver.objects.filter(partner=partner):
        total[driver.full_name()] = reports.filter(full_name=driver).aggregate(
            clean_kasa=Sum('total_amount_without_fee'))['clean_kasa'] or 0
        if total.get(driver.full_name()):
            total_amount += total[driver.full_name()]

    vehicle = CarEfficiency.objects.filter(report_from__range=(start_period, end_period), partner=partner)
    effective = 0
    if vehicle:
        mileage = vehicle.aggregate(Sum('mileage'))['mileage__sum']
        total_kasa = vehicle.aggregate(Sum('total_kasa'))['total_kasa__sum'] or 0
        effective = total_kasa / mileage
        effective = float('{:.2f}'.format(effective))

    return total, total_amount, total_distance, start_date_formatted, end_date_formatted, effective


def investor_cash_car(period, investor_pk, start_date=None, end_date=None):
    total_amount = 0
    total_km = 0

    investor = Investor.objects.get(user_id=investor_pk)
    investor_cars = Vehicle.objects.filter(investor_car=investor)

    if start_date and end_date:
        start_period = datetime.strptime(start_date, '%Y-%m-%d')
        end_period = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_period, end_period = get_dates(period)

    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    results = CarEfficiency.objects.filter(
        vehicle__in=investor_cars,
        report_from__range=(start_period, end_period)
    ).values('vehicle__licence_plate').annotate(
        total_earnings=Sum(F('total_kasa') * F('vehicle__investor_percentage')),
        total_mileage=Sum('mileage'),
        total_spending=Sum('total_spending')
    )

    vehicles = {result['vehicle__licence_plate']: result['total_earnings'] for result in results}
    total_amount = sum(result['total_earnings'] for result in results)
    total_km = sum(result['total_mileage'] for result in results)
    overall_spent = sum(result['total_spending'] for result in results)

    return vehicles, total_amount, total_km, overall_spent, start_date_formatted, end_date_formatted


def get_car_data(cars, investor=None):
    cars_data = []

    for car in cars:
        purchase_price = car.purchase_price
        car_efficiencies = CarEfficiency.objects.filter(vehicle=car)
        clean_kasa = round(sum(efficiency.clean_kasa for efficiency in car_efficiencies), 2)
        total_kasa = round(sum(efficiency.total_kasa for efficiency in car_efficiencies), 2)
        total_spent = sum(efficiency.total_spending for efficiency in car_efficiencies)
        percentage = car.investor_percentage if investor and hasattr(car, 'investor_percentage') else None
        if percentage is not None:
            clean_kasa = total_kasa * percentage
            progress_percentage = round((clean_kasa / purchase_price) * 100) if purchase_price > 0 else 0
        else:
            progress_percentage = round(((clean_kasa - total_spent) / purchase_price) * 100) \
                if purchase_price > 0 else 0

        cars_data.append({
            'licence_plate': car.licence_plate,
            'purchase_price': purchase_price,
            'total_spent': total_spent,
            'total_kasa': round(clean_kasa, 2),
            'progress_percentage': progress_percentage
        })

    return cars_data


def car_piggy_bank(request):
    investor = Investor.objects.get(user_id=request.user.id)
    investor_cars = Vehicle.objects.filter(investor_car=investor)
    cars_data = get_car_data(investor_cars, investor=investor)
    return cars_data


def manager_car_piggy_bank(request):
    manager = Manager.objects.get(user_id=request.user.id)
    manager_cars = Vehicle.objects.filter(manager=manager)
    cars_data = get_car_data(manager_cars)
    return cars_data


def partner_car_piggy_bank(request):
    partner = Partner.objects.get(user_id=request.user.id)
    partner_cars = Vehicle.objects.filter(partner=partner).exclude(licence_plate='Unknown car')
    cars_data = get_car_data(partner_cars)
    return cars_data


def average_effective_vehicle():
    start_date, end_date = get_dates('week')

    start_date_formatted = start_date.strftime('%d.%m.%Y')
    end_date_formatted = end_date.strftime('%d.%m.%Y')

    vehicle = CarEfficiency.objects.filter(report_from__range=(start_date, end_date))
    effective = 0
    if vehicle:
        mileage = vehicle.aggregate(Sum('mileage'))['mileage__sum'] or 0
        total_kasa = vehicle.aggregate(Sum('total_kasa'))['total_kasa__sum'] or 0
        effective = total_kasa / mileage if mileage != 0 else 0
        effective = float('{:.2f}'.format(effective))

    return effective, start_date_formatted, end_date_formatted


def effective_vehicle(period, user_id, action, start_date=None, end_date=None):
    if start_date and end_date:
        start_period = datetime.strptime(start_date, '%Y-%m-%d')
        end_period = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_period, end_period = get_dates(period)

    vehicles = []

    if action == 'investor':
        vehicles = Vehicle.objects.filter(investor_car__user_id=user_id)
    elif action == 'manager':
        vehicles = Vehicle.objects.filter(manager__user_id=user_id)
    elif action == 'partner':
        vehicles = Vehicle.objects.filter(partner__user_id=user_id)

    car_efficiency_aggregate = CarEfficiency.objects.filter(vehicle__in=vehicles, report_from__range=(start_period, end_period)
                                                            ).values('vehicle__licence_plate', 'report_from').annotate(
        total_mileage=Sum('mileage'), total_efficiency=Sum(F('mileage') * F('efficiency')))

    car_efficiency_data = {
        (car['vehicle__licence_plate'], car['report_from']): {
            'total_mileage': car['total_mileage'],
            'total_efficiency': car['total_efficiency'],
        }
        for car in car_efficiency_aggregate
    }

    result = defaultdict(list)

    for effective in car_efficiency_data:
        licence_plate = effective[0]
        total_mileage = car_efficiency_data[effective]['total_mileage']
        efficiency = car_efficiency_data[effective]['total_efficiency'] / total_mileage if total_mileage != 0 else 0

        car_data = {
            'date_effective': effective[1],
            'car': licence_plate,
            'mileage': car_efficiency_data[effective]['total_mileage'],
            'efficiency': round(efficiency, 2),
        }
        result[licence_plate].append(car_data)

    for key in result:
        result[key] = sorted(result[key], key=lambda x: x['date_effective'])

    return result


def update_park_set(partner, key, value, description=None, check_value=True):
    try:
        setting = ParkSettings.objects.get(key=key, partner=partner)
        if setting.value != value and check_value:
            setting.value = value
            setting.save()
    except ObjectDoesNotExist:
        partner = Partner.objects.get(pk=partner)
        ParkSettings.objects.create(key=key, value=value, description=description, partner=partner)


def get_driver_info(request, period, user_id, action, start_date=None, end_date=None):

    if start_date and end_date:
        start_period = datetime.strptime(start_date, '%Y-%m-%d')
        end_period = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        start_period, end_period = get_dates(period)

    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    driver_info_list = []
    drivers = []

    if action == 'get_drivers_manager':
        manager = Manager.objects.filter(user_id=user_id).first()
        drivers = Driver.objects.filter(manager=manager)
    elif action == 'get_drivers_partner':
        partner = Partner.objects.filter(user=user_id).first()
        drivers = Driver.objects.filter(partner=partner)

    for driver in drivers:
        driver_efficiency = DriverEfficiency.objects.filter(
            driver=driver,
            report_from__gte=start_period,
            report_from__lte=end_period
        ).aggregate(
            total_kasa=Sum('total_kasa'),
            total_orders=Sum('total_orders'),
            accept_percent=Avg('accept_percent'),
            mileage=Sum('mileage'),
            road_time=Sum('road_time')
        )

        driver_name = driver.__str__()

        total_orders = driver_efficiency['total_orders'] or 0
        total_kasa = driver_efficiency['total_kasa'] or 0

        average_price = round((total_kasa / total_orders), 2) if total_orders > 0 else 0.0
        efficiency = round((total_kasa / (driver_efficiency['mileage'] or 1)), 2) if total_orders > 0 else 0.0
        accept_percent = round(driver_efficiency['accept_percent'], 2) if driver_efficiency['accept_percent'] is not None else 0.0
        mileage = round(driver_efficiency['mileage'], 2) if driver_efficiency['mileage'] is not None else 0.0
        road_time = str(driver_efficiency['road_time']) if driver_efficiency['road_time'] is not None else '00:00:00'

        driver_info = {
            'driver': driver_name,
            'total_kasa': driver_efficiency['total_kasa'] or 0,
            'total_orders': driver_efficiency['total_orders'] or 0,
            'accept_percent': accept_percent,
            'average_price': average_price,
            'mileage': mileage,
            'efficiency': efficiency,
            'road_time': road_time
        }
        driver_info_list.append(driver_info)

        driver_info_list.sort(key=lambda x: x['total_kasa'], reverse=True)

    return driver_info_list, start_date_formatted, end_date_formatted


def login_in(action=None, user_id=None, success_login=None, login_name=None, password=None, url=None, token=None):
    if action == 'bolt':
        if success_login:
            bolt_url_id = url.split('/')[-2]
            update_park_set(user_id, 'BOLT_PASSWORD', password, description='Пароль користувача Bolt')
            update_park_set(user_id, 'BOLT_NAME', login_name, description='Ім\'я користувача Bolt')
            update_park_set(user_id, 'BOLT_URL_ID_PARK', bolt_url_id, description='BOLT_URL_ID_Парка')
    elif action == 'uklon':
        if success_login:
            update_park_set(user_id, 'UKLON_PASSWORD', password, description='Пароль користувача Uklon')
            update_park_set(user_id, 'UKLON_NAME', login_name, description='Ім\'я користувача Uklon')
            update_park_set(user_id, 'WITHDRAW_UKLON', '150000', description='Залишок грн на карті водія Uklon')
            hex_length = 16
            random_hex = secrets.token_hex(hex_length)
            update_park_set(
                user_id, 'CLIENT_ID', random_hex,
                description='Ідентифікатор клієнта Uklon', check_value=False)
    elif action == 'uber':
        if success_login:
            update_park_set(user_id, 'UBER_PASSWORD', password, description='Пароль користувача Uber')
            update_park_set(user_id, 'UBER_NAME', login_name, description='Ім\'я користувача Uber')
    elif action == 'gps':
        if success_login:
            update_park_set(user_id, 'UAGPS_TOKEN', token, description='Токен для GPS сервісу')
            update_park_set(user_id, 'FREE_RENT', 15, description='Безкоштовна оренда (км)')
            update_park_set(user_id, 'RENT_PRICE', 15, description='Ціна за оренду (грн)')
            success_login = True
    return success_login


def partner_logout(action, user_pk):
    settings = ParkSettings.objects.filter(partner=Partner.get_partner(user_pk))
    action_dict = {
        'uber_logout': ('UBER_NAME', 'UBER_PASSWORD'),
        'bolt_logout': ('BOLT_NAME', 'BOLT_PASSWORD', 'BOLT_URL_ID_PARK'),
        'uklon_logout': ('UKLON_NAME', 'UKLON_PASSWORD', 'CLIENT_ID', 'WITHDRAW_UKLON'),
        'gps_logout': ('UAGPS_TOKEN', 'FREE_RENT', 'RENT_PRICE')
    }
    choose_action = action_dict.get(action)
    if choose_action:
        settings.filter(key__in=choose_action).delete()
    return True


def login_in_investor(request, login_name, password):
    user = authenticate(username=login_name, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            user_name = user.username
            role = user.groups.first().name

            return {'success': True, 'user_name': user_name, 'role': role}
        else:
            return {'success': False, 'message': 'User is not active'}
    else:
        return {'success': False, 'message': 'User is not found'}


def change_password_investor(request, password, new_password, user_email):
    try:
        user = User.objects.filter(email=user_email).first()
        if user is not None:
            user = authenticate(username=user.username, password=password)
            if user.is_active:
                user.set_password(new_password)
                user.save()
                logout(request)
                return {'success': True}
            else:
                return {'success': False, 'message': 'User is not active'}
        else:
            return {'success': False, 'message': 'User is not found'}
    except Exception as error:
        return {'success': False, 'message': 'Користувача не знайдено.'}


def send_reset_code(email, user_login):
    try:
        reset_code = str(random.randint(100000, 999999))

        subject = 'Код скидання пароля'
        message = (
            f'Вас вітає Ninja-Taxi!\nВи запросили відновлення пароля.'
            f'\nЯкщо ви цього не робили просто проігноруйте це повідомлення.'
            f'\nЯкщо все таки це ви то ось ваші данні для відновлення.\n'
            f'Ваш код скидання пароля: {reset_code}\n'
            f'Ваш логін: {user_login}\n'
        )
        from_email = 'Ninja-Taxi@gmail.com'
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list)
        return email, reset_code
    except Exception as error:
        get_logger().error(error)


def check_aggregators(user_pk):
    partner = Partner.objects.get(user_id=user_pk)

    aggregator_results = {
        'bolt': ParkSettings.objects.filter(partner=partner, key='BOLT_NAME').exists(),
        'uklon': ParkSettings.objects.filter(partner=partner, key='UKLON_NAME').exists(),
        'uber': ParkSettings.objects.filter(partner=partner, key='UBER_NAME').exists(),
        'gps': ParkSettings.objects.filter(partner=partner, key='UAGPS_TOKEN').exists(),
    }

    return aggregator_results
