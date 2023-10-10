settings = {
    'TARIFF_IN_THE_CITY': ('15', 'Тариф в місті (грн)'),
    'TARIFF_OUTSIDE_THE_CITY': ('30', 'Тариф за містом (грн)'),
    'TARIFF_CAR_DISPATCH': ('7', 'Тариф за доставку авто за км (грн)'),
    'FREE_CAR_SENDING_DISTANCE': ('5', 'Безкоштовний радіус подачі (км)'),
    'PERSONAL_CLIENT_NOTIFY_KM': ('10', 'Сповіщення до закінчення ордеру (км)'),
    'PERSONAL_CLIENT_NOTIFY_MIN': ('10', 'Сповіщення до закінчення ордеру (хв)'),
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
    'MOBIZON_DOMAIN': ('https://api.mobizon.ua/service/message/sendsmsmessage', 'Домен для смс розсилки'),
    'MOBIZON_API_KEY': ('Enter api key', 'API KEY для розсилки смс'),
    'SEND_DISPATCH_MESSAGE': ('0.3', 'Повідомити про подачу (км)'),
    'MESSAGE_APPEAR': ('30', 'Час до зникнення замовлення у водія (с)'),
    'SEARCH_TIME': ('180', 'Час пошуку водія (с)'),
    'MINIMUM_PRICE_RADIUS': ('30', 'Мінімальна ціна за радіус (грн)'),
    'MAXIMUM_PRICE_RADIUS': ('1000', 'Максимальна ціна за радіус (грн)'),
    'ORDER_CHAT': ('515224934', 'Чат замовлень'),
    'UKLON_TOKEN': ('Enter token for Uklon', 'Код автопарку в Uklon'),
    'GOOGLE_ID_ORDER_CALENDAR': ('Введіть ID календаря для замовлень', 'ID календаря Ninja'),
    'DEVELOPER_CHAT_ID': ('-900290422', 'Чат для розробників'),
    'PRIVACY_POLICE': ('url', 'Політика конфіденційності'),
    'CONTRACT_OFFER': ('url', 'Договір оферти'),
    'SHIPPING_CHILDS': ('url', 'Перевезення дітей'),
    'USER_DUTY': ('100', 'Ліміт боргу для користувача'),
    'CANCEL_ORDER': ('100', 'Ціна за відмінення замовлення'),
    'MINIMUM_PRICE_FOR_ORDER': ('150', 'Мінімальна ціна за замовлення'),
    'NINJA_PHONE': ('///', 'Номер телефону Ninja автопарку'),
    'NINJA_EMAIL': ('///', 'Електрона почта Ninja автопарку'),
    'NINJA_ADDRESS': ('///', 'Адреса офіса Ninja автопарку'),
}

standard_rates = {
    "DAY": ((1000, 0.3), (1500, 0.4), (2000, 0.5), (2500, 0.6), (3000, 0.7), (3500, 0.8), (4000, 0.9), (4500, 1)),
    "WEEK": ((6000, 0.3), (9000, 0.4), (12000, 0.5), (15000, 0.6), (18000, 0.7), (20000, 0.8), (25000, 0.9), (30000, 1))
}

settings_for_partner = {
    "START_CHECK_CASH": ('1000', 'Сума для початку перевірки готівки')
}