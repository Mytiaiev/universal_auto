from django.db import IntegrityError
from scripts.settings_for_park import settings
from app.models import ParkSettings


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


