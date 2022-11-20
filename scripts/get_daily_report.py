from app.models import download_and_save_daily_report
import pendulum


def run(*args):
    if args:
        day = f"{args[0]}"
    else:
        day = pendulum.now().start_of('day').subtract(days=1)  # yesterday

    download_and_save_daily_report(driver=True, sleep=5, headless=True, day=day)
