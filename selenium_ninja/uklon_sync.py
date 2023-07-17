import datetime
import time
import requests
import redis
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models import NewUklonService, ParkSettings, NewUklonFleet, \
    Fleets_drivers_vehicles_rate, Fleet, Driver, Payments, Service
from auto import settings
from scripts.redis_conn import redis_instance
from selenium_ninja.driver import SeleniumTools, clickandclear
from selenium_ninja.synchronizer import Synchronizer
from django.db import IntegrityError


class UklonRequest(Synchronizer):
    variables = ('token', 'type')

    def get_header(self) -> dict:
        type_token, token = self.redis.get(f"{self.partner_id}{self.variables[1]}"), self.redis.get(f"{self.partner_id}{self.variables[0]}")
        headers = {
            'Authorization': f'{type_token.decode()} {token.decode()}'
         }
        return headers

    def park_payload(self) -> dict:
        payload = {
            'client_id': ParkSettings.get_value(key='CLIENT_ID', partner=self.partner_id),
            'client_secret': ParkSettings.get_value(key='CLIENT_SECRET', partner=self.partner_id),
            'contact': ParkSettings.get_value(key='UKLON_NAME', partner=self.partner_id),
            'device_id': "38c13dc5-2ef3-4637-99f5-8de26b2e8216",
            'grant_type': "password_mfa",
            'password': ParkSettings.get_value(key='UKLON_PASSWORD', partner=self.partner_id),
        }
        return payload

    def create_session(self):
        response = requests.post(Service.get_value('UKLON_SESSION'), json=self.park_payload()).json()
        self.redis.set(f"{self.partner_id}{self.variables[0]}", response["access_token"])
        self.redis.set(f"{self.partner_id}{self.variables[1]}", response["token_type"])

    def response_data(self, url: str = None, params: dict = None,  pjson: dict = None) -> dict:
        if not (self.redis.exists(f"{self.partner_id}{self.variables[1]}") and self.redis.get(f"{self.partner_id}{self.variables[0]}")):
            self.create_session()
        while True:
            response = requests.get(
                url=url,
                headers=self.get_header(),
                json=pjson,
                params=params,
            )
            if response.status_code in (401, 403):
                self.create_session()
            else:
                break
        return response.json()

    def to_float(self, number: int, div=100) -> float:
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

    def find_value_str(self, data: dict, *args) -> str:
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
                                         partner=self.get_partner())
        return list(report)

    def save_report(self, day):
        if self.download_report(day):
            return self.download_report(day)
        param = self.parameters()
        param['dateFrom'] = int(self.start_report_interval(day).timestamp())
        param['dateTo'] = int(self.end_report_interval(day).timestamp())
        url = f"{Service.get_value('UKLON_3')}{ParkSettings.get_value(key='ID_PARK', partner=self.partner_id)}"
        url += Service.get_value('UKLON_4')
        data = self.response_data(url=url, params=param)['items']
        if data:
            for i in data:
                order = Payments(
                    report_from=self.start_report_interval(day).date(),
                    vendor_name=self.fleet,
                    full_name=f"{i['driver']['last_name']} {i['driver']['first_name']}",
                    driver_id=str(i['driver']['signal']),
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
                    partner=self.get_partner(),
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
                partner=self.get_partner())
            try:
                order.save()
            except IntegrityError:
                pass

        return self.download_report(day)

    def get_driver_status(self):
        first_key, second_key = 'width_client', 'wait'
        drivers = {
                first_key: [],
                second_key: [],
            }
        url = f"{Service.get_value('UKLON_5')}{ParkSettings.get_value(key='ID_PARK', partner=self.partner_id)}"
        url += Service.get_value('UKLON_6')
        data = self.response_data(url=url, params=self.parameters())

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
        url = f"{Service.get_value('UKLON_1')}{ParkSettings.get_value(key='ID_PARK', partner=self.partner_id)}"
        url_1 = url + Service.get_value('UKLON_6')
        url_2 = url + Service.get_value('UKLON_2')

        all_drivers = self.response_data(url=url_1, params=param)

        for driver in all_drivers['items']:
            pay_cash, vehicle_name, vin_code = True, '', ''
            if driver['restrictions']:
                pay_cash = False if 'Cash' in driver['restrictions'][0]['restriction_types'] else True

            elif self.find_value_str(driver, *('selected_vehicle', )):
                vehicle_name = f"{driver['selected_vehicle']['make']} {driver['selected_vehicle']['model']}"
                vin_code = self.response_data(f"{url_2}/{driver['selected_vehicle']['vehicle_id']}")
                vin_code = vin_code.get('vin_code', '')

            email = self.response_data(url=f"{url_1}/{driver['id']}")

            drivers.append({
                'fleet_name': self.fleet,
                'name': driver['first_name'],
                'second_name': driver['last_name'],
                'email': email.get('email', ''),
                'phone_number': f"+{driver['phone']}",
                'driver_external_id': driver['signal'],
                'pay_cash': pay_cash,
                'licence_plate': self.find_value_str(driver, *('selected_vehicle', 'license_plate')),
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })

        return drivers


