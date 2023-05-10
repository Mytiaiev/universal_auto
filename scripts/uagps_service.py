from app.models import UaGpsService
from django.db import IntegrityError
from scripts.selector_services import uagps_states


def init_service_newuklon():
    for key, value in uagps_states.items():
        if not UaGpsService.objects.filter(key=key):
            uagps_service = UaGpsService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                uagps_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_newuklon()
    print('Script UaGpsService done')
