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
from app.models import ParkSettings, BoltService, Driver, Fleets_drivers_vehicles_rate, Payments
from auto import settings
from selenium_ninja.driver import SeleniumTools, clickandclear
from selenium_ninja.synchronizer import Synchronizer, RequestSynchronizer


class BoltRequest(RequestSynchronizer):
    def __init__(self, fleet='Bolt', base_url=BoltService.get_value('REQUEST_BOLT_LOGIN_URL')):
        self.params = {"language": "uk-ua",
                       "version": "FO.2.61"}
        super().__init__(fleet=fleet, base_url=base_url)

    def get_login_token(self):
        payload = {
            'username': ParkSettings.get_value("BOLT_NAME"),
            'password': ParkSettings.get_value("BOLT_PASSWORD"),
            'device_name': "Chrome",
            'device_os_version': "NT 10.0",
            "device_uid": "6439b6c1-37c2-4736-b898-cb2a8608e6e2"
        }
        response = requests.post(url=f'{self.base_url}startAuthentication', params=self.params, json=payload)
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
            response = requests.post(url=f'{self.base_url}getAccessToken',
                                     params=self.params, json=access_payload)
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
                response = requests.post(url=f'{self.base_url}getAccessToken',
                                         params=self.params, json=new_payload)
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

    @staticmethod
    def start_report_interval(start_date):
        date = pendulum.from_format(start_date, "YYYY-MM-DD")
        return date.in_timezone("Europe/Kiev").start_of("day")

    @staticmethod
    def end_report_interval(end_date):
        date = pendulum.from_format(end_date, "YYYY-MM-DD")
        return date.in_timezone("Europe/Kiev").end_of("day")

    def download_report(self, start, end):
        report = Payments.objects.filter(report_from=self.start_report_interval(start),
                                         report_to=self.end_report_interval(end),
                                         vendor_name=self.fleet)
        return list(report)

    def save_report(self, start, end):
        if self.download_report(start, end):
            return self.download_report(start, end)
        # date format str yyyy-mm-dd
        self.params.update({"start_date": start,
                            "end_date": end,
                            "offset": 0,
                            "limit": 50})
        report = self.get_target_url(f'{self.base_url}getDriverEarnings/dateRange', self.params)
        for driver in report['data']['drivers']:
            order = Payments(
                report_from=self.start_report_interval(start),
                report_to=self.end_report_interval(end),
                vendor_name=self.fleet,
                full_name=driver['name'],
                driver_id=driver['id'],
                total_amount_cash=driver['cash_in_hand'],
                total_amount=driver['gross_revenue'],
                tips=driver['tips'],
                bonuses=driver['bonuses'],
                cancels=driver['cancellation_fees'],
                fee=driver['gross_revenue'] - driver['net_earnings'],
                total_amount_without_fee=driver['net_earnings'],
                compensations=driver['compensations'],
                refunds=driver['expense_refunds'],
)
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
        params.update(self.params)
        report = self.get_target_url(f'{self.base_url}getDriverEngagementData/dateRange', params)
        drivers = report['data']['rows']
        for driver in drivers:
            driver_params = self.params.copy()
            driver_params['id'] = driver['id']
            driver_info = self.get_target_url(f'{self.base_url}getDriver', driver_params)
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
            time.sleep(0.5)
        return driver_list

    def get_drivers_status(self):
        with_client = []
        wait = []
        report = self.get_target_url(f'{self.base_url}getDriversForLiveMap', self.params)
        drivers = report['data']['list']
        if drivers:
            for driver in drivers:
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
        self.post_target_url(f'{self.base_url}driver/toggleCash', self.params, payload)
        pay_cash = True if enable == 'true' else False
        Fleets_drivers_vehicles_rate.objects.filter(driver_external_id=driver).update(pay_cash=pay_cash)

    def add_driver(self, job_application):
        payload = {
                        "email": f"{job_application.email}",
                        "phone": f"{job_application.phone_number}",
                        "referral_code": ""
                }
        response = self.post_target_url(f'{self.base_url}addDriverRegistration', self.params, payload)
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


