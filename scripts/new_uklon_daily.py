from auto.tasks import get_driver_reshuffles, check_available_fleets


def run(*args):
    print(check_available_fleets(4))