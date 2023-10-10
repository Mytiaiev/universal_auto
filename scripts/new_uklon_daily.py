from datetime import timedelta

from django.db.models import F, Sum
from django.utils import timezone

from app.models import Driver, FleetOrder
from selenium_ninja.bolt_sync import BoltRequest

from selenium_ninja.uklon_sync import UklonRequest


def run(*args):
    day = timezone.localtime() - timedelta(days=4)
    print(FleetOrder.objects.filter(accepted_time__date=day.date(),
                              partner=1).values('driver').annotate(time=Sum('distance')))

