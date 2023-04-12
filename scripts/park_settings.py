from app.models import ParkSettings


default = '0'
settings = {
    'FREE_RENT': default,
    'RENT_PRICE': default,
    'TARIFF_IN_THE_CITY': '15',
    'TARIFF_OUTSIDE_THE_CITY': '30',
    'SEND_TIME_ORDER_MIN': 20,
    'CHECK_ORDER_TIME_SEC': 305
}


def init_park_settings():
    for key, value in settings.items():
        if not ParkSettings.objects.filter(key=key):
            park_setting = ParkSettings(
                key=key,
                value=value)
            try:
                park_setting.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_park_settings()
    print('Script ParkSettings done')


