import pendulum

from auto.tasks import download_weekly_report, download_daily_report, send_weekly_report, send_efficiency_report
from selenium_ninja.uber_sync import UberSynchronizer


def run(*args):
    day = pendulum.parse('2023-07-02')
    print(send_efficiency_report.delay())
