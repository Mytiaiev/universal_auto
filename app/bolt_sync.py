import datetime
import mimetypes
import time
from urllib import parse

import pendulum
import requests
from django.db import IntegrityError
from django.utils import timezone

from django.db import models
from app.models import BoltService, Driver, Fleets_drivers_vehicles_rate, Payments, Partner, FleetOrder, \
    CredentialPartner, Vehicle, PaymentTypes, Fleet
from auto import settings
from auto_bot.handlers.order.utils import check_vehicle
from scripts.redis_conn import redis_instance
from selenium_ninja.synchronizer import Synchronizer, AuthenticationError


class BoltRequest(Fleet, Synchronizer):
    base_url = models.URLField(default=BoltService.get_value('REQUEST_BOLT_LOGIN_URL'))

    def create_session(self, partner=None, login=None, password=None):
        partner_id = partner if partner else self.partner.id
        if self.partner:
            login = CredentialPartner.get_value("BOLT_NAME", partner=partner_id)
            password = CredentialPartner.get_value("BOLT_PASSWORD", partner=partner_id)
        payload = {
            'username': login,
            'password': password,
            'device_name': "Chrome",
            'device_os_version': "NT 10.0",
            "device_uid": "6439b6c1-37c2-4736-b898-cb2a8608e6e2"
        }
        response = requests.post(url=f'{self.base_url}startAuthentication',
                                 params=self.param(),
                                 json=payload)
        if response.json()["code"] == 66610:
            raise AuthenticationError(f"{self.name} login or password incorrect.")
        else:
            refresh_token = response.json()["data"]["refresh_token"]
            redis_instance().set(f"{partner_id}_{self.name}_refresh", refresh_token)

    @staticmethod
    def param():
        return {"language": "uk-ua", "version": "FO.3.03"}

    def get_access_token(self):
        token = redis_instance().get(f"{self.partner.id}_{self.name}_refresh")
        park_id = redis_instance().get(f"{self.partner.id}_{self.name}_park_id")
        if token and park_id:
            access_payload = {
                "refresh_token": token,
                "company": {"company_id": park_id,
                            "company_type": "fleet_company"}
            }
            response = requests.post(url=f'{self.base_url}getAccessToken',
                                     params=self.param(),
                                     json=access_payload)
            if not response.json()['code']:
                return response.json()["data"]["access_token"]
        elif token:
            access_payload = {
                "refresh_token": token
            }
            response = requests.post(url=f'{self.base_url}getAccessToken',
                                     params=self.param(),
                                     json=access_payload)
            if not response.json()['code']:
                first_token = response.json()["data"]["access_token"]
                headers = {'Authorization': f'Bearer {first_token}'}
                response = requests.get(url=f'{self.base_url}getProfile',
                                        params=self.param(),
                                        headers=headers)
                if not response.json()['code']:
                    park_id = response.json()["data"]["companies"][0]["id"]
                    redis_instance().set(f"{self.partner.id}_{self.name}_park_id", park_id)
                    self.get_access_token()
        else:
            self.create_session()
            self.get_access_token()

    def get_target_url(self, url, params):
        new_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {new_token}'}
        response = requests.get(url, params=params, headers=headers)
        return response.json()

    def post_target_url(self, url, params, json):
        new_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {new_token}'}
        response = requests.post(url, json=json, params=params, headers=headers)
        return response.json()

    def save_report(self, day):
        reports = Payments.objects.filter(report_from=day, vendor_name=self.name, partner=self.partner.id)
        if reports:
            return list(reports)
        # date format str yyyy-mm-dd
        format_day = day.strftime("%Y-%m-%d")
        param = self.param()
        param.update({"start_date": format_day,
                      "end_date": format_day,
                      "offset": 0,
                      "limit": 50})
        reports = self.get_target_url(f'{self.base_url}getDriverEarnings/dateRange', param)
        param['limit'] = 25
        rides = self.get_target_url(f'{self.base_url}getDriverEngagementData/dateRange', param)
        for driver in reports['data']['drivers']:
            db_driver = Fleets_drivers_vehicles_rate.objects.get(driver_external_id=driver['id'],
                                                                 partner=self.partner.id).driver
            vehicle = check_vehicle(db_driver, day, max_time=True)[0]
            order = Payments(
                report_from=day,
                vendor_name=self.name,
                full_name=driver['name'],
                driver_id=driver['id'],
                total_amount_cash=driver['cash_in_hand'],
                total_amount=driver['gross_revenue'],
                tips=driver['tips'],
                partner=self.partner,
                bonuses=driver['bonuses'],
                cancels=driver['cancellation_fees'],
                fee=-(driver['gross_revenue'] - driver['net_earnings']),
                total_amount_without_fee=driver['net_earnings'],
                compensations=driver['compensations'],
                refunds=driver['expense_refunds'],
                vehicle=vehicle
            )
            for rider in rides['data']['rows']:
                if driver['id'] == rider['id']:
                    order.total_rides = rider['finished_orders']
            try:
                order.save()
            except IntegrityError:
                pass

    def get_drivers_table(self):
        driver_list = []
        start = end = pendulum.now().strftime('%Y-%m-%d')
        params = {"start_date": start,
                  "end_date": end,
                  "offset": 0,
                  "limit": 25}
        params.update(self.param())
        report = self.get_target_url(f'{self.base_url}getDriverEngagementData/dateRange', params)
        drivers = report['data']['rows']
        for driver in drivers:
            driver_params = self.param().copy()
            driver_params['id'] = driver['id']
            driver_info = self.get_target_url(f'{self.base_url}getDriver', driver_params)
            if driver_info['message'] == 'OK':
                driver_list.append({
                    'fleet_name': self.name,
                    'name': driver_info['data']['first_name'],
                    'second_name': driver_info['data']['last_name'],
                    'email': driver_info['data']['email'],
                    'phone_number': driver_info['data']['phone'],
                    'driver_external_id': driver_info['data']['id'],
                    'pay_cash': driver_info['data']['has_cash_payment'],
                    'licence_plate': '',
                    'vehicle_name': '',
                    'vin_code': '',
                    'worked': True,
                })
            time.sleep(0.5)
        return driver_list

    def get_fleet_orders(self, day, pk):
        bolt_states = {
            "client_did_not_show": FleetOrder.CLIENT_CANCEL,
            "finished": FleetOrder.COMPLETED,
            "client_cancelled": FleetOrder.CLIENT_CANCEL,
            "driver_cancelled_after_accept": FleetOrder.DRIVER_CANCEL,
            "driver_rejected": FleetOrder.DRIVER_CANCEL
        }
        driver = Driver.objects.get(pk=pk)
        driver_id = driver.get_driver_external_id(self.name)
        if driver_id:
            format_day = day.strftime("%Y-%m-%d")
            payload = {
                      "offset": 0,
                      "limit": 50,
                      "from_date": format_day,
                      "to_date": format_day,
                      "driver_id": driver_id,
                      "orders_state_statuses": [
                                                "client_did_not_show",
                                                "finished",
                                                "client_cancelled",
                                                "driver_cancelled_after_accept",
                                                "driver_rejected"
                                                ]
                    }
            report = self.post_target_url(f'{self.base_url}getOrdersHistory', self.param(), payload)
            time.sleep(0.5)
            if report.get('data'):
                for order in report['data']['rows']:
                    if FleetOrder.objects.filter(order_id=order['order_id']):
                        continue
                    try:
                        finish = timezone.make_aware(
                            datetime.datetime.fromtimestamp(order['order_stops'][-1]['arrived_at']))
                    except TypeError:
                        finish = None
                    try:
                        price = order['total_price']
                    except KeyError:
                        price = 0
                    vehicle = Vehicle.objects.get(licence_plate=order['car_reg_number'])
                    data = {"order_id": order['order_id'],
                            "fleet": self.name,
                            "driver": driver,
                            "from_address": order['pickup_address'],
                            "accepted_time": timezone.make_aware(
                                datetime.datetime.fromtimestamp(order['accepted_time'])),
                            "state": bolt_states.get(order['order_try_state']),
                            "finish_time": finish,
                            "payment": PaymentTypes.map_payments(order['payment_method']),
                            "destination": order['order_stops'][-1]['address'],
                            "vehicle": vehicle,
                            "price": price,
                            "partner": self.partner
                            }
                    if check_vehicle(driver)[0] != vehicle:
                        redis_instance().hset(f"wrong_vehicle_{self.partner.id}", pk, order['car_reg_number'])
                    FleetOrder.objects.create(**data)

    def get_drivers_status(self):
        with_client = []
        wait = []
        report = self.get_target_url(f'{self.base_url}getDriversForLiveMap', self.param())
        if report.get('data'):
            for driver in report['data']['list']:
                name, second_name = driver['name'].split(' ')
                if driver['state'] == 'waiting_orders':
                    wait.append((name, second_name))
                    wait.append((second_name, name))
                else:
                    with_client.append((name, second_name))
                    with_client.append((second_name, name))
        return {'wait': wait,
                'with_client': with_client}

    def disable_cash(self, driver_id, enable):
        payload = {
            "driver_id": driver_id,
            "has_cash_payment": enable
        }
        self.post_target_url(f'{self.base_url}driver/toggleCash', self.param(), payload)
        pay_cash = True if enable == 'true' else False
        Fleets_drivers_vehicles_rate.objects.filter(driver_external_id=driver_id).update(pay_cash=pay_cash)

    def add_driver(self, job_application):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
                        "email": f"{job_application.email}",
                        "phone": f"{job_application.phone_number}",
                        "referral_code": ""
                }
        response = self.post_target_url(f'{self.base_url}addDriverRegistration', self.param(), payload)
        payload_form = {
            'hash': response['data']['hash'],
            'last_step': 'step_2',
            'first_name': job_application.first_name,
            'last_name': job_application.last_name,
            'email': job_application.email,
            'phone': job_application.phone_number,
            'birthday': '',
            'terms_consent_accepted': '0',
            'whatsapp_opt_in': '0',
            'city_data': 'Kyiv|ua|uk|634|₴|158',
            'city_id': '158',
            'language': 'uk',
            'referral_code': '',
            'has_car': '0',
            'allow_fleet_matching': '',
            'personal_code': '',
            'driver_license': '',
            'has_taxi_license': '0',
            'type': 'person',
            'license_type_selection': '',
            'company_name': '',
            'address': '',
            'reg_code': '',
            'company_is_liable_to_vat': '0',
            'vat_code': '',
            'beneficiary_name': '',
            'iban': '',
            'swift': '',
            'account_branch_code': '',
            'remote_training_url': '',
            'flow_id': '',
            'web_marketing_data[fbp]': '',
            'web_marketing_data[url]': f"{response['data']['registration_link']}/2",
            'web_marketing_data[user_agent]': '''Mozilla/5.0 (Windows NT 10.0; Win64; x64)
             AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36''',
            'is_fleet_company': '1'
        }

        encoded_payload = parse.urlencode(payload_form)
        params = {
            'version': 'DP.11.89',
            'hash': response['data']['hash'],
            'language': 'uk-ua',
        }
        second_params = dict(list(params.items())[:1])
        requests.post(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}register/',
                      params=second_params, headers=headers, data=encoded_payload)
        requests.get(f"{BoltService.get_value('R_BOLT_ADD_DRIVER_1')}getDriverRegistrationDocumentsSet/", params=params)

        file_paths = [
            f"{settings.MEDIA_URL}{job_application.driver_license_front}",  # license_front
            f"{settings.MEDIA_URL}{job_application.photo}",  # photo
            f"{settings.MEDIA_URL}{job_application.car_documents}",  # car_document
            f"{settings.MEDIA_URL}{job_application.insurance}"  # insurance
        ]

        payloads = [
            {'hash': response['data']['hash'], 'expires': str(job_application.license_expired)},
            {'hash': response['data']['hash']},
            {'hash': response['data']['hash']},
            {'hash': response['data']['hash'], 'expires': str(job_application.insurance_expired)}
        ]

        file_keys = [
            'ua_drivers_license',
            'ua_profile_pic',
            'ua_technical_passport',
            'ua_insurance_policy'
        ]

        for file_path, key, payload in zip(file_paths, file_keys, payloads):
            files = {}
            binary = requests.get(file_path).content
            mime_type, _ = mimetypes.guess_type(file_path)
            file_name = file_path.split('/')[-1]
            files[key] = (file_name, binary, mime_type)
            requests.post(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}uploadDriverRegistrationDocument/',
                          params=params, data=payload, files=files)
        payload_form['last_step'] = 'step_4'
        payload_form['web_marketing_data[url]'] = f"{response['data']['registration_link']}/4"
        encoded = parse.urlencode(payload_form)
        requests.post(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}register/', headers=headers,
                      params=params, data=encoded)
        job_application.status_bolt = datetime.datetime.now().date()
        job_application.save()

    def get_vehicles(self):
        vehicles_list = []
        start = end = pendulum.now().strftime('%Y-%m-%d')
        params = {"start_date": start,
                  "end_date": end,
                  "offset": 0,
                  "limit": 25}
        params.update(self.param())
        response = self.get_target_url(f'{self.base_url}getCarsPaginated', params=params)
        vehicles = response['data']['rows']
        for vehicle in vehicles:
            vehicles_list.append({
                'licence_plate': vehicle['reg_number'],
                'vehicle_name': vehicle['model'],
                'vin_code': ''
            })
        return vehicles_list
