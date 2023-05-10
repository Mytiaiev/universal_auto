from django.db import IntegrityError

from app.models import UaGpsService

# States [key its NameService+Func in class]
uagps_states = {
    'BASE_URL': ('https://uagps.net/', 'url'),
    'UAGPS_LOGIN_1': ('user', 'ID'),
    'UAGPS_LOGIN_2': ('passw', 'ID'),
    'UAGPS_LOGIN_3': ('submit', 'ID'),
    'UAGPSS_GENERATE_REPORT_1': ("//div[@title='Reports']", 'xpath'),
    'UAGPSS_GENERATE_REPORT_2': ("//input[@id='report_templates_filter_units']", 'XPATH'),
    'UAGPSS_GENERATE_REPORT_3': ('//div[starts-with(text(),', 'XPATH'),
    'UAGPSS_GENERATE_REPORT_4': ("time_from_report_templates_filter_time", 'ID'),
    'UAGPSS_GENERATE_REPORT_5': ("time_to_report_templates_filter_time", 'ID'),
    'UAGPSS_GENERATE_REPORT_6': ('//input[@value="Execute"]', 'XPATH'),
    'UAGPSS_GENERATE_REPORT_7': ("//tr[@pos='5']/td[2]", 'XPATH'),
    'UAGPSS_GENERATE_REPORT_8': ("//tr[@pos='4']/td[2]", 'XPATH'),
}


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
