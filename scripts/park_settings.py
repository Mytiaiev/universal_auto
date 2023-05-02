from app.models import ParkSettings


settings = {
    'FREE_RENT': ('15', 'Безкоштовна оренда (км)'),
    'RENT_PRICE': ('15', 'Ціна за аренду (грн)'),
    'DRIVER_PLAN': ('10000', 'План водія (грн)'),
    'TARIFF_IN_THE_CITY': ('15', 'Тариф в місті (грн)'),
    'TARIFF_OUTSIDE_THE_CITY': ('30', 'Тариф за містом (грн)'),
    'TARIFF_CAR_DISPATCH': ('7', 'Тариф за доставку авто за км (грн)'),
    'FREE_CAR_SENDING_DISTANCE': ('5', 'Безкоштовна дистація при замовлені (км)'),
    'CENTRE_CITY_LAT': ('50.4501', 'Широта центра міста Києва'),
    'CENTRE_CITY_LNG': ('30.5234', 'Довгота центра міста Києва'),
    'CENTRE_CITY_RADIUS': ('75000', 'Радіус від центра міста Києва (м)'),
    'CITY_PARK': ("Київ|Київська", 'Місто автопарка (де ми надаємо послуги)'),
    'SEND_TIME_ORDER_MIN': ('20', 'Відправка замовлення водіям (хв, час замовлення - наш час)'),
    'CHECK_ORDER_TIME_SEC': ('305', 'Перевірка чи є замовлення на певний час (с)'),
    'TARIFF_CAR_OUTSIDE_DISPATCH': ('15', 'Доставка авто за місто (грн)'),
    'AVERAGE_DISTANCE_PER_HOUR': ('25', 'Середня проходимість авто по місту (км)'),
    'COST_PER_KM': ('20', 'Середня ціна за км (грн, для UaGPS)'),
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


