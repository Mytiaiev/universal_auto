from auto.tasks import get_driver_reshuffles, check_available_fleets
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    print(check_available_fleets(4))