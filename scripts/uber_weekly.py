from auto.drivers import Uber


def run():
    ub = Uber(driver=True, sleep=5, headless=True)
    ub.login()
    ub.download_payments_order()
    ub.save_report()
    ub.quit()


 