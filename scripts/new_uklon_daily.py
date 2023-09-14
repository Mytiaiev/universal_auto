from auto.tasks import get_driver_reshuffles

def run(*args):
    get_driver_reshuffles.delay()