from app.models import NewUklonService
from django.db import IntegrityError
from scripts.selector_services import newuklon_states


def init_service_newuklon():
    for key, value in newuklon_states.items():
        newuklon_service = NewUklonService.objects.filter(key=key).first()
        if not NewUklonService.objects.filter(key=key):
            new_key = NewUklonService(key=key,
                                      value=value[0],
                                      description=value[1])
            try:
                new_key.save()
            except IntegrityError:
                pass
        else:
            if newuklon_service.value != value[0]:
                newuklon_service.value = value[0]
                newuklon_service.save()


def run():
    init_service_newuklon()
    print('Script NewUklonService done')
