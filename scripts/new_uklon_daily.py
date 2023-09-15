from datetime import timedelta

from django.utils import timezone

from app.models import Driver
from auto.tasks import get_driver_reshuffles, check_available_fleets
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    day = timezone.localtime()-timedelta(days=1)
    for driver in Driver.objects.all():
        BoltRequest(4).get_fleet_orders(day, driver.pk)