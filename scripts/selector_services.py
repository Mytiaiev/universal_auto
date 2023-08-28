# States [key its NameService+Func in class]

bolt_states = {
    'REQUEST_BOLT_LOGIN_URL': ('https://fleetownerportal.live.boltsvc.net/fleetOwnerPortal/', 'url'),
    'R_BOLT_ADD_DRIVER_1': ("https://node.taxify.eu/fleet-registration/driverPortal/", 'url'),
    'BOLT_LOGIN_1': ('email', 'ID'),
    'BOLT_LOGIN_2': ('current-password', 'ID'),
    'BOLT_LOGIN_3': ('//button[@type="submit"]', 'XPATH'),
    'BOLT_LOGIN_URL': ('https://fleets.bolt.eu/v2/login', 'url'),
    'CHECK_LOGIN_BOLT': ('//div[@role="tablist"]', 'XPATH'),
}

newuklon_states = {
    'BASE_URL': ('https://fleets.uklon.com.ua', 'url'),
    'UKLON_LOGIN_1': ('https://fleets.uklon.com.ua/auth/login', 'url'),
    'UKLON_LOGIN_2': ('//input[@data-cy="phone-number-control"]', 'XPATH'),
    'UKLON_LOGIN_3': ('//input[@data-cy="password"]', 'XPATH'),
    'UKLON_LOGIN_4': ('//button[@data-cy="login-btn"]', 'XPATH'),
    'CHECK_LOGIN_UKLON': ('//div[@data-cy="side-nav-menu"]', 'XPATH'),
    'NEWUKLON_ADD_DRIVER_1': ('https://partner-registration.uklon.com.ua/registration', 'url'),
    'NEWUKLON_ADD_DRIVER_2': ("//span[text()='Обрати зі списку']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_3': ("//div[@class='region-name' and contains(text(),'Київ')]", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_4': ("//button[@color='accent']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_5': ("//input[@type='tel']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_6': ("//input", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_7': ("//label[@for='registration-type-fleet']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_8': ("//input[@type='file']", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_9': ("//button[contains(@class, 'green')]", 'XPATH'),
    'NEWUKLON_ADD_DRIVER_10': ("mat-input-2", 'XPATH'),
}

uagps_states = {
    'BASE_URL': ('https://uagps.net/wialon/ajax.html', 'url'),
}

uber_states = {
    "REQUEST_UBER_BASE_URL": ("https://supplier.uber.com/graphql", "url"),
    'BASE_URL': ('https://supplier.uber.com', 'url'),
    'UBER_LOGIN_URL': ('https://auth.uber.com/v2/', 'url'),
    'UBER_LOGIN_1': ('//input[@name="email"]', 'xpath'),
    'UBER_LOGIN_2': ('//button[@id="forward-button"]', 'xpath'),
    'UBER_LOGIN_3': ('PASSWORD', 'ID'),
    'UBER_LOGIN_4': ('//button[@id="alt-PASSWORD"]', 'xpath'),
    'UBER_LOGIN_5': ('//button[@id="alt-alternate-forms-option-modal"]', 'xpath'),
    'UBER_LOGIN_6': ('//div[@id="bottom-modal-content"]/button[2]', 'xpath'),
    'CHECK_LOGIN_UBER': ('//div[@data-tracking-name="vehicles"]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_1': ('https://supplier.uber.com/orgs/', 'url'),
    'UBER_GENERATE_PAYMENTS_ORDER_2': ('//div[@data-testid="report-type-dropdown"]/div/div', 'xpath'),
    'UBER_GENERATE_PAYMENTS_ORDER_3': ('//button[@data-tracking-name="custom-date-range"]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_4': ('//div[@data-baseweb="base-input"][1]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_5': ('//button[@data-testid="generate-report-button"]', 'XPATH'),
    'UBER_GENERATE_TRIPS_1': ('//ul/li/div[text()[contains(.,"Trip Activity")]]', 'XPATH'),
    'UBER_GENERATE_TRIPS_2': ('//ul/li/div[text()[contains(.,"Информация о поездке")]]', 'XPATH'),
    'UBER_CALENDAR_1': ('//button[@aria-live="polite"][1]', 'XPATH'),
    'UBER_CALENDAR_2': ('//li[@role="option" and text()[contains(.,"', 'XPATH'),
    'UBER_CALENDAR_3': ('//button[@aria-live="polite"][2]', 'XPATH'),
    'UBER_CALENDAR_4': ('//div[@aria-roledescription="button"]/div[text()=', 'XPATH'),

    'UBER_DOWNLOAD_PAYMENTS_ORDER_1': ('(//div[@data-testid="paginated-table"]//button)[1]', 'XPATH'),
    'UBER_DOWNLOAD_PAYMENTS_ORDER_2': ('//i[@class="_css-bvkFtm"]', 'XPATH'),

}

states = {
    'UKLON_SESSION': ('https://fleets.uklon.com.ua/api/', 'url'),
    'UKLON_1': ('https://fleets.uklon.com.ua/api/fleets/', 'url'),
    'UKLON_2': ('/vehicles', 'url'),
    'UKLON_3': ('https://fleets.uklon.com.ua/api/fleets/reports/', 'url'),
    'UKLON_4': ('/orders', 'url'),
    'UKLON_5': ('https://fleets.uklon.com.ua/api/geolocation/', 'url'),
    'UKLON_6': ('/drivers', 'url'),
    'UKLON_7': ('/finance/drivers/wallets', 'url'),
    'UKLON_8': ('/finance/wallet/transfers/transfer-to-fleet', 'url')
}