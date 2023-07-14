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


def get_dates(period=None):

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

    week_start, week_end = get_dates('week')

    start_date_formatted = week_start.strftime('%d.%m.%Y')
    end_date_formatted = week_end.strftime('%d.%m.%Y')

    total_distance = RentInformation.objects.filter(
        created_at__date__range=(week_start, week_end)).aggregate(total_distance=Sum('rent_distance'))['total_distance'] or 0

    return total_distance, start_date_formatted, end_date_formatted


def collect_total_earnings(period):
    total = {}
    total_amount = 0
    start_period, end_period = get_dates(period)
    reports = SummaryReport.objects.filter(report_from__range=(start_period, end_period))
    for driver in Driver.objects.all():
        total[driver.full_name()] = reports.filter(full_name=driver).aggregate(
            clean_kasa=Sum('total_amount_without_fee'))['clean_kasa']
        if total.get(driver.full_name()):
            total_amount += total[driver.full_name()]
    return total, total_amount, start_period, end_period


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


def effective_vehicle(period, vehicle):
    start_date, end_date = get_dates(period=period)
    car_effective = []

    effective_objects = CarEfficiency.objects.filter(
        licence_plate=vehicle, report_from__range=(start_date, end_date)).order_by('report_from')

    for effective in effective_objects:
        date_effective = effective.report_from
        name = effective.driver
        total_amount = effective.total_kasa
        car = effective.licence_plate
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
