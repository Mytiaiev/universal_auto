import pendulum
from datetime import datetime
from datetime import timezone

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from app.models import UberPaymentsOrder, BoltPaymentsOrder, UklonPaymentsOrder, SeleniumTools, NewUklonPaymentsOrder, \
    Fleets_drivers_vehicles_rate, Bolt, Fleet
from auto.tasks import download_weekly_report

from auto import celery_app
i = celery_app.control.inspect()
sc = i.scheduled()
ac = i.active()


class DriversRatingMixin:

    def get_rating(self, start=None, end=None):
        st = SeleniumTools(session='')
        if not start:
            start = st.start_of_week()
        if not end:
            end = st.end_of_week()

        # st = SeleniumTools(session='', week_number='2022-09-19')

        fleets = [fleet(start, end) for fleet in GenericDriversRating.get_fleets()]

        return [{'fleet': item.fleet_name, 'rating': item.get_rating()} for item in fleets]


class DriversRating:

    fleet_name = ''
    model = None

    def __init__(self, start_of_week, end_of_week):
        self.start_of_week = start_of_week
        self.end_of_week = end_of_week

    def check_missing_weeks(self, qset):
        dct = {}

        weeks=sorted({x.start_of('week') for x in pendulum.instance(self.end_of_week) - pendulum.instance(self.start_of_week)})
        missing_weeks = []
        for week in weeks:
            weekly_report_exists = False
            for item in qset:
                if week >= item.report_from and week <= item.report_to:
                    weekly_report_exists = True
                    break
            if not weekly_report_exists:
                missing_weeks.append(week.strftime('%Y-%m-%d'))
                dct[(datetime.utcfromtimestamp(week.start_of('week').timestamp()),
                     datetime.utcfromtimestamp(week.end_of('week').timestamp()))] = {}
        if missing_weeks:
            download_weekly_report.delay(self.fleet_name, ';'.join(missing_weeks))
            # download_weekly_report(self.fleet_name, ';'.join(missing_weeks))
        return dct

    def get_rating(self):

        qset = self.model.objects.filter(report_from__lte=self.end_of_week, report_to__gte=self.start_of_week).order_by('report_from')

        dct = self.check_missing_weeks(qset)

        # Group by periods and drivers
        for item in qset:
            period_key = (item.report_from, item.report_to)
            period = dct.get(period_key)
            if not period:
                dct[period_key] = {}
                period = dct[period_key]
            drv = period.get(self.get_driver_identifier(item))
            if not drv:
                period[self.get_driver_identifier(item)] = {'driver': self.get_driver(item), 'trips': 0, 'amount': 0}
                drv = period[self.get_driver_identifier(item)]
            drv['trips'] = drv['trips'] + self.get_trips(item)
            drv['amount'] = drv['amount'] + item.kassa()

        # Sorting and converting to a list
        for k, period in dct.items():
            dct[k] = {'start': k[0], 'end': k[1], 'rating': sorted(list(period.values()), key=lambda item: item['amount'], reverse=True)}

        rating = list(dct.values())

        # Numerating
        for i in range(len(rating)):
            for j in range(len(rating[i]['rating'])):
                rating[i]['rating'][j]['num'] = j + 1

        return rating

    def get_driver(self, item):
        try:
            record = Fleets_drivers_vehicles_rate.objects.get(driver_external_id=self.get_driver_identifier(item),
                                                              fleet__name=item.vendor_name)
            return record.driver.__str__()
        except Fleets_drivers_vehicles_rate.DoesNotExist:
            raise ObjectDoesNotExist
        except Fleets_drivers_vehicles_rate.MultipleObjectsReturned:
            raise MultipleObjectsReturned

    def get_trips(self, item):
        return 0

    def get_driver_identifier(self, item):
        return ''


class GenericDriversRating(type):

    _registry = {}

    def __new__(cls, name, bases, attrs):

        fleet_name_ = attrs.get('fleet_name')
        if fleet_name_ in cls._registry:
            raise ValueError(f'{fleet_name_} is already registered for {name}')

        new_cls = type.__new__(cls, name, bases, attrs)
        cls._registry[fleet_name_] = new_cls

        return new_cls

    @classmethod
    def get_fleets(cls):
        return [item for item in cls._registry.values()]


class UberDriversRating(DriversRating, metaclass=GenericDriversRating):

    fleet_name = 'Uber'
    model = UberPaymentsOrder

    def get_driver(self, item):
        try:
            return super().get_driver(item)
        except ObjectDoesNotExist:
            return f"<ObjectDoesNotExist> {item.first_name} {item.last_name}"
        except MultipleObjectsReturned:
            return f"<MultipleObjectsReturned> {item.first_name} {item.last_name}"

    def get_driver_identifier(self, item):
        return item.driver_uuid


class BoltDriversRating(DriversRating, metaclass=GenericDriversRating):

    fleet_name = 'Bolt'
    model = BoltPaymentsOrder

    def get_driver(self, item):
        try:
            return super().get_driver(item)
        except ObjectDoesNotExist:
            return f"<ObjectDoesNotExist {self.get_driver_identifier(item)}> {item.driver_full_name}"
        except MultipleObjectsReturned:
            return f"<MultipleObjectsReturned {self.get_driver_identifier(item)}> {item.driver_full_name}"

    def get_driver_identifier(self, item):
        return item.mobile_number


class UklonDriversRating(DriversRating, metaclass=GenericDriversRating):

    fleet_name = 'Uklon'
    model = UklonPaymentsOrder

    def get_driver(self, item):
        try:
            return super().get_driver(item)
        except ObjectDoesNotExist:
            return f"<ObjectDoesNotExist> {item.licence_plate}"
        except MultipleObjectsReturned:
            return f"<MultipleObjectsReturned> {item.licence_plate}"

    def get_trips(self, item):
        return item.total_rides

    def get_driver_identifier(self, item):
        return item.signal

    def check_missing_weeks(self, qset):
        return {}


class NewUklonDriversRating(DriversRating, metaclass=GenericDriversRating):

    fleet_name = 'NewUklon'
    model = NewUklonPaymentsOrder

    def get_driver(self, item):
        try:
            return super().get_driver(item)
        except ObjectDoesNotExist:
            return f"<ObjectDoesNotExist> {item.full_name}"
        except MultipleObjectsReturned:
            return f"<MultipleObjectsReturned> {item.full_name}"

    def get_trips(self, item):
        return item.total_rides

    def get_driver_identifier(self, item):
        return item.signal
