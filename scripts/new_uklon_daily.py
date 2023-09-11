from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.uagps_sync import UaGpsSynchronizer
from selenium_ninja.uber_sync import UberRequest
from selenium_ninja.uklon_sync import UklonRequest
from auto.tasks import get_driver_reshuffles

def run(*args):
    get_driver_reshuffles.delay()