from app.models import NewUklonService
from django.db import IntegrityError
from scripts.selector_services import newuklon_states


def init_service_newuklon():
    for key, value in newuklon_states.items():
        if not NewUklonService.objects.filter(key=key):
            newuklon_service = NewUklonService(
                key=key,
                value=value[0],
                description=value[1])
            try:
                newuklon_service.save()
            except IntegrityError:
                pass
        else:
            continue


def run():
    init_service_newuklon()
    print('Script NewUklonService done')
