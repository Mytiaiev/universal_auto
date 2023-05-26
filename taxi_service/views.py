import os

from django.shortcuts import render
from django.views.generic import View, TemplateView

from taxi_service.forms import SubscriberForm, MainOrderForm
from taxi_service.handlers import PostRequestHandler, GetRequestHandler

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
        park_setting_objects = ParkSettings.objects.all()
        for park_setting in park_setting_objects:
            park_settings[park_setting.key] = park_setting.value
        return park_settings

    def get_google_api_key(self):
        return ParkSettings.get_value("GOOGLE_API_KEY", os.environ["GOOGLE_API_KEY"])


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
        else:
            return handler.handle_unknown_action(request)



def about(request):
    return render(request, 'about.html', {'subscribe_form': SubscriberForm()})


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html', {'subscribe_form': SubscriberForm()})


def agreement(request):
    return render(request, 'agreement.html', {'subscribe_form': SubscriberForm()})
