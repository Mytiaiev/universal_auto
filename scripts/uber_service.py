from app.models import UberService
from django.db import IntegrityError
from scripts.selector_services import uber_states


def init_service_uber():
    for key, value in uber_states.items():
        uber_service = UberService.objects.filter(key=key).first()
        if not uber_service:
            new_key = UberService(key=key,
                                  value=value[0],
                                  description=value[1])
            try:
                new_key.save()
            except IntegrityError:
                pass
        else:
            if uber_service.value != value[0]:
                uber_service.value = value[0]
                uber_service.save()


def run():
    init_service_uber()
    print('Script UberService done')
