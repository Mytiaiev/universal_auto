import json
import random
import secrets
from datetime import timedelta, date
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from app.models import Driver, UseOfCars, VehicleGPS, Order, Partner, ParkSettings, CredentialPartner, Fleet
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


def update_park_set(partner, key, value, description=None, check_value=True, park=True):
    if park:
        try:
            setting = ParkSettings.objects.get(key=key, partner=partner)
            if setting.value != value and check_value:
                setting.value = value
                setting.save()
        except ObjectDoesNotExist:
            partner = Partner.get_partner(partner)
            ParkSettings.objects.create(key=key, value=value, description=description, partner=partner)
    else:
        try:
            setting = CredentialPartner.objects.get(key=key, partner=partner)
            if CredentialPartner.decrypt_credential(value) != value and check_value:
                setting.value = CredentialPartner.encrypt_credential(value)
                setting.save()
        except ObjectDoesNotExist:
            partner = Partner.get_partner(partner)
            value = CredentialPartner.encrypt_credential(value)
            CredentialPartner.objects.create(key=key, value=value, partner=partner)


def login_in(aggregator=None, partner_id=None, login_name=None, password=None, token=None):
    if aggregator == 'Bolt':
        update_park_set(partner_id, 'BOLT_PASSWORD', password, description='Пароль користувача Bolt', park=False)
        update_park_set(partner_id, 'BOLT_NAME', login_name, description='Ім\'я користувача Bolt', park=False)

    elif aggregator == 'Uklon':
        update_park_set(partner_id, 'UKLON_PASSWORD', password, description='Пароль користувача Uklon', park=False)
        update_park_set(partner_id, 'UKLON_NAME', login_name, description='Ім\'я користувача Uklon', park=False)
        update_park_set(partner_id, 'WITHDRAW_UKLON', '150000', description='Залишок грн на карті водія Uklon')
        hex_length = 16
        random_hex = secrets.token_hex(hex_length)
        update_park_set(
            partner_id, 'CLIENT_ID', random_hex,
            description='Ідентифікатор клієнта Uklon', check_value=False, park=False)
    elif aggregator == 'Uber':
        update_park_set(partner_id, 'UBER_PASSWORD', password, description='Пароль користувача Uber', park=False)
        update_park_set(partner_id, 'UBER_NAME', login_name, description='Ім\'я користувача Uber', park=False)
    elif aggregator == 'Gps':
        update_park_set(partner_id, 'UAGPS_TOKEN', token, description='Токен для GPS сервісу', park=False)
    fleet = Fleet.objects.get(name=aggregator)
    fleet.partner.add(partner_id)
    return True


def partner_logout(aggregator, partner_pk):
    settings = ParkSettings.objects.filter(partner=partner_pk)
    credentials = CredentialPartner.objects.filter(partner=partner_pk)
    if aggregator == 'Uklon':
        settings.filter(key='WITHDRAW_UKLON').delete()

    credential_dict = {
        'Uber': ('UBER_NAME', 'UBER_PASSWORD'),
        'Bolt': ('BOLT_NAME', 'BOLT_PASSWORD'),
        'Uklon': ('UKLON_NAME', 'UKLON_PASSWORD', 'CLIENT_ID'),
        'Gps': ('UAGPS_TOKEN',)
    }

    credential_action = credential_dict.get(aggregator)
    if credential_action:
        credentials.filter(key__in=credential_action).delete()
    fleet = Fleet.objects.get(name=aggregator)
    fleet.partner.remove(partner_pk)
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


def check_aggregators(user_pk):
    partner = Partner.objects.get(user_id=user_pk)
    aggregators = Fleet.objects.filter(partner=partner).values_list('name', flat=True)

    # aggregator_results = {
    #     'Bolt': CredentialPartner.objects.filter(partner=partner, key='BOLT_NAME').exists(),
    #     'Uklon': CredentialPartner.objects.filter(partner=partner, key='UKLON_NAME').exists(),
    #     'Uber': CredentialPartner.objects.filter(partner=partner, key='UBER_NAME').exists(),
    #     'Gps': CredentialPartner.objects.filter(partner=partner, key='UAGPS_TOKEN').exists(),
    # }
    fleets = Fleet.objects.all().values_list('name', flat=True)
    return list(aggregators), list(fleets)