class BoltSynchronizer(Synchronizer, SeleniumTools):

    def login(self):
        self.driver.get(f"{BoltService.get_value('BOLT_LOGIN_URL')}")
        if self.sleep:
            time.sleep(self.sleep)
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_1'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_NAME"))
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_2'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_PASSWORD"))
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_LOGIN_3')).click()

    def download_payments_order(self, day=None, interval=None):
        url = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_URL')
        xpath = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_1')
        self.get_target_element_of_page(url, xpath)
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, BoltService.get_value('BOLT_GET_DRIVER_STATUS_FROM_MAP_1')))).click()
        except:
            pass
        if day:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_2')))).click()
            xpath = f"{BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_3')}[{interval}]"
            date = self.driver.find_element(By.XPATH, xpath)
            if date.text != 'нд':
                date.click()
            else:
                self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_7')).click()
                xpath = f"{BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_3')}[{interval}]"
                self.driver.find_element(By.XPATH, xpath).click()
            self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_4')).click()
        else:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_1')))).click()
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_5')))).click()
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_6')).click()
        if self.sleep:
            time.sleep(self.sleep)
        if self.remote:
            self.get_last_downloaded_file_frome_remote(save_as=self.file_pattern(self.fleet, self.partner, day=day))
        else:
            self.get_last_downloaded_file(save_as=self.file_pattern(self.fleet, self.partner, day=day))

    def save_report(self, day=None):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        self.logger.info(self.file_pattern(self.fleet, self.partner, day=day))

        if self.payments_order_file_name(self.fleet, self.partner, day=day) is not None:
            with open(self.payments_order_file_name(self.fleet, self.partner, day=day), encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    if row[0] == "":
                        break
                    if row[0] is None:
                        break
                    if row[1] == "":
                        continue
                    order = Payments(
                        report_from=self.start_report_interval(day=day),
                        report_to=self.end_report_interval(day=day),
                        report_file_name=file.name,
                        driver_full_name=row[0][:24],
                        mobile_number='',
                        range_string='',
                        total_amount=float(row[1].replace(',', '.')),
                        cancels_amount=float(row[9].replace(',', '.')),
                        autorization_payment=0,
                        autorization_deduction=0,
                        additional_fee=0,
                        fee=float(row[1].replace(',', '.')) - float(row[4].replace(',', '.')),
                        total_amount_cach=float(row[5].replace(',', '.')),
                        discount_cash_trips=0,
                        driver_bonus=float(row[7].replace(',', '.')),
                        compensation=float(str(row[8] or 0).replace(',', '.')),
                        refunds=float(row[14].replace(',', '.')),
                        tips=float(row[6].replace(',', '.')),
                        weekly_balance=0)
                    try:
                        order.save()
                    except IntegrityError:
                        pass
                    items.append(order)
        else:
            order = Payments(
                report_from=self.start_report_interval(day=day),
                report_to=self.end_report_interval(day=day),
                report_file_name='',
                driver_full_name='',
                mobile_number='',
                range_string='',
                total_amount=0,
                cancels_amount=0,
                autorization_payment=0,
                autorization_deduction=0,
                additional_fee=0,
                fee=0,
                total_amount_cach=0,
                discount_cash_trips=0,
                driver_bonus=0,
                compensation=0,
                refunds=0,
                tips=0,
                weekly_balance=0)
            try:
                order.save()
            except IntegrityError:
                pass

        return items

    def get_drivers_table(self):
        drivers = []
        url = BoltService.get_value('BOLT_DRIVERS_URL')
        xpath = BoltService.get_value('BOLT_GET_DRIVERS_TABLE_1')
        self.get_target_element_of_page(url, xpath)
        # self.driver.get_screenshot_as_file('BoltSynchronizer.png')
        i_table = 0
        while True:
            i_table += 1
            try:
                xpath = f'{BoltService.get_value("BOLT_GET_DRIVERS_TABLE_2")}[{i_table}]'
                driver_row = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                name = driver_row.find_element(By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_3"))
                full_name = name.text
                name.click()
                email = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_4")))).text
                phone_number = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_5")))).text
                elements = self.driver.find_elements(By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_6"))
                pay_cash = (len(elements) == 2)
                self.driver.back()
                s_name = self.split_name(full_name)
                drivers.append({
                    'fleet_name': self.fleet,
                    'name': s_name[0],
                    'second_name': s_name[1],
                    'email': self.validate_email(email),
                    'phone_number': self.validate_phone_number(phone_number),
                    'driver_external_id': full_name,
                    'pay_cash': pay_cash,
                    'licence_plate': '',
                    'vehicle_name': '',
                    'vin_code': '',

                })
            except TimeoutException:
                break
        return drivers

    def get_driver_status_from_map(self, search_text):
        raw_data = []
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located(
                    (By.XPATH, BoltService.get_value("BOLT_GET_DRIVER_STATUS_FROM_MAP_1")))).click()
        except:
            pass
        try:
            xpath = f'{BoltService.get_value("BOLT_GET_DRIVER_STATUS_FROM_MAP_2")}[{search_text}]/div'
            element_count = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            if element_count.text[-1] == '-':
                return raw_data
            element_count.click()
        except TimeoutException:
            return raw_data
        i = 0
        while i < int(element_count.text[-1]):
            i += 1
            try:
                el = BoltService.get_value("BOLT_GET_DRIVER_STATUS_FROM_MAP_3")
                xpath = f'{el}{i}{BoltService.get_value("BOLT_GET_DRIVER_STATUS_FROM_MAP_3.1")}'
                driver_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                break
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name = '', ''
            try:
                name, second_name = name_list[0], name_list[1]
            except IndexError:
                pass
            raw_data.append((name, second_name))
            raw_data.append((second_name, name))
        return raw_data

    def get_driver_status(self):
        try:
            url = BoltService.get_value('BOLT_MAP_URL')
            xpath = BoltService.get_value('BOLT_GET_DRIVER_STATUS_1')
            self.get_target_element_of_page(url, xpath)
            return {
                'width_client': self.get_driver_status_from_map('1'),
                'wait': self.get_driver_status_from_map('2')
            }
        except (TimeoutException, WebDriverException) as err:
            self.logger.error(err)

    def download_weekly_report(self, day=None, interval=None):
        try:
            report = Payments.objects.filter(report_from=self.start_report_interval(day),
                                             report_to=self.end_report_interval(day),
                                             vendor_name=self.fleet)
            if not report:
                self.download_payments_order(day=day, interval=interval)
                self.save_report(day=day)
                report = Payments.objects.filter(report_from=self.start_report_interval(day),
                                                 report_to=self.end_report_interval(day),
                                                 vendor_name=self.fleet)
            return list(report)
        except Exception as err:
            self.logger.error(err)

    def disable_cash(self, name, second_name, disable):
        url = BoltService.get_value('BOLT_DRIVERS_URL')
        xpath = BoltService.get_value('BOLT_GET_DRIVERS_TABLE_1')
        self.get_target_element_of_page(url, xpath)
        driver = self.get_driver_by_name(name=name, second_name=second_name)
        fleet = Fleet.objects.get(name=self.fleet)
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, BoltService.get_value('BOLT_GET_DRIVER_STATUS_FROM_MAP_1')))).click()
        except:
            pass
        try:
            xpath = f'{BoltService.get_value("BOLT_DISABLE_CASH_1")}{name} {second_name}")]'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        except TimeoutException:
            try:
                xpath = f'{BoltService.get_value("BOLT_DISABLE_CASH_1")}{second_name}")]'
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            except TimeoutException:
                self.logger.error(f"No driver {driver} in {fleet}")
        time.sleep(self.sleep)
        elements = self.driver.find_elements(By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_6"))
        if disable and len(elements) == 2:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLT_DISABLE_CASH_2")))).click()
            time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLT_DISABLE_CASH_3")))).click()
        if not disable and len(elements) != 2:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLT_DISABLE_CASH_2")))).click()
        new_elements = self.driver.find_elements(By.XPATH, BoltService.get_value("BOLT_GET_DRIVERS_TABLE_6"))
        if len(new_elements) == 2:
            pay_cash = True
        else:
            pay_cash = False
        Fleets_drivers_vehicles_rate.objects.filter(driver=driver, fleet=fleet).update(pay_cash=pay_cash)

    def add_driver(self, jobapplication):
        if not jobapplication.status_bolt:
            url = BoltService.get_value('BOLT_DRIVERS_URL')
            self.get_target_element_of_page(url, BoltService.get_value('BOLT_ADD_DRIVER_1'))
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_1')))).click()
            form_email = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_ADD_DRIVER_2'))))
            clickandclear(form_email)
            form_email.send_keys(jobapplication.email)
            form_phone_number = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_ADD_DRIVER_3'))))
            clickandclear(form_phone_number)
            form_phone_number.send_keys(jobapplication.phone_number[4:])
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_4')))).click()
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_5')))).click()
            new_window = self.driver.window_handles[1]
            self.driver.switch_to.window(new_window)
            form_first_name = self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_6'))
            clickandclear(form_first_name)
            form_first_name.send_keys(jobapplication.first_name)
            form_last_name = self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_7'))
            clickandclear(form_last_name)
            form_last_name.send_keys(jobapplication.last_name)
            self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_8')).click()
            if self.sleep:
                time.sleep(self.sleep)
            elements_to_select = [str(jobapplication.license_expired).split("-")[0],
                                  str(jobapplication.license_expired).split("-")[1],
                                  str(jobapplication.license_expired).split("-")[2],
                                  str(jobapplication.insurance_expired).split("-")[0],
                                  str(jobapplication.insurance_expired).split("-")[1],
                                  str(jobapplication.insurance_expired).split("-")[2]
                                  ]
            form_fields = self.driver.find_elements(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_9'))
            for i, select_elem in enumerate(elements_to_select):
                form_fields[i].click()
                self.driver.find_element(By.XPATH,
                                         f"{BoltService.get_value('BOLT_ADD_DRIVER_10')}'{select_elem}']").click()
            upload_elements = self.driver.find_elements(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_11'))
            file_paths = [
                f"{settings.MEDIA_URL}{jobapplication.driver_license_front}",  # license_front
                f"{settings.MEDIA_URL}{jobapplication.photo}",  # photo
                f"{settings.MEDIA_URL}{jobapplication.car_documents}",  # car_document
                f"{settings.MEDIA_URL}{jobapplication.insurance}",  # insurance
            ]
            for i, file_path in enumerate(file_paths):
                local_path = self.download_from_bucket(file_path, i)
                upload_element = upload_elements[i]
                upload_element.click()
                upload_input = upload_element.find_element(By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_12'))
                # Execute JavaScript code to remove the display property from the element's style
                self.driver.execute_script("arguments[0].style.removeProperty('display');", upload_input)
                upload_input.send_keys(local_path)
            if self.sleep:
                time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_13')))).click()
            jobapplication.status_bolt = datetime.datetime.now().date()
            jobapplication.save()
