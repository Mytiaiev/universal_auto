from datetime import datetime, timedelta

from django.db.models import Sum
from django.utils import timezone

from auto_bot.handlers.driver_manager.utils import get_drivers_vehicles_list, calculate_efficiency, get_efficiency
from selenium_ninja.bolt_sync import BoltRequest
from app.models import FleetOrder, PaymentTypes, Driver, Vehicle


def run(*args):
    start = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday())
    yesterday = timezone.localtime().date() - timedelta(days=1)
    get_efficiency(515224934, start, yesterday)



