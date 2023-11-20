from app.models import ParkSettings, UberService, UaGpsService, BoltService, NewUklonService, Service
from django.db import IntegrityError
from scripts.selector_services import uber_states, uagps_states, bolt_states, newuklon_states, states
from scripts.settings_for_park import settings


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


def init_service_uagps():
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


def init_service_():
    for key, value in states.items():
        service = Service.objects.filter(key=key).first()
        if not service:
            new_key = Service(key=key,
                              value=value[0],
                              description=value[1])
            try:
                new_key.save()
            except IntegrityError:
                pass
        else:
            if service.value != value[0]:
                service.value = value[0]
                service.save()


def run():
    init_park_settings()
    init_service_uagps()
    init_service_uber()
    init_service_bolt()
    init_service_()
    init_service_newuklon()
    print('Script ParkSettings done')


