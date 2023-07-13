from auto.tasks import download_daily_report,get_car_efficiency


def run(*args):
    download_daily_report.delay("2023-07-09")
    get_car_efficiency.delay("2023-07-09")
