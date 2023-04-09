import os
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import render
from taxi_service.forms import SubscriberForm, MainOrderForm, CommentForm
from app.models import *


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


def index(request):
    print(request.POST)
    sub_form = SubscriberForm()
    order_form = MainOrderForm()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST.get('action') == 'order':
            order_form = MainOrderForm(request.POST)
            if order_form.is_valid():
                order_form.save()
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

        elif request.GET.get('action') == 'active_vehicles_locations':
            active_vehicle_locations = active_vehicles_gps()
            return JsonResponse({'data': active_vehicle_locations}, safe=False)

    park_settings = ParkSettings.objects.all()
    tariff = {}
    for park in park_settings:
        tariff[park.key] = park.value
    google_api = os.environ['GOOGLE_API_KEY']
    context = {
        "tariff": tariff,
        "google_api": google_api,
        "subscribe_form": sub_form,
        "order_form": order_form,
    }

    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html')





