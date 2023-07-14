import csv
import datetime
import io
import mimetypes
import time
from urllib import parse

import pendulum
import requests
from django.db import IntegrityError
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models import ParkSettings, BoltService, BoltPaymentsOrder, Driver, Fleets_drivers_vehicles_rate
from auto import settings
from selenium_ninja.synchronizer import Synchronizer


class BoltRequest(Synchronizer):
    def base_url(self):
        return BoltService.get_value('REQUEST_BOLT_LOGIN_URL')

    def parameters(self):
        param = {"language": "uk-ua",
                 "version": "FO.2.61"}
        return param

    def get_login_token(self):
        payload = {
            'username': ParkSettings.get_value("BOLT_NAME", park=self.id),
            'password': ParkSettings.get_value("BOLT_PASSWORD", park=self.id),
            'device_name': "Chrome",
            'device_os_version': "NT 10.0",
            "device_uid": "6439b6c1-37c2-4736-b898-cb2a8608e6e2"
        }
        response = requests.post(url=f'{self.base_url()}startAuthentication',
                                 params=self.parameters(),
                                 json=payload)
        self.redis.set(f"{self.fleet}_refresh", response.json()["data"]["refresh_token"])
        return response.json()

    def get_access_token(self):
        token = self.redis.get(f"{self.fleet}_refresh")
        if token:
            access_payload = {
                "refresh_token": token.decode(),
                "company": {"company_id": "58225",
                            "company_type": "fleet_company"}
            }
            response = requests.post(url=f'{self.base_url()}getAccessToken',
                                     params=self.parameters(),
                                     json=access_payload)
            if not response.json()['code']:
                self.redis.set(f"{self.fleet}_token", response.json()["data"]["access_token"])
            else:
                self.get_login_token()
                new_token = self.redis.get(f"{self.fleet}_refresh")
                new_payload = {
                    "refresh_token": new_token.decode(),
                    "company": {"company_id": "58225",
                                "company_type": "fleet_company"}
                }
                response = requests.post(url=f'{self.base_url()}getAccessToken',
                                         params=self.parameters(),
                                         json=new_payload)
                self.redis.set(f"{self.fleet}_token", response.json()["data"]["access_token"])
        else:
            self.get_login_token()
            self.get_access_token()

    def get_target_url(self, url, params):
        self.get_access_token()
        new_token = self.redis.get(f"{self.fleet}_token")
        headers = {'Authorization': f'Bearer {new_token.decode()}'}
        response = requests.get(url, params=params, headers=headers)
        return response.json()

    def post_target_url(self, url, params, json):
        self.get_access_token()
        new_token = self.redis.get(f"{self.fleet}_token")
        headers = {'Authorization': f'Bearer {new_token.decode()}'}
        response = requests.post(url, json=json, params=params, headers=headers)
        return response.json()

    def download_report(self, start, end):
        report = BoltPaymentsOrder.objects.filter(report_from=self.start_report_interval(start),
                                                  report_to=self.end_report_interval(end),
                                                  partner=self.get_partner())
        return list(report)

    def save_report(self, start, end):
        if self.download_report(start, end):
            return self.download_report(start, end)
        # date format str yyyy-mm-dd
        param = self.parameters()
        param.update({"start_date": start,
                                  "end_date": end,
                                  "offset": 0,
                                  "limit": 50})

        report = self.get_target_url(f'{self.base_url()}getDriverEarnings/dateRange', param)
        for driver in report['data']['drivers']:
            order = BoltPaymentsOrder(
                report_from=self.start_report_interval(start),
                report_to=self.end_report_interval(end),
                driver_full_name=driver['name'],
                mobile_number=driver['id'],
                range_string='',
                total_amount=driver['gross_revenue'],
                cancels_amount=driver['cancellation_fees'],
                autorization_payment=0,
                autorization_deduction=0,
                additional_fee=0,
                fee=float(driver['gross_revenue']) - float(driver['net_earnings']),
                total_amount_cach=driver['cash_in_hand'],
                discount_cash_trips=0,
                driver_bonus=driver['bonuses'],
                compensation=driver['compensations'],
                refunds=driver['expense_refunds'],
                tips=driver['tips'],
                weekly_balance=0,
                partner=self.get_partner())
            try:
                order.save()
            except IntegrityError:
                pass
        return self.download_report(start, end)

    def get_drivers_table(self):
        driver_list = []
        start = end = pendulum.now().strftime('%Y-%m-%d')
        params = {"start_date": start,
                  "end_date": end,
                  "offset": 0,
                  "limit": 25}
        params.update(self.parameters())
        report = self.get_target_url(f'{self.base_url()}getDriverEngagementData/dateRange', params)
        drivers = report['data']['rows']
        for driver in drivers:
            driver_params = self.parameters().copy()
            driver_params['id'] = driver['id']
            driver_info = self.get_target_url(f'{self.base_url()}getDriver', driver_params)
            driver_list.append({
                'fleet_name': self.fleet,
                'name': driver_info['data']['first_name'],
                'second_name': driver_info['data']['last_name'],
                'email': driver_info['data']['email'],
                'phone_number': driver_info['data']['phone'],
                'driver_external_id': driver_info['data']['id'],
                'pay_cash': driver_info['data']['has_cash_payment'],
                'licence_plate': '',
                'vehicle_name': '',
                'vin_code': '',

            })
            time.sleep(1)
        return driver_list

    def get_drivers_status(self):
        with_client = []
        wait = []
        report = self.get_target_url(f'{self.base_url()}getDriversForLiveMap', self.parameters())
        if report['data']:
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

    def cash_restriction(self, pk, enable):
        driver = Driver.objects.get(pk=pk)
        driver_id = driver.get_driver_external_id(self.fleet)
        payload = {
            "driver_id": driver_id,
            "has_cash_payment": enable
        }
        self.post_target_url(f'{self.base_url()}driver/toggleCash', self.parameters(), payload)
        pay_cash = True if enable == 'true' else False
        Fleets_drivers_vehicles_rate.objects.filter(driver_external_id=driver).update(pay_cash=pay_cash)

    def add_driver(self, job_application):
        payload = {
                        "email": f"{job_application.email}",
                        "phone": f"{job_application.phone_number}",
                        "referral_code": ""
                }
        response = self.post_target_url(f'{self.base_url()}addDriverRegistration', self.parameters(), payload)
        payload_form = {
            'hash': response['data']['hash'],
            'last_step': 'step_2',
            'first_name': f"{job_application.first_name}",
            'last_name': f"{job_application.last_name}",
            'email': f"{job_application.email}",
            'phone': f"{job_application.phone_number}",
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
            'web_marketing_data[user_agent]': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'is_fleet_company': '1'
        }

        encoded_payload = parse.urlencode(payload_form)
        params = {
            'version': 'DP.11.89',
            'hash': response['data']['hash'],
            'language': 'uk-ua',
        }
        first_params = dict(list(params.items())[:2])
        second_params = dict(list(params.items())[0])
        requests.get(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}getDriverRegistrationLog/', params=first_params)
        requests.post(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}register/',
                      params=second_params, data=encoded_payload)
        requests.get(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}getDriverRegistrationDocumentsSet/', params)

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
        requests.post(f'{BoltService.get_value("R_BOLT_ADD_DRIVER_1")}register/', params=params, data=encoded)

