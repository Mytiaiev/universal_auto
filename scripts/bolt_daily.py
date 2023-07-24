from datetime import timedelta
from django.utils import timezone


def run(*args):
    print(timezone.localtime().date() - timedelta(weeks=1))