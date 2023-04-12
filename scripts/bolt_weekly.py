from app.models import Bolt


def run():
    b = Bolt(driver=True, sleep=5, headless=True)
    b.login()
    b.download_payments_order()
    b.save_report()