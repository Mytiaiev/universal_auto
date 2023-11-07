from datetime import timedelta

from django.utils import timezone

from app.models import Fleet
from app.uklon_sync import UklonRequest
from auto_bot.handlers.driver_manager.utils import get_efficiency


def run(*args):
    UklonRequest.objects.create(name="Uklon", min_fee=6000)
    fleet = Fleet.objects.get(name='Uklon')
    print(fleet)



