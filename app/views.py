import datetime

from django.shortcuts import render
import folium
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from scripts.driversrating import DriversRatingMixin
from app.models import VehicleGPS, Vehicle


class DriversRatingView(DriversRatingMixin, TemplateView):
    template_name = 'app/drivers_rating.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        try:
            start = datetime.datetime.strptime(self.request.GET.get("start"), "%d-%m-%Y")
        except:
            start = None
        try:
            end = datetime.datetime.strptime(self.request.GET.get("end"), "%d-%m-%Y")
        except:
            end = None
        context['rating'] = self.get_rating(start, end)
        return context


class GpsData(APIView):
    def get(self, request, format=None):
        return Response('OK')

    def post(self, request):
        return Response('OK')


def drivers_total_weekly_rating(request):
    rate = DriversRatingMixin().get_rating()
    date = f"{rate[0]['rating'][0]['start']:%d.%m.%Y} - {rate[0]['rating'][0]['end']:%d.%m.%Y}"
    drivers = {}
    for fleet in DriversRatingMixin().get_rating():
        for period in fleet['rating']:
            if period['rating']:
                for item in period['rating']:
                    drivers.setdefault(item['driver'], 0)
                    drivers[item['driver']] += round(item['amount'], 2)

    drivers = dict(sorted(drivers.items(), key=lambda item: item[1], reverse=True))

    context = {'date': date, 'drivers': drivers}

    return render(request, 'app/drivers_total_weekly_rating.html', context)


def gps_cars(request):
    all_gps_cars = Vehicle.objects.all()
    # Create Map Object
    map_obj = folium.Map(location=[19, -12], zoom_start=2)
    for car in all_gps_cars:
        vehicle_gps = VehicleGPS.objects.all().filter(vehicle_id=car.id).order_by('-created_at')
        lat = vehicle_gps[0].lat/10
        lon = vehicle_gps[0].lon/10
        if vehicle_gps:
            folium.Marker([lat, lon], tooltip="Click for more", popup=car.name).add_to(map_obj)
        else:
            continue
    # Get HTML Representation of Map Object
    map_obj = map_obj._repr_html_()
    context = {
        "map_obj": map_obj
    }
    return render(request, 'map.html', context)

