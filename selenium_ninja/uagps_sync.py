import json
import datetime
import requests
from _decimal import Decimal
from django.utils import timezone
from app.models import UaGpsService, ParkSettings, Driver, Vehicle, StatusChange, RentInformation, UberTrips, Partner


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
        parameters = {
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
            'params': json.dumps(parameters)
        }
        try:
            report = requests.get(self.url, params=params)
            print(report.json())
            raw_time = report.json()['reportResult']['stats'][4][1]
            clean_time = [int(i) for i in raw_time.split(':')]
            rent_time = datetime.timedelta(hours=clean_time[0], minutes=clean_time[1], seconds=clean_time[2])
            raw_distance = report.json()['reportResult']['stats'][5][1]
            rent_distance = Decimal(raw_distance.split(' ')[0])
        except Exception as e:
            print(e)
        return rent_distance, rent_time

    @staticmethod
    def get_timestamp(timeframe):
        return int(timeframe.timestamp())

    def get_rent_distance(self, partner_id):
        start = timezone.datetime.combine(timezone.localtime(), datetime.datetime.min.time()).astimezone()
        end = timezone.localtime()
        partner_obj = Partner.objects.get(id=partner_id)
        for _driver in Driver.objects.filter(partner=partner_id):
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
            rent_today = RentInformation.objects.filter(driver=_driver,
                                                        created_at__date=timezone.localtime().date()).first()
            if not rent_today:
                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=rent_time,
                                               rent_distance=rent_distance,
                                               partner=partner_obj)
            else:
                rent_today.rent_distance = rent_distance
                rent_today.rent_time = rent_time
                rent_today.save()

    def total_per_day(self, licence_plate, day):
        start = datetime.datetime.combine(day, datetime.time.min)
        end = datetime.datetime.combine(day, datetime.time.max)
        vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
        if vehicle:
            distance = self.generate_report(self.get_timestamp(start),
                                            self.get_timestamp(end),
                                            vehicle.gps_id)[0]
            return distance, vehicle
