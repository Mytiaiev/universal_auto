from datetime import timedelta

from django.db.models import F, Sum
from django.utils import timezone

from app.models import Driver, FleetOrder
from selenium_ninja.bolt_sync import BoltRequest

from selenium_ninja.uklon_sync import UklonRequest


def run(*args):
    day = timezone.localtime() - timedelta(minutes=5)
    drivers = Driver.objects.filter(partner=1)
    for driver in drivers:
        BoltRequest(1).get_fleet_orders(day, driver.pk)

