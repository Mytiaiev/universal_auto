import pendulum

from app.models import Bolt


def run(*args):
    if args:
        day = f"{args[0]}"
    else:
        day = pendulum.now().start_of('day').subtract(days=1)
    b = Bolt(driver=True, day=day, sleep=5, headless=True)
    b.login()
    b.download_payments_order()
    b.save_report()