import pendulum

from scripts.webdriver import Uber


def run(*args):
    if args:
        day = f"{args[0]}"
    else:
        day = pendulum.now().start_of('day').subtract(days=1)
    ub = Uber(driver=True, day=day, sleep=5, headless=True)
    ub.login_v3()
    ub.download_payments_order()
    ub.save_report()
    ub.quit()