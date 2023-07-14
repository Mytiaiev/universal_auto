from auto.tasks import download_daily_report, get_car_efficiency
from scripts.redis_conn import redis_instance


def run(*args):
    redis_instance.set(f'running_{1}', 1)
    print(redis_instance.get(f'running_{1}').decode())
