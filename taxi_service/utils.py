import json
from datetime import date, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from app.models import *


def active_vehicles_gps():
    vehicles_gps = []
    active_drivers = Driver.objects.filter(driver_status=Driver.ACTIVE)
    for driver in active_drivers:
        today = date.today()
        vehicle = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=today).first()
        if vehicle:
            vehicles = VehicleGPS.objects.filter(
                vehicle__licence_plate=vehicle.licence_plate
            ).values('vehicle__licence_plate', 'lat', 'lon').last()
            vehicles_gps.append(vehicles)
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


def get_all_drivers():
    drivers = Driver.objects.all()
    return drivers


def get_week_dates():
    current_date = timezone.now().date()
    weekday = current_date.weekday()
    if weekday == 0:
        start_date = current_date - timedelta(days=7)
        end_date = start_date + timedelta(days=6)
    else:
        start_date = current_date - timedelta(days=(weekday + 1))
        end_date = start_date + timedelta(days=6)
    return start_date, end_date


def weekly_rent():
    start_date, end_date = get_week_dates()

    start_date_formatted = start_date.strftime('%d.%m.%Y')
    end_date_formatted = end_date.strftime('%d.%m.%Y')

    rents = RentInformation.objects.filter(created_at__range=(start_date, end_date))
    total_distance = sum(rent.rent_distance for rent in rents)
    return total_distance, start_date_formatted, end_date_formatted


def weekly_income():

    start_date, end_date = get_week_dates()

    start_date_formatted = start_date.strftime('%d.%m.%Y')
    end_date_formatted = end_date.strftime('%d.%m.%Y')

    income_week_uklon = NewUklonPaymentsOrder.objects.filter(report_from__range=(start_date, end_date))
    income_week_bolt = BoltPaymentsOrder.objects.filter(report_from__range=(start_date, end_date))
    income_week_uber = UberPaymentsOrder.objects.filter(report_from__range=(start_date, end_date))
    income_week_ninja = NinjaPaymentsOrder.objects.filter(report_from__range=(start_date, end_date))

    total_amount_new_uklon = income_week_uklon.aggregate(Sum('total_amount_without_comission'))['total_amount_without_comission__sum'] or 0
    total_amount_bolt = income_week_bolt.aggregate(Sum('total_amount')).get('total_amount__sum', 0) - income_week_bolt.aggregate(Sum('fee')).get('fee__sum', 0)
    total_amount_uber = income_week_uber.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_amount_ninja = income_week_ninja.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    total_amount = total_amount_new_uklon + total_amount_bolt + total_amount_uber + total_amount_ninja

    return total_amount, start_date_formatted, end_date_formatted


def calculate_earnings(fleet_name, model, driver_external_id_field, full_name_fields: [], total_field: str, fee_field: str = None):
    fleet = Fleet.objects.get(name=fleet_name)
    driver_external_ids = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet).values_list('driver_external_id', flat=True)
    earnings_dict = {}

    start_date, end_date = get_week_dates()

    for driver_external_id in driver_external_ids:
        income_week = model.objects.filter(**{driver_external_id_field: driver_external_id,
                                              'report_from__range': (start_date, end_date)})

        for report in income_week:
            full_name = ' '.join([getattr(report, field) for field in full_name_fields])
            if fee_field:
                total_amount_without_comission = float(getattr(report, total_field)) - float(getattr(report, fee_field))
            else:
                total_amount_without_comission = float(getattr(report, total_field))

            earnings_dict[full_name] = earnings_dict.get(full_name, 0) + total_amount_without_comission

    return earnings_dict


def collect_total_earnings():
    total_earnings = {}

    uklon_earnings = calculate_earnings('Uklon', NewUklonPaymentsOrder, 'signal', ['full_name'], 'total_amount_without_comission')
    for driver_name, total_amount in uklon_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[0], split_name[1]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total_amount

    bolt_earnings = calculate_earnings('Bolt', BoltPaymentsOrder, 'driver_full_name', ['driver_full_name'], 'total_amount')
    for driver_name, total_amount in bolt_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total_amount

    uber_earnings = calculate_earnings('Uber', UberPaymentsOrder, 'driver_uuid', ['first_name', 'last_name'], 'total_amount')
    for first_name, total_amount in uber_earnings.items():
        split_name = first_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total_amount

    ninja_earnings = calculate_earnings('Ninja', NinjaPaymentsOrder, 'chat_id', ['full_name'], 'total_amount')
    for driver_name, total_amount in ninja_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total_amount

    return total_earnings


def get_all_vehicle():
    vehicles = Vehicle.objects.all()
    return vehicles