import json
from datetime import date, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.db.models import F

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


def get_week_dates(period=None):

    if period == 'day':
        current_date = timezone.now().date()
        previous_date = current_date - timedelta(days=1)

        start_date = previous_date
        end_date = current_date
        return start_date, end_date

    elif period == 'week':
        current_date = timezone.now().date()
        weekday = current_date.weekday()

        if weekday == 0:
            start_date = current_date - timedelta(days=7)
            end_date = start_date + timedelta(days=6)
        else:
            start_date = current_date - timedelta(days=weekday)
            end_date = start_date + timedelta(days=6)
        return start_date, end_date

    elif period == 'month':
        current_date = timezone.now().date()
        start_date = current_date.replace(day=1)
        next_month = current_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        return start_date, end_date

    elif period == 'quarter':
        current_date = timezone.now().date()
        current_month = current_date.month
        current_quarter = (current_month - 1) // 3 + 1

        if current_quarter == 1:
            start_date = date(current_date.year, 1, 1)
            end_date = date(current_date.year, 3, 31)
            return start_date, end_date
        elif current_quarter == 2:
            start_date = date(current_date.year, 4, 1)
            end_date = date(current_date.year, 6, 30)
            return start_date, end_date
        elif current_quarter == 3:
            start_date = date(current_date.year, 7, 1)
            end_date = date(current_date.year, 9, 30)
            return start_date, end_date
        elif current_quarter == 4:
            start_date = date(current_date.year, 10, 1)
            end_date = date(current_date.year, 12, 31)
            return start_date, end_date
    else:
        current_date = timezone.now().date()
        weekday = current_date.weekday()

        if weekday == 0:
            start_date = current_date - timedelta(days=7)
            end_date = start_date + timedelta(days=6)
        else:
            start_date = current_date - timedelta(days=weekday)
            end_date = start_date + timedelta(days=6)
        return start_date, end_date


def weekly_rent():

    week_start, week_end = get_week_dates('week')

    start_date_formatted = week_start.strftime('%d.%m.%Y')
    end_date_formatted = week_end.strftime('%d.%m.%Y')

    total_distance = RentInformation.objects.filter(
        created_at__date__range=(week_start, week_end)).aggregate(total_distance=Sum('rent_distance'))['total_distance'] or 0

    return total_distance, start_date_formatted, end_date_formatted


def calculate_earnings(fleet_name, model, driver_external_id_field, full_name_fields: [], total_field: str, fee_field: str = None, period: str = None):
    fleet = Fleet.objects.get(name=fleet_name)
    driver_external_ids = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet).values_list('driver_external_id', flat=True)
    earnings_dict = {}

    start_date, end_date = get_week_dates(period=period)

    for driver_external_id in driver_external_ids:
        income_week = model.objects.filter(**{driver_external_id_field: driver_external_id,
                                              'report_from__date': F('report_to__date'),
                                              'report_from__range': (start_date, end_date)})

        for report in income_week:
            full_name = ' '.join([getattr(report, field) for field in full_name_fields])
            if fee_field:
                total_amount_without_comission = float(getattr(report, total_field)) - float(getattr(report, fee_field))
            else:
                total_amount_without_comission = float(getattr(report, total_field))

            earnings_dict[full_name] = earnings_dict.get(full_name, 0) + total_amount_without_comission
    start_date_formatted = start_date.strftime('%d.%m.%Y')
    end_date_formatted = end_date.strftime('%d.%m.%Y')

    return earnings_dict, start_date_formatted, end_date_formatted


def collect_total_earnings(period):
    total_earnings = {}
    total_amount = 0

    uklon_earnings, start_date, end_date = calculate_earnings('Uklon', NewUklonPaymentsOrder, 'signal', ['full_name'], 'total_amount_without_comission', period=period)
    for driver_name, total in uklon_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[0], split_name[1]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total
        total_amount += total

    bolt_earnings, _, _ = calculate_earnings('Bolt', BoltPaymentsOrder, 'mobile_number', ['driver_full_name'], 'total_amount', 'fee', period=period)
    for driver_name, total in bolt_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total
        total_amount += total

    uber_earnings, _, _ = calculate_earnings('Uber', UberPaymentsOrder, 'driver_uuid', ['first_name', 'last_name'], 'total_amount', period=period)
    for first_name, total in uber_earnings.items():
        split_name = first_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total
        total_amount += total

    ninja_earnings, _, _ = calculate_earnings('Ninja', NinjaPaymentsOrder, 'chat_id', ['full_name'], 'total_amount', period=period)
    for driver_name, total in ninja_earnings.items():
        split_name = driver_name.split(' ')
        reversed_name = ' '.join([split_name[1], split_name[0]])
        total_earnings[reversed_name] = total_earnings.get(reversed_name, 0) + total
        total_amount += total

    return total_earnings, total_amount, start_date, end_date


def get_all_vehicle():
    vehicles = Vehicle.objects.exclude(licence_plate='Unknown car')
    return vehicles


def average_effective_vehicle():
    start_date, end_date = get_week_dates('week')

    start_date_formatted = start_date.strftime('%d.%m.%Y')
    end_date_formatted = end_date.strftime('%d.%m.%Y')

    vehicle = CarEfficiency.objects.filter(start_report__range=(start_date, end_date))
    mileage = vehicle.aggregate(Sum('mileage'))['mileage__sum'] or 0
    total_kasa = vehicle.aggregate(Sum('total_kasa'))['total_kasa__sum'] or 0
    effective = total_kasa / mileage
    effective = float('{:.2f}'.format(effective))

    return effective, start_date_formatted, end_date_formatted


def effective_vehicle(period, vehicle):
    start_date, end_date = get_week_dates(period=period)
    car_effective = []

    effective_objects = CarEfficiency.objects.filter(vehicle=vehicle, start_report__range=(start_date, end_date))
    vehicle_effective = effective_objects.exclude(efficiency=0)

    for effective in vehicle_effective:
        date_effective = effective.start_report
        name = effective.driver
        total_amount = effective.total_kasa
        car = effective.vehicle
        mileage = effective.mileage
        effective = effective.efficiency

        car_data = {
            'date_effective': date_effective,
            'car': car,
            'name': name,
            'total_amount': total_amount,
            'mileage': mileage,
            'effective': effective
        }
        car_effective.append(car_data)
    result = {'data': car_effective}

    return result
