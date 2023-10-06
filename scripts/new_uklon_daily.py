from datetime import timedelta

from django.utils import timezone

from app.models import Driver
from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.uklon_sync import UklonRequest


def run(*args):
    drivers = Driver.objects.filter(partner=1)
    day = timezone.localtime() - timedelta(days=1)
    for driver in drivers:
        UklonRequest(1).get_fleet_orders(day, driver.pk)
