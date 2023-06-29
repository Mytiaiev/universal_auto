import json
from datetime import date
from django.core.serializers.json import DjangoJSONEncoder

from app.models import Driver, UseOfCars, VehicleGPS, Order


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