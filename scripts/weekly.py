from datetime import datetime, timedelta

from auto.tasks import get_car_efficiency, upload_db


def run(*args):
    start = datetime.now().date() - timedelta(days=30)
    end = datetime.now().date() - timedelta(days=1)
    while start <= end:
        upload_db.delay(start)
        day = datetime.strftime(start, "%Y-%m-%d")
        get_car_efficiency.delay(day)
        start += timedelta(days=1)
