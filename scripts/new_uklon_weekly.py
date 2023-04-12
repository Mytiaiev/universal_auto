from app.models import NewUklon


def run():
    b = NewUklon(driver=True, sleep=5, headless=True)
    b.login()
    b.download_payments_order()
    b.save_report()