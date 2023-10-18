from datetime import timedelta, datetime, time

from django.utils import timezone

from app.models import Driver
from auto_bot.handlers.order.utils import check_reshuffle
from scripts.google_calendar import GoogleCalendar
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    day = timezone.localtime() - timedelta(days=3)
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = timezone.make_aware(datetime.combine(day, time.max))
    for driver in Driver.objects.filter(partner=1, worked=True):
        vehicles = check_reshuffle(driver, day)
        print(vehicles)

