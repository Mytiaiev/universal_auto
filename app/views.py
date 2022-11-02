import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from scripts.driversrating import DriversRatingMixin



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
