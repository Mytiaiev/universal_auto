from datetime import timedelta

from django.utils import timezone

from app.bolt_sync import BoltRequest
from app.models import Fleet
from app.uklon_sync import UklonRequest
from auto_bot.handlers.driver_manager.utils import get_efficiency


def run(*args):
    fleet = Fleet.objects.filter(partner=4, name='Bolt').first()
    fleet.disable_cash(driver_id="4477749", enable="false")


