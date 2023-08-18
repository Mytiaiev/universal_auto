import jwt
import json

from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.views.generic import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from taxi_service.forms import SubscriberForm, MainOrderForm
from taxi_service.handlers import PostRequestHandler, GetRequestHandler
from taxi_service.utils import weekly_rent, average_effective_vehicle
from app.models import ParkSettings, Driver, Vehicle, Partner, Manager


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
            return handler.handler_order_form(request)
        elif action == 'subscribe':
            return handler.handler_subscribe_form(request)
        elif action == 'send_comment':
            return handler.handler_comment_form(request)
        elif action in ['order_sum', 'user_opt_out']:
            return handler.handler_update_order(request)
        elif action in ['increase_price', 'continue_search']:
            return handler.handler_restarting_order(request)
        elif action in ['uber', 'uklon', 'bolt']:
            return handler.handler_success_login(request)
        elif action in ['uber_logout', 'uklon_logout', 'bolt_logout']:
            return handler.handler_handler_logout(request)
        elif action == 'login_invest':
            return handler.handler_success_login_investor(request)
        elif action == 'logout_invest':
            return handler.handler_logout_investor(request)
        elif action in ['change_password', 'send_reset_code', 'update_password']:
            return handler.handler_change_password(request)
        else:
            return handler.handler_unknown_action(request)


class GetRequestView(View):
    def get(self, request):
        handler = GetRequestHandler()
        action = request.GET.get('action')

        if action == 'active_vehicles_locations':
            return handler.handle_active_vehicles_locations(request)
        elif action == 'order_confirm':
            return handler.handle_order_confirm(request)
        elif action == 'get_cash':
            return handler.handle_get_drivers_cash(request)
        elif action == 'effective_vehicle':
            return handler.handle_effective_vehicle(request)
        elif action == 'is_logged_in':
            return handler.handle_is_logged_in(request)
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
        drivers = Driver.objects.all()
        paginator = Paginator(drivers, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['subscribe_form'] = SubscriberForm()
        context['page_obj'] = page_obj
        return context


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            partner = Partner.objects.filter(user=user).exists()
            manager = Manager.objects.filter(user=user).exists()

            if partner:
                context['user_role'] = 'Partner'
            elif manager:
                context['user_role'] = 'Manager'
            else:
                context['user_role'] = 'User'
        context['total_distance_rent'] = weekly_rent()
        context['get_all_vehicle'] = Vehicle.objects.exclude(licence_plate='Unknown car')
        context['average_effective_vehicle'] = average_effective_vehicle()

        return context


class GoogleAuthView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(GoogleAuthView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        credential_data = request.POST.get('credential')
        data = jwt.decode(credential_data, options={'verify_signature': False})
        email = data["email"].lower()
        redirect_url = reverse('index')

        if email:
            user = User.objects.filter(email=email).first()
            if user:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                redirect_url = reverse('dashboard')
            else:

                return redirect(reverse('index') + "?signed_in=false")

        return HttpResponseRedirect(redirect_url)


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html', {'subscribe_form': SubscriberForm()})


def agreement(request):
    return render(request, 'agreement.html', {'subscribe_form': SubscriberForm()})
