from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.uber_sync import UberRequest
from selenium_ninja.uklon_sync import UklonRequest


def run(*args):
    UberRequest(2).synchronize()