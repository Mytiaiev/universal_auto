import json
import random
import secrets
from datetime import timedelta, date

from django.db.models import Sum, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from app.models import (Driver, UseOfCars, VehicleGPS, Order, RentInformation, SummaryReport, CarEfficiency,
                        Partner, ParkSettings, Manager, Investor, Vehicle, VehicleSpendings, )
from selenium_ninja.driver import SeleniumTools
from scripts.redis_conn import get_logger


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


# Робота з dashboard.html #################


def get_dates(period=None):
    current_date = timezone.now().date()
    if period == 'day':
        previous_date = current_date - timedelta(days=1)

        start_date = previous_date
        end_date = current_date

    elif period == 'week':
        weekday = current_date.weekday()

        if weekday == 0:
            start_date = current_date - timedelta(days=7)
            end_date = start_date + timedelta(days=6)
        else:
            start_date = current_date - timedelta(days=weekday)
            end_date = start_date + timedelta(days=6)

    elif period == 'month':
        current_date = timezone.now().date()
        start_date = current_date.replace(day=1)
        next_month = current_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)

    elif period == 'quarter':
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

    else:
        weekday = current_date.weekday()

        if weekday == 0:
            start_date = current_date - timedelta(days=7)
            end_date = start_date + timedelta(days=6)
        else:
            start_date = current_date - timedelta(days=weekday)
            end_date = start_date + timedelta(days=6)
    return start_date, end_date


def weekly_rent():
    week_start, week_end = get_dates('week')

    start_date_formatted = week_start.strftime('%d.%m.%Y')
    end_date_formatted = week_end.strftime('%d.%m.%Y')

    total_distance = RentInformation.objects.filter(
        created_at__date__range=(week_start, week_end)).aggregate(
        total_distance=Sum('rent_distance'))['total_distance'] or 0

    return total_distance, start_date_formatted, end_date_formatted


def collect_total_earnings(period):
    total = {}
    total_amount = 0

    start_period, end_period = get_dates(period)
    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    reports = SummaryReport.objects.filter(report_from__range=(start_period, end_period))
    for driver in Driver.objects.all():
        total[driver.full_name()] = reports.filter(full_name=driver).aggregate(
                    clean_kasa=Sum('total_amount_without_fee'))['clean_kasa'] or 0
        if total.get(driver.full_name()):
            total_amount += total[driver.full_name()]
    return total, total_amount, start_date_formatted, end_date_formatted


def investor_cash_car(period, investor_pk):
    vehicles = {}
    total_amount = 0
    total_km = 0

    investor = Investor.objects.get(user_id=investor_pk)
    investor_cars = Vehicle.objects.filter(investor_car=investor)
    licence_plates = [car.licence_plate for car in investor_cars]

    start_period, end_period = get_dates(period)
    start_date_formatted = start_period.strftime('%d.%m.%Y')
    end_date_formatted = end_period.strftime('%d.%m.%Y')

    results = CarEfficiency.objects.filter(
        Q(licence_plate__in=licence_plates) &
        Q(report_from__range=(start_period, end_period))
    )

    for result in results:
        licence_plate = result.licence_plate
        total_kasa = result.total_kasa
        vehicle = Vehicle.objects.get(licence_plate=licence_plate)
        earnings = float(total_kasa) * float(vehicle.investor_percentage)

        if licence_plate not in vehicles:
            vehicles[licence_plate] = earnings
        else:
            vehicles[licence_plate] += earnings

        total_amount += earnings
        total_km += result.mileage

    overall_spent = sum(spending.amount for spending in VehicleSpendings.objects.filter(
        vehicle__licence_plate__in=licence_plates,
        created_at__range=(start_period, end_period)
    )
    )

    return vehicles, total_amount, total_km, overall_spent, start_date_formatted, end_date_formatted


def car_piggy_bank(request):
    investor = Investor.objects.get(user_id=request.user.id)
    investor_cars = Vehicle.objects.filter(investor_car=investor)

    cars_data = []

    for car in investor_cars:
        licence_plate = car.licence_plate
        purchase_price = car.purchase_price

        spendings = VehicleSpendings.objects.filter(vehicle=car)
        total_spent = sum(spending.amount for spending in spendings)

        car_efficiencies = CarEfficiency.objects.filter(licence_plate=licence_plate)
        total_kasa = sum(efficiency.total_kasa for efficiency in car_efficiencies)

        progress_percentage = ((total_kasa - total_spent) / purchase_price) * 100
        # progress_percentage = float('{:.2f}'.format(progress_percentage)) # TODO: check this
        progress_percentage = int(progress_percentage)

        cars_data.append({
            'licence_plate': licence_plate,
            'purchase_price': purchase_price,
            'total_spent': total_spent,
            'total_kasa': total_kasa,
            'progress_percentage': progress_percentage
        })

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
        effective = total_kasa / mileage
        effective = float('{:.2f}'.format(effective))
    return effective, start_date_formatted, end_date_formatted


