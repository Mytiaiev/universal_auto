from app.models import BoltService

# States [key its NameService+Func in class]
states = {
    'BASE_URL': ('https://fleets.bolt.eu', 'url'),
    'BOLT_LOGIN_1': ('https://fleets.bolt.eu/login', 'url'),
    'BOLT_LOGIN_2': ('username', 'ID'),
    'BOLT_LOGIN_3': ('password', 'ID'),
    'BOLT_LOGIN_4': ('//button[@type="submit"]', 'XPATH'),
    'BOLT_DOWNLOAD_PAYMENTS_ORDER_1': ('https://fleets.bolt.eu/company/58225/reports/weekly', 'url'),
    'BOLT_DOWNLOAD_PAYMENTS_ORDER_2': ('//div/div/table', 'xpath'),
    'BOLT_DOWNLOAD_PAYMENTS_ORDER_3': ('https://fleets.bolt.eu/company/58225/reports/daily/', 'url'),
    'BOLT_DOWNLOAD_PAYMENTS_ORDER_4': ('//table/tbody/tr/td[text()=', 'XPATH'),
    'BOLT_DOWNLOAD_PAYMENTS_ORDER_5': ('./../td/a', 'XPATH'),
    'BOLT_ADD_DRIVER_1': ('https://fleets.bolt.eu/company/58225/driver/add', 'url'),
    'BOLT_ADD_DRIVER_2': ('email', 'ID'),
    'BOLT_ADD_DRIVER_3': ('phone', 'ID'),
    'BOLT_ADD_DRIVER_4': ('ember38', 'ID'),
    'BOLT_ADD_DRIVER_5': ('//a[text()="Продовжити реєстрацію"]', 'XPATH'),
    'BOLT_ADD_DRIVER_6': ('//input[@id="first_name"]', 'XPATH'),
    'BOLT_ADD_DRIVER_7': ('//input[@id="last_name"]', 'XPATH'),
    'BOLT_ADD_DRIVER_8': ('//button[@type="submit"]', 'XPATH'),
    'BOLT_ADD_DRIVER_9': ('//div[@class="form-group"]', 'XPATH'),
    'BOLT_ADD_DRIVER_10': (
        '//div[@class="ember-basic-dropdown-content-wormhole-origin"]/div[contains(@id, "ember-basic-dropdown-content-")]',
        'XPATH'),
    'BOLT_ADD_DRIVER_11': ('.//a[.//span[text()=', 'XPATH'),
    'BOLT_ADD_DRIVER_12': ("//label[contains(., 'Завантажити файл')]", 'XPATH'),
    'BOLT_ADD_DRIVER_13': ("./input", 'XPATH'),
    'BOLT_ADD_DRIVER_14': ("//button[@type='submit']", 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_1': ('https://fleets.bolt.eu/company/58225/drivers', 'url'),
    'BOLTS_GET_DRIVERS_TABLE_2': ('//table[@class="table"]', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_3': ('//table[@class="table"]', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_4': (']/tbody/tr[', '_'),
    'BOLTS_GET_DRIVERS_TABLE_4.1': (']/td[2]/span', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_5': ('//table[@class="table"][', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_5.1': (']/td[1]/a', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_5.2': (']/td[3]/a', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_5.3': (']/td[4]/a', 'XPATH'),
    'BOLTS_GET_DRIVERS_TABLE_5.4': (']/td[5]/span', 'XPATH'),
    'BOLTS_GET_DRIVER_STATUS_1': ('https://fleets.bolt.eu/v2/liveMap', 'url'),
    'BOLTS_GET_DRIVER_STATUS_2': ('//div[contains(@class, "map-overlay")]', 'XPATH'),
    'BOLTS_GET_DRIVER_STATUS_FROM_MAP_1': ("//button[@aria-label='Close']", 'XPATH'),
    'BOLTS_GET_DRIVER_STATUS_FROM_MAP_2': (
        '//div[contains(@class, "map-overlay")]/div/div[1]/div[@role="tablist"]/div', 'XPATH'),
    'BOLTS_GET_DRIVER_STATUS_FROM_MAP_3': (
        '//div[contains(@class, "map-overlay")]/div/div/div[@role="button"][', 'XPATH'),
    'BOLTS_GET_DRIVER_STATUS_FROM_MAP_3.1': (']/div/div/div[1]/span/span', 'XPATH'),
}


def init_service_bolt():
    for key, value in states.items():
        if not BoltService.objects.filter(key=key):
            bolt_service = BoltService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                bolt_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_bolt()
    print('Script BoltService done')
