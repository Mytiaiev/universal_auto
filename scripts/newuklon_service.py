from app.models import NewUklonService

# States [key its NameService+Func in class]
newuklon_states = {
    'BASE_URL': ('https://fleets.uklon.com.ua', 'url'),
    'NEWUKLON_LOGIN_1': ('https://fleets.uklon.com.ua/auth/login', 'url'),
    'NEWUKLON_LOGIN_2': ('//input[@data-cy="phone-number-control"]', 'XPATH'),
    'NEWUKLON_LOGIN_3': ('//input[@data-cy="password"]', 'XPATH'),
    'NEWUKLON_LOGIN_4': ('//button[@data-cy="login-btn"]', 'XPATH'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_1': ('https://fleets.uklon.com.ua/workspace/orders', 'url'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_2': ('//flt-group-filter[1]/flt-date-range-filter/mat-form-field/div', 'xpath'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_3': ('//mat-option/span/div[text()=" Вибрати період "]', 'XPATH'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_4': ('//input', 'XPATH'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_5': ('//span[text()= " Застосувати "]', 'XPATH'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_6': ('//span[text()=" Минулий тиждень "]', 'XPATH'),
    'NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_7': ('//flt-filter-group/div/div/button', 'XPATH'),
    'NEWUKLON_ADD_DRIVER_1': ('https://partner-registration.uklon.com.ua/registration', 'url'),
    'NEWUKLON_ADD_DRIVER_2': ("//span[text()='Обрати зі списку']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_3': ("//div[@class='region-name' and contains(text(),'Київ')]", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_4': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_5': ("//input[@type='tel']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_6': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_7': ("//input", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_8': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_9': ("//label[@for='registration-type-fleet']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_10': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_11': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_12': ("//input[@type='file']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_13': ("//button[contains(@class, 'green')]", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_14': ("//button[contains(@class, 'green')]", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_15': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_16': ("mat-input-2", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_17': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_1': ('https://fleets.uklon.com.ua/workspace/drivers', 'url'),
    'NEWUKLONS_GET_DRIVERS_TABLE_2': ('//upf-drivers-list[@data-cy="driver-list"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_3.1': ('//cdk-row[', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_3.2': (']/cdk-cell[@data-cy="cell-FullName"]//a', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_4': ('//span[@data-cy="driver-name"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_5': ('//dd[@data-cy="driver-email"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_6': ('//span[@data-cy="driver-phone"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_7': ('//dd[@data-cy="driver-signal"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_8': ('//div[@class="mat-tab-labels"]/div[@aria-posinset="4"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_9': ('//mat-slide-toggle[@formcontrolname="walletToCard"]//input', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_10': ('//div/a[contains(@class, "tw-font-medium")]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_11': ('//span[@data-cy="license-plate"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_12': ('//span[@data-cy="make-model-year"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVERS_TABLE_13': ('//dd[@data-cy="vin-code"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_1': ('//div[@role="tab"]/div[text()="Поїздки"]', 'xpath'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_2': ('//button[@data-cy="order-filter-apply-btn"]', 'xpath'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_3': ('//table[@data-cy="trips-list-table"]/tbody/tr[', '_'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_3.1': (']/td[@data-cy="td-driver"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_3.2': (']/td[@data-cy="td-pickup-time"]', 'XPATH'),
    'NEWUKLONS_GET_DRIVER_STATUS_FROM_TABLE_3.3': (']/td[@data-cy="td-status"]/i', 'XPATH'),
    'NEWUKLONS_GET_DRIVER_STATUS_1': ('https://fleets.uklon.com.ua/workspace/orders', 'url'),
    'NEWUKLONS_GET_DRIVER_STATUS_2': ('//div[@role="tab"]/div[text()="Поїздки"]', 'xpath'),
    'NEWUKLONS_WITHDRAW_MONEY_1': ('https://fleets.uklon.com.ua/workspace/finance', 'url'),
    'NEWUKLONS_WITHDRAW_MONEY_2': ("//div[text()='Гаманці водіїв']", 'xpath'),
    'NEWUKLONS_WITHDRAW_MONEY_3': ("//span[@class='mat-checkbox-inner-container']", 'XPATH'),
    'NEWUKLONS_WITHDRAW_MONEY_4': ("//input[@formcontrolname='remaining']", 'XPATH'),
    'NEWUKLONS_WITHDRAW_MONEY_5': ("//button/span[text()=' Перевод на гаманець автопарку ']", 'XPATH'),
    'NEWUKLONS_WITHDRAW_MONEY_6': ("//button/span[text()=' Перевести гроші ']", 'XPATH'),
}


def init_service_newuklon():
    for key, value in newuklon_states.items():
        if not NewUklonService.objects.filter(key=key):
            newuklon_service = NewUklonService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                newuklon_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_newuklon()
    print('Script NewUklonService done')
