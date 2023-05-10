from app.models import UberService
from django.db import IntegrityError
from scripts.selector_services import uber_states


def init_service_uber():
    for key, value in uber_states.items():
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
