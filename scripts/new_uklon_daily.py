from auto.tasks import get_car_efficiency

def run(*args):
    get_car_efficiency.delay(1)

