import json
import datetime
import requests
from _decimal import Decimal
from django.utils import timezone
from app.models import UaGpsService, ParkSettings, Driver, Vehicle, StatusChange, RentInformation, UberTrips


class UaGpsSynchronizer:

    def __init__(self, url=f'{UaGpsService.get_value("BASE_URL")}'):
        self.url = url
        self.session = self.get_session()

    def get_session(self):

        params = {
            'svc': 'token/login',
            'params': json.dumps({"token": f"{ParkSettings.get_value('UAGPS_TOKEN')}"})
        }
        login = requests.get(self.url, params=params)
        return login.json()['eid']

    def get_vehicle_id(self):
        params = {
            'sid': self.session,
            'svc': 'core/update_data_flags',
            'params': json.dumps({"spec": [{"type": "type",
                                            "data": "avl_unit",
                                            "flags": 1,
                                            "mode": 0}]})
        }
        response = requests.get(self.url, params=params)
        for vehicle in response.json():
            Vehicle.objects.filter(licence_plate=vehicle['d']['nm'].split('(')[0]).update(gps_id=vehicle['i'])

    def generate_report(self, start_time, end_time, vehicle_id):
        rent_distance = 0
        rent_time = datetime.timedelta()
        parametrs = {
            "reportResourceId": 66281,
            "reportObjectId": vehicle_id,
            "reportObjectSecId": 0,
            "reportTemplateId": 1,
            "reportTemplate": None,
            "interval": {
                "from": start_time,
                "to": end_time,
                "flags": 16777216
            }
        }

        params = {
            'svc': 'report/exec_report',
            'sid': self.session,
            'params': f'{json.dumps(parametrs)}'
        }
        try:
            report = requests.get(self.url, params=params)
            raw_time = report.json()['reportResult']['stats'][4][1]
            clean_time = [int(i) for i in raw_time.split(':')]
            rent_time = datetime.timedelta(hours=clean_time[0], minutes=clean_time[1], seconds=clean_time[2])
            raw_distance = report.json()['reportResult']['stats'][5][1]
            rent_distance = float(raw_distance.split(' ')[0])
        except:
            pass
        return rent_distance, rent_time

    @staticmethod
    def get_timestamp(timeframe):
        return int(timeframe.timestamp())

    def start_day(self, day):
        start_of_day = day.in_timezone("Europe/Kiev").start_of("day")
        return self.get_timestamp(start_of_day)

    def end_day(self, day):
        end_of_day = day.in_timezone("Europe/Kiev").end_of("day")
        return self.get_timestamp(end_of_day)

    def get_rent_distance(self):
        yesterday = timezone.localtime() - datetime.timedelta(days=1)
        start = timezone.datetime.combine(yesterday, datetime.datetime.min.time()).astimezone()
        end = timezone.datetime.combine(yesterday, datetime.datetime.max.time()).astimezone()
        for _driver in Driver.objects.all():
            if not RentInformation.objects.filter(driver=_driver,
                                                  created_at__date=timezone.localtime().date()):
                rent_distance = 0
                rent_time = datetime.timedelta()
                # car that have worked at that day
                vehicle = _driver.vehicle
                if vehicle:
                    rent_statuses = StatusChange.objects.filter(driver=_driver.id,
                                                                vehicle=vehicle,
                                                                start_time__gte=timezone.localtime(start),
                                                                end_time__lte=timezone.localtime(end))
                    if rent_statuses:
                        first_status = rent_statuses.first()
                        first_report = self.generate_report(self.get_timestamp(timezone.localtime(start)),
                                                            self.get_timestamp(
                                                                timezone.localtime(first_status.start_time)),
                                                            vehicle.gps_id)
                        rent_distance += first_report[0]
                        rent_time += first_report[1]

                        last_status = rent_statuses.last()
                        last_report = self.generate_report(self.get_timestamp(timezone.localtime(last_status.end_time)),
                                                           self.get_timestamp(timezone.localtime(end)),
                                                           vehicle.gps_id)
                        rent_distance += last_report[0]
                        rent_time += last_report[1]
                        statuses = rent_statuses.filter(name__in=[Driver.ACTIVE, Driver.OFFLINE, Driver.RENT])
                        for st in statuses:
                            status_report = self.generate_report(self.get_timestamp(timezone.localtime(st.start_time)),
                                                                 self.get_timestamp(timezone.localtime(st.end_time)),
                                                                 vehicle.gps_id)
                            rent_distance += status_report[0]
                            rent_time += status_report[1]
                    else:
                        report = self.generate_report(self.get_timestamp(timezone.localtime(start)),
                                                      self.get_timestamp(timezone.localtime(end)),
                                                      vehicle.gps_id)
                        rent_distance += report[0]
                        rent_time += report[1]

                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=rent_time,
                                               rent_distance=rent_distance)

    def no_uber_rent_distance(self):
        drivers = Driver.objects.all()
        for driver in drivers:
            rent = RentInformation.objects.filter(driver_name=driver,
                                                  created_at__date=timezone.localtime().date()).first()
            driver_id = driver.get_driver_external_id('Uber')
            distance_in_trips = 0
            if driver_id and rent:
                vehicle = Vehicle.objects.filter(driver=driver).first()
                trips = UberTrips.objects.filter(driver_external_id=driver_id,
                                                 created_at__date=timezone.localtime().date(),
                                                 end_trip__isnull=False)
                for trip in trips:
                    trip_distance = self.generate_report(self.get_timestamp(timezone.localtime(trip.start_trip)),
                                                         self.get_timestamp(timezone.localtime(trip.end_trip)),
                                                         vehicle.gps_id)
                    distance_in_trips += trip_distance[0]
                rent.rent_distance -= Decimal(distance_in_trips)
                rent.save()

    def total_per_day(self, licence_plate, day):
        vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
        if vehicle:
            distance = self.generate_report(self.start_day(day),
                                            self.end_day(day),
                                            vehicle.gps_id)[0]
            return distance
