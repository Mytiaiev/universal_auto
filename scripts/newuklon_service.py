from app.models import NewUklonService

# States [key its NameService+Func in class]
states = {
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
}


def init_service_newuklon():
    for key, value in states.items():
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
