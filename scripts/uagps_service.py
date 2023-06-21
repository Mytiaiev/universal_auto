from app.models import UaGpsService
from django.db import IntegrityError
from scripts.selector_services import uagps_states


def init_service_newuklon():
    for key, value in uagps_states.items():
        uagps_service = UaGpsService.objects.filter(key=key).first()
        if not uagps_service:
            new_key = UaGpsService(key=key,
                                   value=value[0],
                                   description=value[1])
            try:
                new_key.save()
            except IntegrityError:
                pass
        else:
            if uagps_service.value != value[0]:
                uagps_service.value = value[0]
                uagps_service.save()



def run():
    init_service_newuklon()
    print('Script UaGpsService done')
