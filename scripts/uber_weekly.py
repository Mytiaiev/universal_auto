from scripts.webdriver import Uber


def run():
    ub = Uber(driver=True, sleep=5, headless=True)
    ub.login_v3()
    ub.download_payments_order()
    ub.save_report()
    ub.quit()


 