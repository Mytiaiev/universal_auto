from datetime import timedelta

import pendulum
from django.utils import timezone

from app.models import Driver
from scripts.google_calendar import GoogleCalendar


def run(*args):
    calendar = GoogleCalendar()
