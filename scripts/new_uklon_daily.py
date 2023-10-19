from auto_bot.handlers.driver_manager.utils import get_daily_report
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    result = get_daily_report(515224934)[0]
    for key in result:
        print(key)
        print(result[key])


