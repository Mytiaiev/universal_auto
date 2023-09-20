import os

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
from taxi_service.utils import average_effective_vehicle, \
    car_piggy_bank, get_driver_info, manager_car_piggy_bank, partner_car_piggy_bank
from app.models import ParkSettings, Driver, Vehicle, Partner, Manager, Investor
from auto_bot.main import bot


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

        method = {
            'order': handler.handler_order_form,
            'subscribe': handler.handler_subscribe_form,
            'send_comment': handler.handler_comment_form,
            'order_sum': handler.handler_update_order,
            'user_opt_out': handler.handler_update_order,
            'increase_price': handler.handler_restarting_order,
            'continue_search': handler.handler_restarting_order,
            'uber': handler.handler_success_login,
            'uber_logout': handler.handler_handler_logout,
            'uklon': handler.handler_success_login,
            'uklon_logout': handler.handler_handler_logout,
            'bolt': handler.handler_success_login,
            'bolt_logout': handler.handler_handler_logout,
            'gps': handler.handler_success_login,
            'gps_logout': handler.handler_handler_logout,
            'login_invest': handler.handler_success_login_investor,
            'logout_invest': handler.handler_logout_investor,
            'change_password': handler.handler_change_password,
            'send_reset_code': handler.handler_change_password,
            'update_password': handler.handler_change_password,
            'upd_database': handler.handler_update_database,
        }

        if action in method:
            return method[action](request)
        else:
            return handler.handler_unknown_action(request)


class GetRequestView(View):
    def get(self, request):
        handler = GetRequestHandler()
        action = request.GET.get('action')

        method = {
            'active_vehicles_locations': handler.handle_active_vehicles_locations,
            'order_confirm': handler.handle_order_confirm,
            'get_cash_investor': handler.handle_get_investor_cash,
            'get_cash_manager': handler.handle_get_manager_cash,
            'get_cash_partner': handler.handle_get_partner_cash,
            'get_drivers_manager': handler.handle_get_drivers_manager,
            'get_drivers_partner': handler.handle_get_drivers_partner,
            'investor': handler.handle_effective_vehicle,
            'manager': handler.handle_effective_vehicle,
            'partner': handler.handle_effective_vehicle,
            'is_logged_in': handler.handle_is_logged_in,
            'get_role': handler.handle_get_role
        }

        if action in method:
            return method[action](request)
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


class DashboardInvestorView(TemplateView):
    template_name = 'dashboard/dashboard-investor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_id = self.request.user.id
        investor = Investor.objects.get(user_id=user_id)
        investor_cars = Vehicle.objects.filter(investor_car=investor)

        context['get_all_vehicle'] = investor_cars
        context['car_piggy_bank'] = car_piggy_bank(self.request)

        return context


class DashboardPartnerView(TemplateView):
    template_name = 'dashboard/dashboard-partner.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['get_all_vehicle'] = Vehicle.objects.exclude(licence_plate='Unknown car')
        context['average_effective_vehicle'] = average_effective_vehicle()
        context['car_piggy_bank'] = partner_car_piggy_bank(self.request)

        return context


class DashboardManagerView(TemplateView):
    template_name = 'dashboard/dashboard-manager.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['average_effective_vehicle'] = average_effective_vehicle()
        context['car_piggy_bank'] = manager_car_piggy_bank(self.request)

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


class SendToTelegramView(View):
    def get(self, request, *args, **kwargs):

        chat_id = os.environ.get('TELEGRAM_BOT_CHAT_ID')

        telegram_link = f"https://t.me/{bot.username}?start={chat_id}"

        return HttpResponseRedirect(telegram_link)


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html', {'subscribe_form': SubscriberForm()})


def agreement(request):
    return render(request, 'agreement.html', {'subscribe_form': SubscriberForm()})
