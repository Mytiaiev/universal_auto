import json
import datetime
import requests
from _decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from app.models import UaGpsService, ParkSettings, Driver, Vehicle, StatusChange, RentInformation, Partner


class UaGpsSynchronizer:

    def __init__(self, url=UaGpsService.get_value("BASE_URL")):
        self.url = url
        self.session = self.get_session()

    def get_session(self):

        params = {
            'svc': 'token/login',
            'params': json.dumps({"token": ParkSettings.get_value('UAGPS_TOKEN')})
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
            road_distance = 0
            rent_distance = 0
            road_time = datetime.timedelta()
            # car that have worked at that day
            vehicle = _driver.vehicle
            if vehicle:
                road_statuses = StatusChange.objects.filter(driver=_driver.id,
                                                            vehicle=vehicle,
                                                            name=Driver.WITH_CLIENT,
                                                            start_time__gte=timezone.localtime(start))
                if road_statuses:
                    for status in road_statuses:
                        if status.end_time is not None:
                            report = self.generate_report(self.get_timestamp(timezone.localtime(status.start_time)),
                                                          self.get_timestamp(timezone.localtime(status.end_time)),
                                                          vehicle.gps_id)
                        else:
                            report = self.generate_report(self.get_timestamp(timezone.localtime(status.start_time)),
                                                          self.get_timestamp(timezone.localtime(end)),
                                                          vehicle.gps_id)
                        road_distance += report[0]
                        road_time += report[1]
                    total = self.total_per_day(vehicle.licence_plate, end)[0]
                    rent_distance = total - road_distance
                else:
                    last_status = StatusChange.objects.filter(driver=_driver.id,
                                                              vehicle=vehicle).last()
                    if last_status.name == Driver.WITH_CLIENT:
                        if last_status.end_time:
                            report = self.generate_report(self.get_timestamp(last_status.end_time),
                                                          self.get_timestamp(timezone.localtime(end)),
                                                          vehicle.gps_id)
                        else:
                            report = (0, datetime.timedelta(minutes=60))

                    else:
                        report = self.generate_report(self.get_timestamp(timezone.localtime(start)),
                                                      self.get_timestamp(timezone.localtime(end)),
                                                      vehicle.gps_id)
                    rent_distance = report[0]

            rent_today = RentInformation.objects.filter(driver=_driver,
                                                        created_at__date=timezone.localtime().date())
            if not rent_today:
                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=road_time,
                                               rent_distance=rent_distance,
                                               partner=partner_obj)
            else:
                rent_distance -= rent_today.aggregate(distance=Sum('rent_distance'))['distance']
                road_time -= rent_today.aggregate(time=Sum('rent_time'))['time']
                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=road_time,
                                               rent_distance=rent_distance,
                                               partner=partner_obj)

    def total_per_day(self, licence_plate, day):
        start = datetime.datetime.combine(day, datetime.time.min)
        end = datetime.datetime.combine(day, datetime.time.max)
        vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
        if vehicle:
            distance = self.generate_report(self.get_timestamp(start),
                                            self.get_timestamp(end),
                                            vehicle.gps_id)[0]
            return distance, vehicle
