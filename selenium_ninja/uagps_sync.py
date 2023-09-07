import json
import datetime
import requests
from _decimal import Decimal
from django.utils import timezone
from app.models import UaGpsService, ParkSettings, Driver, Vehicle, StatusChange, RentInformation, Partner, FleetOrder, \
    DriverEfficiency
from scripts.redis_conn import redis_instance


class UaGpsSynchronizer:

    def __init__(self, partner_id, url=UaGpsService.get_value("BASE_URL")):
        self.url = url
        self.partner_id = partner_id
        self.session = self.get_session()

    def get_session(self):

        params = {
            'svc': 'token/login',
            'params': json.dumps({"token": ParkSettings.get_value('UAGPS_TOKEN', partner=self.partner_id)})
        }
        login = requests.get(self.url, params=params)
        return login.json()['eid']

    def get_gps_id(self):
        if not redis_instance().exists(f"{self.partner_id}_gps_id"):
            payload = {"spec": {"itemsType": "avl_resource", "propName": "sys_name", "propValueMask": "*", "sortType": ""},
                       "force": 1, "flags": 5, "from": 0, "to": 4294967295}
            params = {
                'sid': self.session,
                'svc': 'core/search_items',
            }
            params.update({'params': json.dumps(payload)})
            response = requests.post(url=UaGpsService.get_value("BASE_URL"), params=params)
            redis_instance().set(f"{self.partner_id}_gps_id", response.json()['items'][0]['id'])
        return redis_instance().get(f"{self.partner_id}_gps_id")

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
        road_distance = 0
        road_time = datetime.timedelta()
        parameters = {
            "reportResourceId": self.get_gps_id(),
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
            road_time = datetime.timedelta(hours=clean_time[0], minutes=clean_time[1], seconds=clean_time[2])
            raw_distance = report.json()['reportResult']['stats'][5][1]
            road_distance = Decimal(raw_distance.split(' ')[0])
        except Exception as e:
            print(e)
        return road_distance, road_time

    @staticmethod
    def get_timestamp(timeframe):
        return int(timeframe.timestamp())

    def get_road_distance(self, start=None, end=None, delta=None):
        if not start:
            day = timezone.localtime() - datetime.timedelta(days=delta)
            start = timezone.datetime.combine(day, datetime.datetime.min.time()).astimezone()
            end = timezone.datetime.combine(day, datetime.datetime.max.time()).astimezone()
        else:
            pass
        road_dict = {}
        for _driver in Driver.objects.filter(partner=self.partner_id):
            vehicle = _driver.vehicle
            road_distance = 0
            road_time = datetime.timedelta()
            completed = FleetOrder.objects.filter(driver=_driver,
                                                  state=FleetOrder.COMPLETED,
                                                  accepted_time__gte=start,
                                                  accepted_time__lt=end)
            if vehicle and completed:
                for order in completed:
                    end_report = order.finish_time if order.finish_time < end else end
                    report = self.generate_report(self.get_timestamp(timezone.localtime(order.accepted_time)),
                                                  self.get_timestamp(timezone.localtime(end_report)),
                                                  vehicle.gps_id)
                    road_distance += report[0]
                    road_time += report[1]
                # canceled = FleetOrder.objects.filter(driver=_driver,
                #                                      state__in=[FleetOrder.DRIVER_CANCEL,
                #                                                 FleetOrder.SYSTEM_CANCEL,
                #                                                 FleetOrder.CLIENT_CANCEL],
                #                                      accepted_time__gte=start)
                # for order in canceled:
                #     first_status = StatusChange.objects.filter(
                #         driver=_driver.id,
                #         vehicle=vehicle,
                #         name__in=[Driver.ACTIVE, Driver.WITH_CLIENT],
                #         start_time__gte=timezone.localtime(order.accepted_time)).first()
                #     if first_status:
                #         if first_status.name == Driver.WITH_CLIENT:
                #             continue
                #         else:
                #             end_report = first_status.start_time if first_status.start_time < end else end
                #             report = self.generate_report(self.get_timestamp(timezone.localtime(order.accepted_time)),
                #                                           self.get_timestamp(timezone.localtime(end_report)),
                #                                           vehicle.gps_id)
                #             road_distance += report[0]
                #             road_time += report[1]

                yesterday_order = FleetOrder.objects.filter(driver=_driver,
                                                            finish_time__gt=start,
                                                            accepted_time__lte=start).first()
                if yesterday_order:
                    report = self.generate_report(self.get_timestamp(timezone.localtime(start)),
                                                  self.get_timestamp(timezone.localtime(yesterday_order.finish_time)),
                                                  vehicle.gps_id)
                    road_distance += report[0]
                    road_time += report[1]
            road_dict[_driver] = (road_distance, road_time)
        return road_dict

    def total_per_day(self, licence_plate, day):
        start = datetime.datetime.combine(day, datetime.time.min)
        end = datetime.datetime.combine(day, datetime.time.max)
        vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
        if vehicle:
            distance = self.generate_report(self.get_timestamp(start),
                                            self.get_timestamp(end),
                                            vehicle.gps_id)[0]
            return distance, vehicle

    def save_daily_rent(self, delta):
        day = timezone.localtime() - datetime.timedelta(days=delta)
        in_road = self.get_road_distance(self.partner_id, delta=delta)
        for driver, result in in_road.items():
            if driver.vehicle:

                total_km = self.total_per_day(driver.vehicle.licence_plate, day)[0]
                rent_distance = total_km - result[0]
            else:
                rent_distance = 0
            driver_eff = DriverEfficiency.objects.filter(driver=driver, report_from=day).first()
            if driver_eff:
                driver_eff.road_time = result[1]
                driver_eff.save()
            RentInformation.objects.create(report_from=day,
                                           driver=driver,
                                           partner=Partner.get_partner(self.partner_id),
                                           rent_distance=rent_distance)
