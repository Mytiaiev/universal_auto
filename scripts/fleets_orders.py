from datetime import datetime, timedelta
from auto.tasks import get_orders_from_fleets


def run(partner_id):
    start = datetime.now().date() - timedelta(days=15)
    end = datetime.now().date() - timedelta(days=1)
    while start <= end:
        day = datetime.strftime(start, "%Y-%m-%d")
        get_orders_from_fleets.delay(partner_id, day)
        start += timedelta(days=1)


 