import os
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
from taxi_service.forms import SubscriberForm, MainOrderForm, CommentForm
from django.forms.models import model_to_dict

from app.models import Driver, UseOfCars, VehicleGPS, Order, ParkSettings


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


def index(request):
    sub_form = SubscriberForm()
    order_form = MainOrderForm()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST.get('action') == 'order':
            order_form = MainOrderForm(request.POST)
            if order_form.is_valid():
                save_form = order_form.save(
                    request.POST.get('sum'),
                    request.POST.get('payment_method')
                )
                order_dict = model_to_dict(save_form)
                json_data = json.dumps(order_dict, cls=DjangoJSONEncoder)
                return JsonResponse({'data': json_data}, safe=False)
            else:
                return JsonResponse(order_form.errors, status=400)

        elif request.POST.get('action') == 'subscribe':
            sub_form = SubscriberForm(request.POST)
            if sub_form.is_valid():
                sub_form.save()
            else:
                return JsonResponse(sub_form.errors, status=400)

        elif request.POST.get('action') == 'send_comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment_form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse(
                    {'success': False, 'errors': 'Щось пішло не так!'})

        elif request.POST.get('action') == 'order_sum':
            update_order_sum_or_status(
                request.POST.get('idOrder'),
                request.POST.get('sum'),
                request.POST.get('action')
            )

        elif request.POST.get('action') == 'user_opt_out':
            update_order_sum_or_status(
                request.POST.get('idOrder'),
                request.POST.get('sum'),
                request.POST.get('action')
            )

        elif request.GET.get('action') == 'active_vehicles_locations':
            active_vehicle_locations = active_vehicles_gps()
            return JsonResponse({'data': active_vehicle_locations}, safe=False)

        elif request.GET.get('action') == 'order_confirm':
            driver = order_confirm(request.GET.get('id_order'))
            return JsonResponse({'data': driver}, safe=False)

    park_setting = ParkSettings.objects.all()
    park_settings = {}
    for park in park_setting:
        park_settings[park.key] = park.value
    google_api = ParkSettings.get_value("GOOGLE_API_KEY", os.environ["GOOGLE_API_KEY"])
    context = {
        "parkSettings": park_settings,
        "google_api": google_api,
        "subscribe_form": sub_form,
        "order_form": order_form,
    }

    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html', {'subscribe_form': SubscriberForm()})


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html', {'subscribe_form': SubscriberForm()})


def agreement(request):
    return render(request, 'agreement.html', {'subscribe_form': SubscriberForm()})





