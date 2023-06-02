from app.models import get_report
from auto.tasks import download_weekly_report_force


def run(*args):
    if args:
        week_number = f"2022W{args[0]}5"
    else:
        week_number = None
    # print(get_report(week=True, week_number=week_number, driver=True, sleep=5, headless=True))
    download_weekly_report_force.delay()