def effective_vehicle(period, vehicle1, vehicle2):
    start_date, end_date = get_dates(period=period)

    effective_objects = CarEfficiency.objects.filter(Q(licence_plate=vehicle1) | Q(licence_plate=vehicle2),
                                                     report_from__range=(start_date, end_date)
                                                     ).order_by('licence_plate', 'report_from')

    result = {'vehicle1': [], 'vehicle2': []}

    for effective in effective_objects:
        car_data = {
            'date_effective': effective.report_from,
            'car': effective.licence_plate,
            'total_amount': effective.total_kasa,
            'mileage': effective.mileage,
            'effective': effective.efficiency
        }
        result_key = 'vehicle1' if effective.licence_plate == vehicle1 else 'vehicle2'
        result[result_key].append(car_data)

    return result


def investor_effective_vehicle(period, investor_pk):
    start_date, end_date = get_dates(period=period)

    investor = Investor.objects.get(user_id=investor_pk)
    investor_cars = Vehicle.objects.filter(investor_car=investor)
    licence_plates = [car.licence_plate for car in investor_cars]

    effective_objects = CarEfficiency.objects.filter(
            licence_plate__in=licence_plates,
            report_from__range=(start_date, end_date)
    ).order_by('licence_plate', 'report_from')

    result = {}

    for effective in effective_objects:
        car_data = {
            'date_effective': effective.report_from,
            'car': effective.licence_plate,
            'mileage': effective.mileage,
        }
        if effective.licence_plate not in result:
            result[effective.licence_plate] = [car_data]
        else:
            result[effective.licence_plate].append(car_data)
    return result


def update_park_set(partner, key, value, description=None, check_value=True):
    try:
        setting = ParkSettings.objects.get(key=key, partner=partner)
        if setting.value != value and check_value:
            setting.value = value
            setting.save()
    except ObjectDoesNotExist:
        ParkSettings.objects.create(key=key, value=value, description=description, partner=partner)


def login_in(action, login_name, password, user_id):
    partner = Partner.objects.get(user_id=user_id)
    selenium_tools = SeleniumTools(partner=partner.pk)
    success_login = False
    if action == 'bolt':
        success_login, url = selenium_tools.bolt_login(
            login=login_name,
            password=password)
        if success_login:
            bolt_url_id = url.split('/')[-2]
            update_park_set(partner, 'BOLT_PASSWORD', password, description='Пароль користувача Bolt')
            update_park_set(partner, 'BOLT_NAME', login_name, description='Ім\'я користувача Bolt')
            update_park_set(partner, 'BOLT_URL_ID_PARK', bolt_url_id, description='BOLT_URL_ID_Парка')
    elif action == 'uklon':
        success_login = selenium_tools.uklon_login(
            login=login_name[4:],
            password=password)
        if success_login:
            update_park_set(partner, 'UKLON_PASSWORD', password, description='Пароль користувача Uklon')
            update_park_set(partner, 'UKLON_NAME', login_name, description='Ім\'я користувача Uklon')
            hex_length = 16
            random_hex = secrets.token_hex(hex_length)
            update_park_set(
                partner, 'CLIENT_ID', random_hex,
                description='Ідентифікатор клієнта Uklon', check_value=False)
    elif action == 'uber':
        success_login = selenium_tools.uber_login(
            login=login_name,
            password=password)
        if success_login:
            update_park_set(partner, 'UBER_PASSWORD', password, description='Пароль користувача Uber')
            update_park_set(partner, 'UBER_NAME', login_name, description='Ім\'я користувача Uber')
    return success_login


def partner_logout(action, user_pk):
    settings = ParkSettings.objects.filter(partner=Partner.get_partner(user_pk))
    if action == 'uber_logout':
        settings.filter(key__in=['UBER_NAME', 'UBER_PASSWORD']).delete()
    elif action == 'bolt_logout':
        settings.filter(key__in=['BOLT_NAME', 'BOLT_PASSWORD', 'BOLT_URL_ID_PARK']).delete()
    elif action == 'uklon_logout':
        settings.filter(key__in=['UKLON_NAME', 'UKLON_PASSWORD', 'CLIENT_ID']).delete()
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
