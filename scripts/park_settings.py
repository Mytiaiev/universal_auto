from django.db import IntegrityError

from app.models import ParkSettings


settings = {
    'FREE_RENT': ('15', 'Безкоштовна оренда (км)'),
    'RENT_PRICE': ('15', 'Ціна за аренду (грн)'),
    'TARIFF_IN_THE_CITY': ('15', 'Тариф в місті (грн)'),
    'TARIFF_OUTSIDE_THE_CITY': ('30', 'Тариф за містом (грн)'),
    'TARIFF_CAR_DISPATCH': ('7', 'Тариф за доставку авто за км (грн)'),
    'FREE_CAR_SENDING_DISTANCE': ('5', 'Безкоштовний радіус подачі (км)'),
    'CENTRE_CITY_LAT': ('50.4501', 'Широта центра міста Києва'),
    'CENTRE_CITY_LNG': ('30.5234', 'Довгота центра міста Києва'),
    'CENTRE_CITY_RADIUS': ('75000', 'Радіус від центра міста Києва (м)'),
    'CITY_PARK': ("Київ|Київська", 'Місто автопарка (де ми надаємо послуги)'),
    'SEND_TIME_ORDER_MIN': ('20', 'Відправка замовлення водіям (хв, час замовлення - наш час)'),
    'TIME_ORDER_MIN': ('60', 'Мінімальний час для передзамовлення'),
    'CHECK_ORDER_TIME_MIN': ('5', 'Перевірка чи є замовлення на певний час (хв)'),
    'TARIFF_CAR_OUTSIDE_DISPATCH': ('15', 'Доставка авто за місто (грн)'),
    'AVERAGE_DISTANCE_PER_HOUR': ('25', 'Середня проходимість авто по місту (км)'),
    'COST_PER_KM': ('20', 'Середня ціна за км (грн, для UaGPS)'),
    'GOOGLE_API_KEY': ('Enter google api', 'Ключ Google api'),
    'UBER_NAME': ('Enter username for Uber', 'Ім\'я користувача Uber'),
    'UBER_PASSWORD': ('Enter password for Uber', 'Пароль користувача Uber'),
    'BOLT_NAME': ('Enter username for Bolt', 'Ім\'я користувача Bolt'),
    'BOLT_PASSWORD': ('Enter password for Bolt', 'Пароль користувача Bolt'),
    'UKLON_NAME': ('Enter username for Uklon', 'Ім\'я користувача Uklon'),
    'UKLON_PASSWORD': ('Enter password for Uklon', 'Пароль користувача Uklon'),
    'UKLON_TOKEN': ('Enter token for Uklon', 'Код автопарку в Uklon'),
    'UAGPS_LOGIN': ('Enter username for Uagps', 'Ім\'я користувача Uagps'),
    'UAGPS_PASSWORD': ('Enter password for Uagps', 'Пароль Uagps'),
    'MOBIZON_DOMAIN': ('https://api.mobizon.ua/service/message/sendsmsmessage', 'Домен для смс розсилки'),
    'MOBIZON_API_KEY': ('Enter api key', 'API KEY для розсилки смс'),
    'WITHDRAW_UKLON': ('150', 'Залишок на карті водія Uklon (грн)'),
    'DRIVERS_CHAT': ('-863882769', 'Чат водіїв'),
    'SEND_DISPATCH_MESSAGE': ('0.3', 'Повідомити про подачу (км)'),
    'MESSAGE_APPEAR': ('30', 'Час до зникнення замовлення у водія (с)'),
    'SEARCH_TIME': ('180', 'Час пошуку водія (с)'),
    'MINIMUM_PRICE_RADIUS': ('30', 'Мінімальна ціна за радіус (грн)'),
    'MAXIMUM_PRICE_RADIUS': ('1000', 'Максимальна ціна за радіус (грн)'),
    'MANAGER_ID': ('515224934', 'Тимчасово id менеджера')
}


def init_park_settings():
    for key, value in settings.items():
        response = ParkSettings.objects.filter(key=key).first()
        if not response:
            park_setting = ParkSettings(
                key=key,
                value=value[0],
                description=value[1] or '')
            try:
                park_setting.save()
            except IntegrityError:
                pass
        else:
            if not response.description:
                response.description = settings[f'{key}'][1]
                response.save()
            continue


def run():
    init_park_settings()
    print('Script ParkSettings done')


