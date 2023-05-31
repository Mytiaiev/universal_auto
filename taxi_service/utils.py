import json
from django.core.serializers.json import DjangoJSONEncoder

from app.models import Driver, UseOfCars, VehicleGPS, Order


def active_vehicles_gps():
    vehicles_gps = []
    active_drivers = Driver.objects.filter(driver_status=Driver.ACTIVE)
    for driver in active_drivers:
        vehicle = UseOfCars.objects.filter(user_vehicle=driver).first()
        if vehicle:
            vehicles = VehicleGPS.objects.filter(
                vehicle__licence_plate=vehicle.licence_plate
            ).values('vehicle__licence_plate', 'lat', 'lon')
            for vehicle_gps in vehicles:
                vehicles_gps.append(vehicle_gps)
    json_data = json.dumps(vehicles_gps, cls=DjangoJSONEncoder)
    print('UTILS', json_data)
    return json_data


def order_confirm(id_order):
    order = Order.objects.get(id=id_order)
    driver = order.driver
    vehicle = UseOfCars.objects.filter(user_vehicle=driver).first()
    if vehicle is not None:
        vehicle_gps = VehicleGPS.objects.filter(
            vehicle__licence_plate=vehicle.licence_plate
        ).values('vehicle__licence_plate', 'lat', 'lon')
        json_data = json.dumps(list(vehicle_gps), cls=DjangoJSONEncoder)
        return json_data
    else:
        return "[]"


def update_order_sum_or_status(id_order, arg, action):
    if action == 'order_sum':
        order = Order.objects.get(id=id_order)
        order.sum = arg
        order.save()

    if action == 'user_opt_out':
        order = Order.objects.get(id=id_order)
        order.status_order = Order.CANCELED
        order.sum = arg
        order.save()
