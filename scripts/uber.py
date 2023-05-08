from app.models import UberService

# States [key its NameService+Func in class]
states = {
    'BASE_URL': ('https://supplier.uber.com', 'url'),
    'UBER_LOGIN_V2_1': ('https://drivers.uber.com/', 'url'),
    'UBER_LOGIN_V2_2.1': ('PHONE_NUMBER_or_EMAIL_ADDRESS', 'ID'),
    'UBER_LOGIN_V2_2.2': ('forward-button', 'ID'),
    'UBER_LOGIN_V2_3.1': ('PASSWORD', 'ID'),
    'UBER_LOGIN_V2_3.2': ('forward-button', 'ID'),
    'UBER_LOGIN_V3_1': ('https://auth.uber.com/v2/', 'url'),
    'UBER_LOGIN_V3_2.1': ('PHONE_NUMBER_or_EMAIL_ADDRESS', 'ID'),
    'UBER_LOGIN_V3_2.2': ('forward-button', 'ID'),
    'UBER_LOGIN_V3_3': ('alt-PASSWORD', 'ID'),
    'UBER_PASSWORD_FORM_V3_1': ('PASSWORD', 'ID'),
    'UBER_PASSWORD_FORM_V3_2': ('forward-button', 'ID'),
    'UBER_LOGIN_1': ('https://auth.uber.com/login/', 'url'),
    'UBER_LOGIN_2.1': ('userInput', 'CLASS_NAME'),
    'UBER_LOGIN_2.2': ('next-button-wrapper', 'CLASS_NAME'),
    'UBER_LOGIN_3.1': ('password', 'CLASS_NAME'),
    'UBER_LOGIN_3.2': ('next-button-wrapper', 'CLASS_NAME'),
    'UBER_GENERATE_PAYMENTS_ORDER_1': (
        'https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/reports', 'url'),
    'UBER_GENERATE_PAYMENTS_ORDER_2': ('//div[@data-testid="report-type-dropdown"]/div/div', 'xpath'),
    'UBER_GENERATE_PAYMENTS_ORDER_3': ('//ul/li/div[text()[contains(.,"Payments Driver")]]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_4': ('//ul/li/div[text()[contains(.,"Платежи (водитель)")]]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_5': ('//div[2]/div/div/div[1]/button[2]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_6': (
        '(//input[@aria-describedby="datepicker--screenreader--message--input"])[1]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_7': ('//button[@aria-label="Next month."]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_8': ('//button[@aria-label="Previous month."]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_9': ('//div[@aria-roledescription="button"]/div[text()=', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_10': (
        '(//input[@aria-describedby="datepicker--screenreader--message--input"])[2]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_11': ('(//button[@aria-live="polite"])[1]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_12': ('(//li[@role="option" and text()[contains(.,"', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_13': ('(//button[@aria-live="polite"])[2]', 'XPATH'),
    'UBER_GENERATE_PAYMENTS_ORDER_14': ('//button[@data-testid="generate-report-button"]', 'XPATH'),
    'UBER_DOWNLOAD_PAYMENTS_ORDER_1': ('(//div[@data-testid="paginated-table"]//button)[1]', 'XPATH'),
    'UBER_DOWNLOAD_PAYMENTS_ORDER_2': ('//i[@class="_css-bvkFtm"]', 'XPATH'),
    'UBER_OTP_CODE_V2_1': ('PHONE_SMS_OTP-0', 'ID'),
    'UBER_OTP_CODE_V2_2': ('PHONE_SMS_OTP-1', 'ID'),
    'UBER_OTP_CODE_V2_3': ('PHONE_SMS_OTP-2', 'ID'),
    'UBER_OTP_CODE_V2_4': ('PHONE_SMS_OTP-3', 'ID'),
    'UBER_OTP_CODE_V2_5': ('forward-button', 'ID'),
    'UBER_OTP_CODE_V1_1': ('verificationCode', 'ID'),
    'UBER_OTP_CODE_V1_2': ("next-button-wrapper", 'CLASS_NAME'),
    'UBER_FORCE_OPT_FORM': ('alt-PHONE-OTP', 'ID'),
    'UBER_ADD_DRIVER_1': ('https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/drivers', 'url'),
    'UBER_ADD_DRIVER_2': ('//button', 'XPATH'),
    'UBER_ADD_DRIVER_3': ('//div[2]/div/input', 'XPATH'),
    'UBER_ADD_DRIVER_4': ('//div[5]/div[2]/button', 'XPATH'),
}


def init_service_uber():
    for key, value in states.items():
        if not UberService.objects.filter(key=key):
            uber_service = UberService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                uber_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_uber()
    print('Script UberService done')
