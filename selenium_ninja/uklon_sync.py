import json
import uuid
from datetime import datetime

import requests
from django.utils import timezone

from app.models import ParkSettings, Fleets_drivers_vehicles_rate, Driver, Payments, Service, Partner, FleetOrder
from scripts.redis_conn import redis_instance
from selenium_ninja.synchronizer import Synchronizer
from django.db import IntegrityError


class UklonRequest(Synchronizer):

    def get_header(self) -> dict:
        token = self.redis.get(f"{self.partner_id}token")
        headers = {
            'Authorization': f'Bearer {token}'
         }
        return headers

    def park_payload(self) -> dict:
        payload = {
            'client_id': ParkSettings.get_value(key='CLIENT_ID', partner=self.partner_id),
            'contact': ParkSettings.get_value(key='UKLON_NAME', partner=self.partner_id),
            'device_id': "38c13dc5-2ef3-4637-99f5-8de26b2e8216",
            'grant_type': "password_mfa",
            'password': ParkSettings.get_value(key='UKLON_PASSWORD', partner=self.partner_id),
        }
        return payload

    def uklon_id(self):
        if not redis_instance().exists(f"{self.partner_id}_park_id"):
            response = self.response_data(url=f"{Service.get_value('UKLON_SESSION')}me")
            redis_instance().set(f"{self.partner_id}_park_id", response['fleets'][0]['id'])
        return redis_instance().get(f"{self.partner_id}_park_id")

    def create_session(self):
        response = requests.post(f"{Service.get_value('UKLON_SESSION')}auth", json=self.park_payload()).json()
        self.redis.set(f"{self.partner_id}token", response["access_token"])

    @staticmethod
    def request_method(url: str = None,
                       headers: dict = None,
                       params: dict = None,
                       data: dict = None,
                       pjson: dict = None,
                       method: str = None):
        if method == "POST":
            response = requests.post(url=url, headers=headers, data=data, json=pjson, params=params)
        elif method == "PUT":
            response = requests.put(url=url, headers=headers, data=data, json=pjson, params=params)
        elif method == "DELETE":
            response = requests.delete(url=url, headers=headers, data=data, json=pjson, params=params)
        else:
            response = requests.get(url=url, headers=headers, data=data, json=pjson, params=params)
        return response

    def response_data(self, url: str = None,
                      params: dict = None,
                      data=None,
                      headers: dict = None,
                      pjson: dict = None,
                      method: str = None) -> dict:

        if not self.redis.exists(f"{self.partner_id}token"):
            self.create_session()
        while True:
            response = self.request_method(url=url,
                                           params=params,
                                           headers=self.get_header() if headers is None else headers,
                                           pjson=pjson,
                                           data=data,
                                           method=method)
            if response.status_code in (401, 403):
                self.create_session()
            else:
                break
        return response.json()

    @staticmethod
    def to_float(number: int, div=100) -> float:
        return float("{:.2f}".format(number / div))

    def find_value(self, data: dict, *args) -> float:
        """Search value if args not False and return float"""
        nested_data = data
        for key in args:
            if key in nested_data:
                nested_data = nested_data[key]
            else:
                return float(0)

        return self.to_float(nested_data)

    @staticmethod
    def find_value_str(data: dict, *args) -> str:
        """Search value if args not False and return str"""
        nested_data = data

        for key in args:
            if key in nested_data:
                nested_data = nested_data[key]
            else:
                return ''

        return nested_data

    def download_report(self, day):
        report = Payments.objects.filter(report_from=self.start_report_interval(day),
                                         vendor_name=self.fleet,
                                         partner=self.partner_id)
        return list(report)

    def save_report(self, day):
        if self.download_report(day):
            return self.download_report(day)
        param = self.parameters()
        param['dateFrom'] = int(self.start_report_interval(day).timestamp())
        param['dateTo'] = int(self.end_report_interval(day).timestamp())
        url = f"{Service.get_value('UKLON_3')}{self.uklon_id()}"
        url += Service.get_value('UKLON_4')
        data = self.response_data(url=url, params=param)['items']
        if data:
            for i in data:
                order = Payments(
                    report_from=self.start_report_interval(day).date(),
                    vendor_name=self.fleet,
                    full_name=f"{i['driver']['first_name'].split()} {i['driver']['last_name'].split()}",
                    driver_id=str(i['driver']['id']),
                    total_rides=0 if 'total_orders_count' not in i else i['total_orders_count'],
                    total_distance=float(
                        0) if 'total_distance_meters' not in i else self.to_float(i['total_distance_meters'], div=1000),
                    total_amount_cash=self.find_value(i, *('profit', 'order', 'cash', 'amount')),
                    total_amount_on_card=self.find_value(i, *('profit', 'order', 'wallet', 'amount')),
                    total_amount=self.find_value(i, *('profit', 'order', 'total', 'amount')),
                    tips=self.find_value(i, *('profit', 'tips', 'amount')),
                    bonuses=float(0),
                    fares=float(0),
                    fee=self.find_value(i, *('loss', 'order', 'wallet', 'amount')),
                    total_amount_without_fee=self.find_value(i, *('profit', 'total', 'amount')),
                    partner=Partner.get_partner(self.partner_id),
                )
                try:
                    order.save()
                except IntegrityError:
                    pass
        else:
            order = Payments(
                report_from=self.start_report_interval(day).date(),
                vendor_name=self.fleet,
                full_name='',
                driver_id='',
                total_rides=0,
                total_distance=0,
                total_amount_cash=0,
                total_amount_on_card=0,
                total_amount=0,
                tips=0,
                bonuses=0,
                fares=0,
                fee=0,
                total_amount_without_fee=0,
                partner=Partner.get_partner(self.partner_id))
            try:
                order.save()
            except IntegrityError:
                pass

        return self.download_report(day)

    def get_drivers_status(self):
        first_key, second_key = 'with_client', 'wait'
        drivers = {
                first_key: [],
                second_key: [],
            }
        url = f"{Service.get_value('UKLON_5')}{self.uklon_id()}"
        url += Service.get_value('UKLON_6')
        data = self.response_data(url, params=self.parameters())

        for driver in data['drivers']:
            first_data = (driver['last_name'], driver['first_name'])
            second_data = (driver['first_name'], driver['last_name'])
            if driver['status'] == 'Active':
                drivers[f'{second_key}'].append(first_data)
                drivers[f'{second_key}'].append(second_data)
            elif driver['status'] == 'OrderExecution':
                drivers[f'{first_key}'].append(first_data)
                drivers[f'{first_key}'].append(second_data)
        return drivers

    def get_drivers_table(self):
        drivers = []
        param = self.parameters()
        param['name'], param['phone'], param['status'], param['limit'] = ('', '', 'All', '30')
        url = f"{Service.get_value('UKLON_1')}{self.uklon_id()}"
        url_1 = url + Service.get_value('UKLON_6')
        url_2 = url + Service.get_value('UKLON_2')

        all_drivers = self.response_data(url=url_1, params=param)

        for driver in all_drivers['items']:
            pay_cash, vehicle_name, vin_code = True, '', ''
            if driver['restrictions']:
                pay_cash = False if 'Cash' in driver['restrictions'][0]['restriction_types'] else True
            elif self.find_value_str(driver, *('selected_vehicle',)):
                vehicle_name = f"{driver['selected_vehicle']['make']} {driver['selected_vehicle']['model']}"
                vin_code = self.response_data(f"{url_2}/{driver['selected_vehicle']['vehicle_id']}")
                vin_code = vin_code.get('vin_code', '')

            email = self.response_data(url=f"{url_1}/{driver['id']}")

            drivers.append({
                'fleet_name': self.fleet,
                'name': driver['first_name'],
                'second_name': driver['last_name'],
                'email': email.get('email'),
                'phone_number': f"+{driver['phone']}",
                'driver_external_id': driver['id'],
                'pay_cash': pay_cash,
                'licence_plate': self.find_value_str(driver, *('selected_vehicle', 'license_plate')),
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
                'worked': True,
            })

        return drivers

    def get_fleet_orders(self, day, pk):
        states = {"completed": FleetOrder.COMPLETED,
                  "Rider": FleetOrder.CLIENT_CANCEL,
                  "Driver": FleetOrder.DRIVER_CANCEL,
                  "System": FleetOrder.SYSTEM_CANCEL,
                  "Dispatcher": FleetOrder.SYSTEM_CANCEL
                  }

        driver = Driver.objects.get(pk=pk)
        driver_id = driver.get_driver_external_id(self.fleet)
        if driver_id:
            str_driver_id = driver_id.replace("-", "")
            params = {"limit": 50,
                      "fleetId": self.uklon_id(),
                      "driverId": driver_id,
                      "from": int(self.start_report_interval(day).timestamp()),
                      "to": int(self.end_report_interval(day).timestamp())
                      }
            orders = self.response_data(url=f"{Service.get_value('UKLON_1')}orders", params=params)
            for order in orders['items']:
                if FleetOrder.objects.filter(order_id=order['id']):
                    continue
                detail = self.response_data(url=f"{Service.get_value('UKLON_1')}orders/{order['id']}",
                                            params={"driverId": str_driver_id})
                try:
                    finish_time = timezone.make_aware(datetime.fromtimestamp(detail["completedAt"]))
                except KeyError:
                    finish_time = None
                try:
                    start_time = timezone.make_aware(datetime.fromtimestamp(detail["createdAt"]))
                except KeyError:
                    start_time = None
                if order['status'] != "completed":
                    state = order["cancellation"]["initiator"]
                else:
                    state = order['status']

                data = {"order_id": order['id'],
                        "fleet": self.fleet,
                        "driver": driver,
                        "from_address": order['route']['points'][0]["address"],
                        "accepted_time": start_time,
                        "state": states.get(state),
                        "finish_time": finish_time,
                        "destination": order['route']['points'][-1]["address"],
                        "partner": Partner.get_partner(self.partner_id)
                        }
                FleetOrder.objects.create(**data)

    def disable_cash(self, pk, enable):
        url = f"{Service.get_value('UKLON_1')}{self.uklon_id()}"
        driver_id = Driver.objects.get(pk=pk).get_driver_external_id(self.fleet)
        url += f'{Service.get_value("UKLON_6")}/{driver_id}/restrictions'
        headers = self.get_header()
        headers.update({"Content-Type": "application/json"})
        payload = {"type": "Cash"}
        if enable == 'true':
            self.response_data(url=url,
                               headers=headers,
                               data=json.dumps(payload),
                               method='DELETE')
        else:
            self.response_data(url=url,
                               headers=headers,
                               data=json.dumps(payload),
                               method='PUT')
        pay_cash = True if enable == 'true' else False
        Fleets_drivers_vehicles_rate.objects.filter(driver_external_id=driver_id).update(pay_cash=pay_cash)

    def withdraw_money(self):
        base_url = f"{Service.get_value('UKLON_1')}{self.uklon_id()}"
        url = base_url + f"{Service.get_value('UKLON_7')}"
        balance = {}
        items = []
        headers = self.get_header()
        headers.update({"Content-Type": "application/json"})
        resp = self.response_data(url, headers=headers)
        for driver in resp['items']:
            balance[driver['driver_id']] = driver['wallet']['balance']['amount'] -\
                                           int(ParkSettings.get_value('WITHDRAW_UKLON',
                                                                      partner=self.partner_id)) * 100
        for key, value in balance.items():
            if value > 0:
                transfer = str(uuid.uuid4())
                items.append({
                    "transfer_id": f"{transfer}",
                    "driver_id": key,
                    "amount": {
                        "amount": value,
                        "currency": "UAH"
                    }})
        if items:
            url2 = base_url + f"{Service.get_value('UKLON_8')}"
            payload = {
                "items": items
            }
            self.response_data(url=url2, headers=headers, data=json.dumps(payload), method='POST')

    def detaching_the_driver_from_the_car(self, licence_plate):
        base_url = f"{Service.get_value('UKLON_1')}{self.uklon_id()}"
        url = base_url + Service.get_value('UKLON_2')
        params = {
            'limit': '30',
        }
        vehicles = self.response_data(url=url, params=params)
        matching_object = next((item for item in vehicles["data"] if item["licencePlate"] == licence_plate), None)
        if matching_object:
            id_vehicle = matching_object["id"]
            url += f"/{id_vehicle}/release"
            self.response_data(url=url, method='POST')

    def get_vehicles(self):
        vehicles = []

        param = self.parameters()
        param.update({"limit": 30})
        url = f"{Service.get_value('UKLON_1')}{self.uklon_id()}"
        url += Service.get_value('UKLON_2')
        all_vehicles = self.response_data(url=url, params=param)
        for vehicle in all_vehicles['data']:
            response = self.response_data(url=f"{url}/{vehicle['id']}")

            vehicles.append({
                'licence_plate': vehicle['licencePlate'],
                'vehicle_name': f"{vehicle['about']['maker']['name']} {vehicle['about']['model']['name']}",
                'vin_code': response.get('vin_code', '')
            })

        return vehicles
