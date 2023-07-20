import time
from datetime import datetime, timedelta
from auto.tasks import download_daily_report, get_car_efficiency


def run(partner_id):
    start = datetime.now().date() - timedelta(days=15)
    end = datetime.now().date() - timedelta(days=1)
    while start <= end:
        day = datetime.strftime(start, "%Y-%m-%d")
        download_daily_report.delay(partner_id, day)
        get_car_efficiency.delay(partner_id, day)
        start += timedelta(days=1)
