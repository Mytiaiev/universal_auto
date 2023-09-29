from auto.tasks import get_driver_reshuffles, check_available_fleets
from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    # rate = [(1600, 0.38), (1800, 0.44), (2000, 0.5), (2500, 0.55), (3000, 0.6)]
    # kasa = 18000 driver = 9450 partner = 8550 150% plan
    # kasa = 16000 driver = 8250 partner = 7750
    # kasa = 14000 driver = 7099 partner = 6901
    # kasa = 12000 driver = 6000 partner = 6000 100% plan
    # kasa = 10000 driver = 4422 partner = 5578
    # kasa = 9600 driver = 3648 partner = 5952 80% plan
    # Троценко каса 10546,04 зарплата 4393,14
    # Половко каса 20186,83 зарплата 10685.45
    rate_tiers = [(9000, 0.40), (10500, 0.45), (12000, 0.5), (15000, 0.6), (18000, 0.7), (20000, 0.8), (25000, 0.9),
                  (30000, 1)]
    kasa_list = [20186.83, 13092.38, 12300, 11241.07, 10801.32, 10546.04, 3414.82]
    driver_payment = [11668.14, 6655.42, 6180.0, 4645.53, 4425.66, 4298.02, 1365.92]

    # Initialize driver_spending
    for kasa in kasa_list:
        driver_spending = 0
        tier = 0
        rates = rate_tiers[2:] if kasa >= 12000 else rate_tiers
        for tier_kasa, rate in rates:
            tier_kasa -= tier
            if kasa > tier_kasa:
                driver_spending += tier_kasa * rate
                kasa -= tier_kasa
                tier += tier_kasa
            else:
                driver_spending += kasa * rate
                break
        print(driver_spending)