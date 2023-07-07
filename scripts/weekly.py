import pendulum

from auto.tasks import download_weekly_report, download_daily_report


def run(*args):
    day = pendulum.now().start_of('day').subtract(days=1)
    print(download_daily_report.delay('2023-06-28'))
