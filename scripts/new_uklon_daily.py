from datetime import timedelta, datetime

from django.utils import timezone

from auto.tasks import get_car_efficiency, download_daily_report
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    day = timezone.localtime() - timedelta(days=2)
    day = day.strftime("%Y-%m-%d")
    download_daily_report.delay(4, day)

