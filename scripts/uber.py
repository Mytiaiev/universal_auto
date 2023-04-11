from app.models import Uber


def run():
    ub = Uber(driver=True, sleep=5, headless=True)
    ub.login_v3()
    ub.download_payments_order()
    ub = ub.save_report()
    ub.quit()


 