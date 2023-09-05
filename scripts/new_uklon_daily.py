from django.utils import timezone

from app.models import DriverReshuffle


def run(*args):
    for resh in DriverReshuffle.objects.all():
        print(timezone.localtime(resh.swap_time))