from datetime import datetime, timedelta

import pendulum
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import Driver, Payments, SummaryReport
from auto.tasks import download_daily_report, send_weekly_report, send_efficiency_report
from selenium_ninja.uber_sync import UberSynchronizer


def run(*args):
    download_daily_report.delay("2023-07-10")