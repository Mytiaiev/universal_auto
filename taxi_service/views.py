from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.core.paginator import Paginator

from taxi_service.forms import SubscriberForm, MainOrderForm
from taxi_service.handlers import PostRequestHandler, GetRequestHandler
from taxi_service.utils import *
from app.models import ParkSettings


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parkSettings"] = self.get_park_settings()
        context["google_api"] = self.get_google_api_key()
        context["subscribe_form"] = SubscriberForm()
        context["order_form"] = MainOrderForm()
        return context

    def get_park_settings(self):
        park_settings = {}
        specific_keys = [
            "FREE_CAR_SENDING_DISTANCE", "TARIFF_CAR_DISPATCH",
            "TARIFF_CAR_OUTSIDE_DISPATCH", "TARIFF_IN_THE_CITY",
            "TARIFF_OUTSIDE_THE_CITY", "CENTRE_CITY_LAT", "CENTRE_CITY_LNG",
            "CENTRE_CITY_RADIUS", "SEND_TIME_ORDER_MIN", "SEARCH_TIME",
            "MINIMUM_PRICE_RADIUS", "MAXIMUM_PRICE_RADIUS"
        ]

        park_setting_objects = ParkSettings.objects.filter(
            key__in=specific_keys)

        for park_setting in park_setting_objects:
            park_settings[park_setting.key] = park_setting.value

        return json.dumps(park_settings)

    def get_google_api_key(self):
        return ParkSettings.get_value("GOOGLE_API_KEY")


class PostRequestView(View):
    def post(self, request):
        handler = PostRequestHandler()
        action = request.POST.get('action')

        if action == 'order':
            return handler.handle_order_form(request)
        elif action == 'subscribe':
            return handler.handle_subscribe_form(request)
        elif action == 'send_comment':
            return handler.handle_comment_form(request)
        elif action in ['order_sum', 'user_opt_out']:
            return handler.handle_update_order(request)
        elif action in ['increase_price', 'continue_search']:
            return handler.handler_restarting_order(request)
        else:
            return handler.handle_unknown_action(request)


class GetRequestView(View):
    def get(self, request):
        handler = GetRequestHandler()
        action = request.GET.get('action')

        if action == 'active_vehicles_locations':
            return handler.handle_active_vehicles_locations(request)
        elif action == 'order_confirm':
            return handler.handle_order_confirm(request)
        elif action == 'get_drivers_cash':
            return handler.handle_get_drivers_cash(request)
        elif action == 'effective_vehicle':
            return handler.handle_effective_vehicle(request)
        else:
            return handler.handle_unknown_action(request)


class InvestmentView(View):
    def get(self, request):
        return render(request, 'investment.html', {'subscribe_form': SubscriberForm()})


class DriversView(TemplateView):
    template_name = 'drivers.html'
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        drivers = get_all_drivers()
        paginator = Paginator(drivers, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['subscribe_form'] = SubscriberForm()
        context['page_obj'] = page_obj
        return context


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_distance_rent'] = weekly_rent()
        context['get_all_vehicle'] = get_all_vehicle()
        context['average_effective_vehicle'] = average_effective_vehicle()

        return context


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html', {'subscribe_form': SubscriberForm()})


def agreement(request):
    return render(request, 'agreement.html', {'subscribe_form': SubscriberForm()})