class UklonSynchronizer(Synchronizer, SeleniumTools):
    def login(self):
        self.driver.get(NewUklonService.get_value('NEWUKLON_LOGIN_1'))
        if self.sleep:
            time.sleep(self.sleep)
        login = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_2'))
        login.send_keys(ParkSettings.get_value("UKLON_NAME", partner=self.partner_id))
        password = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_3'))
        password.send_keys('')
        password.send_keys(ParkSettings.get_value("UKLON_PASSWORD", partner=self.partner_id))
        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_4')).click()

    def wait_otp_code(self, user):
        p = redis_instance.pubsub()
        p.subscribe(f'{user.phone_number} code')
        p.ping()
        otpa = []
        start = time.time()
        while True:
            try:
                if time.time() - start >= 180:
                    break
                otp = p.get_message()
                if otp:
                    otpa = list(f'{otp["data"]}')
                    otpa = list(filter(lambda d: d.isdigit(), otpa))
                    digits = [s.isdigit() for s in otpa]
                    if not digits or (not all(digits)) or len(digits) != 4:
                        continue
                    break
            except redis.ConnectionError as e:
                self.logger.error(str(e))
                p = redis_instance.pubsub()
                p.subscribe(f'{user.phone_number} code')
            time.sleep(1)
        return otpa

    def disable_cash(self, pk, enable):
        url = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_1')
        xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath)
        driver = Driver.objects.get(pk=pk)
        fleet = Fleet.objects.get(name=self.fleet)
        try:
            xpath = f'{NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_1")}{driver.second_name} {driver.name}")]'
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except TimeoutException:
            try:
                xpath = f'{NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_1")}{driver.second_name}")]'
                WebDriverWait(self.driver, self.sleep).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))).click()
            except TimeoutException:
                self.logger.error(f'No_driver {str(driver)} in {fleet}')
        WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH,
                                            NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_8")))).click()
        check_cash = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_9"))))
        if enable not in check_cash.get_attribute("aria-checked"):
            time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH,
                                                NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_2")))).click()
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_3")))).click()
        pay_cash = True if enable == 'true' else False
        Fleets_drivers_vehicles_rate.objects.filter(driver=driver, fleet=fleet).update(pay_cash=pay_cash)

    def withdraw_money(self):
        url = NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_1')
        xpath = NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_2')
        self.get_target_element_of_page(url, xpath)
        WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_2')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_3')))).click()
        sum_remain = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_4'))))
        clickandclear(sum_remain)
        sum_remain.send_keys(ParkSettings.get_value("WITHDRAW_UKLON"))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_5')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_6')))).click()

    def add_driver(self, jobapplication):
        url = NewUklonService.get_value('NEWUKLON_ADD_DRIVER_1')
        self.get_target_element_of_page(url, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_2'))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_2')))).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_3')))).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        form_phone_number = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_5'))
        clickandclear(form_phone_number)
        form_phone_number.send_keys(jobapplication.phone_number[4:])
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()

        # 2FA
        code = self.wait_otp_code(jobapplication)
        digits = self.driver.find_elements(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_6'))
        for i, element in enumerate(digits):
            element.send_keys(code[i])
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_7')).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        registration_fields = {"firstName": jobapplication.first_name,
                               "lastName": jobapplication.last_name,
                               "email": jobapplication.email,
                               "password": jobapplication.password}
        for field, value in registration_fields.items():
            element = self.driver.find_element(By.ID, field)
            clickandclear(element)
            element.send_keys(value)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()

        file_paths = [
            f"{settings.MEDIA_URL}{jobapplication.photo}",
            f"{settings.MEDIA_URL}{jobapplication.driver_license_front}",
            f"{settings.MEDIA_URL}{jobapplication.driver_license_back}",

        ]
        for i, file_path in enumerate(file_paths):
            if self.sleep:
                time.sleep(self.sleep)
            local_path = self.download_from_bucket(file_path, i)
            photo_input = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_8'))
            photo_input.send_keys(local_path)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_9')))).click()
            time.sleep(1)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_9')))).click()
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        fleet_code = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_10'))))
        clickandclear(fleet_code)
        fleet_code.send_keys(ParkSettings.get_value("UKLON_TOKEN", NewUklonFleet.token))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        jobapplication.status_uklon = datetime.datetime.now().date()
        jobapplication.save()

    def detaching_the_driver_from_the_car(self, licence_plate):
        self.driver.get(NewUklonService.get_value('NEWUKLONS_DETACHING_THE_DRIVER_FROM_THE_CAR_1'))
        search = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located(
                (By.XPATH, NewUklonService.get_value('NEWUKLONS_DETACHING_THE_DRIVER_FROM_THE_CAR_2'))))
        search.click()
        search.clear()
        search.send_keys(licence_plate)
        time.sleep(self.sleep)
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located(
                    (By.XPATH, NewUklonService.get_value('NEWUKLONS_DETACHING_THE_DRIVER_FROM_THE_CAR_3')))).click()
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located(
                    (By.XPATH, NewUklonService.get_value('NEWUKLONS_DETACHING_THE_DRIVER_FROM_THE_CAR_4')))).click()
        except Exception as err:
            self.logger.error(err)
