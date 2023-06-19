from app.models import BoltService
from django.db import IntegrityError
from scripts.selector_services import bolt_states


def init_service_bolt():
    for key, value in bolt_states.items():
        bolt_service = BoltService.objects.filter(key=key).first()
        if not bolt_service:
            new_key = BoltService(key=key,
                                  value=value[0],
                                  description=value[1])
            try:
                new_key.save()
            except IntegrityError:
                pass
        else:
            if bolt_service.value != value[0]:
                bolt_service.value = value[0]
                bolt_service.save()


def run():
    init_service_bolt()
    print('Script BoltService done')
