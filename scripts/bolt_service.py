from app.models import BoltService
from django.db import IntegrityError
from scripts.selector_services import bolt_states


def init_service_bolt():
    for key, value in bolt_states.items():
        if not BoltService.objects.filter(key=key):
            bolt_service = BoltService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                bolt_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_bolt()
    print('Script BoltService done')
