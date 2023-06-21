from app.models import Driver
from auto.tasks import download_weekly_report, fleets_cash_trips


def run(*args):
    driver = Driver.objects.get(id=29)
    if args:
        week_number = f"2022W{args[0]}5"
    else:
        week_number = None
    fleets_cash_trips.delay(driver.name, driver.second_name, True)



