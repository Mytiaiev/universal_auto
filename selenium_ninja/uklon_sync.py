import csv
import datetime
import os
import pickle
import time

import redis
from django.db import IntegrityError
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.models import NewUklonService, ParkSettings, NewUklonPaymentsOrder, NewUklonFleet, \
    Fleets_drivers_vehicles_rate, Fleet
from auto import settings
from selenium_ninja.driver import SeleniumTools, clickandclear
from selenium_ninja.synchronizer import Synchronizer


class UklonSynchronizer(Synchronizer, SeleniumTools):

    def login(self):
        self.driver.get(NewUklonService.get_value('NEWUKLON_LOGIN_1'))
        if self.sleep:
            time.sleep(self.sleep)
        login = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_2'))
        login.send_keys(ParkSettings.get_value("UKLON_NAME"))
        password = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_3'))
        password.send_keys('')
        password.send_keys(ParkSettings.get_value("UKLON_PASSWORD"))

        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_4')).click()
        if self.sleep:
            time.sleep(self.sleep)
        cookie_filename = f'{ParkSettings.get_value("UKLON_NAME")}_cookie'
        cookie_filepath = os.path.join(os.getcwd(), "cookies", cookie_filename)

        pickle.dump(self.driver.get_cookies(), open(cookie_filepath, 'wb'))

    def download_payments_order(self, day=None):
        url = NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_1')
        xpath = NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_2')
        self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
        self.driver.find_element(By.XPATH, xpath).click()
        if day:
            if self.sleep:
                time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_3')))).click()
            input_data = WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_4'))))
            input_data.click()
            input_data.send_keys(day + Keys.TAB + day)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_5')))).click()
        else:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_6')))).click()

        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_7')).click()
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
                    order = NewUklonPaymentsOrder(
                        report_from=self.start_report_interval(day=day),
                        report_to=self.end_report_interval(day=day),
                        report_file_name=file.name,
                        full_name=row[0],
                        signal=row[1],
                        total_rides=float((row[2] or '0').replace(',', '')),
                        total_distance=float((row[3] or '0').replace(',', '')),
                        total_amount_cach=float((row[4] or '0').replace(',', '')),
                        total_amount_cach_less=float((row[5] or '0').replace(',', '')),
                        total_amount_on_card=float((row[6] or '0').replace(',', '')),
                        total_amount=float((row[7] or '0').replace(',', '')),
                        tips=float((row[8] or '0').replace(',', '')),
                        bonuses=float((row[9] or '0').replace(',', '')),
                        fares=float((row[10] or '0').replace(',', '')),
                        comission=float((row[11] or '0').replace(',', '')),
                        total_amount_without_comission=float((row[12] or '0').replace(',', '')))
                    try:
                        order.save()
                    except IntegrityError:
                        pass
                    items.append(order)

        else:
            order = NewUklonPaymentsOrder(
                report_from=self.start_report_interval(day=day),
                report_to=self.end_report_interval(day=day),
                report_file_name='',
                full_name='',
                signal='',
                total_rides=0,
                total_distance=0,
                total_amount_cach=0,
                total_amount_cach_less=0,
                total_amount_on_card=0,
                total_amount=0,
                tips=0,
                bonuses=0,
                fares=0,
                comission=0,
                total_amount_without_comission=0)
            try:
                order.save()
            except IntegrityError:
                pass

        return items

    def wait_otp_code(self, user):
        r = redis.Redis.from_url(os.environ["REDIS_URL"])
        p = r.pubsub()
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
                    if not (digits) or (not all(digits)) or len(digits) != 4:
                        continue
                    break
            except redis.ConnectionError as e:
                self.logger.error(str(e))
                p = r.pubsub()
                p.subscribe(f'{user.phone_number} code')
            time.sleep(1)
        return otpa

    def get_drivers_table(self):
        drivers = []
        url = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_1')
        xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
        # self.driver.get_screenshot_as_file('UklonSynchronizer.png')
        driver_urls = []
        i = 0
        while True:
            i += 1
            try:
                xpath = f'{NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_3.1")}{i}{NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_3.2")}'
                url = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("href")
                driver_urls.append(url)
            except TimeoutException:
                break
        for url in driver_urls:
            self.driver.get(url)
            xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_4')
            self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
            name = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_5')
            email = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_6')
            phone_number = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_7')
            driver_external_id = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            try:
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_8')
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_9')
                pay_cash = 'true' in WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-checked")
            except TimeoutException:
                pay_cash = False
            licence_plate = ''
            vehicle_name = ''
            vin_code = ''
            try:
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_10')
                vehicle_url = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("href")
                self.driver.get(vehicle_url)
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_11')
                self.get_target_element_of_page(vehicle_url, xpath, ParkSettings.get_value("UKLON_NAME"))
                licence_plate = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_12')
                vehicle_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_13')
                vin_code = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                pass
            s_name = self.split_name(name)
            drivers.append({
                'fleet_name': 'NewUklon',
                'name': s_name[0],
                'second_name': s_name[1],
                'email': self.validate_email(email),
                'phone_number': self.validate_phone_number(phone_number),
                'driver_external_id': driver_external_id,
                'pay_cash': pay_cash,
                'licence_plate': licence_plate,
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })
        return drivers

    def get_driver_status_from_map(self, search_text):
        raw_data = []
        self.driver.refresh()
        xpath = f"{NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_FROM_MAP_1')}[{search_text}]"
        status_box = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
        count_drivers = status_box.find_element(
            By.XPATH, NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_FROM_MAP_2.0')).text
        if int(count_drivers):
            status_box.click()
        else:
            return raw_data
        i = 0
        while i < int(count_drivers):
            i += 1
            try:
                el = NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_FROM_MAP_2.1')
                xpath = f"{el}{i}{NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_FROM_MAP_2.2')}"
                driver_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                return raw_data
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name = '', ''
            try:
                name, second_name = name_list[0], name_list[1]
            except IndexError:
                pass
            raw_data.append((name, second_name))
            raw_data.append((second_name, name))
        xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_FROM_MAP_3')
        WebDriverWait(self.driver, self.sleep).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        return raw_data

    def get_driver_status(self):
        try:
            url = NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_1')
            xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVER_STATUS_2')

            self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
            return {
                'width_client': self.get_driver_status_from_map('1'),
                'wait': self.get_driver_status_from_map('2')
            }
        except WebDriverException as err:
            self.logger.error(err)

    def disable_cash(self, name, second_name, disable):
        url = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_1')
        xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
        driver = self.get_driver_by_name(name=name, second_name=second_name)
        fleet = Fleet.objects.get(name=self.fleet)
        try:
            xpath = f'{NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_1")}{second_name} {name}")]'
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, xpath))).click()
        except TimeoutException:
            try:
                xpath = f'{NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_1")}{second_name}")]'
                WebDriverWait(self.driver, self.sleep).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))).click()
            except TimeoutException:
                self.logger.error(f'No_driver {driver} in {fleet}')
        WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH,
                                            NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_8")))).click()
        check_cash = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_9"))))
        if ((disable and 'true' in check_cash.get_attribute("aria-checked")) or
                (not disable and 'false' in check_cash.get_attribute("aria-checked"))):
            time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH,
                                                NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_2")))).click()
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value("NEWUKLONS_DISABLE_CASH_3")))).click()
        new_check = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value("NEWUKLONS_GET_DRIVERS_TABLE_9"))))
        if 'true' in new_check.get_attribute("aria-checked"):
            pay_cash = True
        else:
            pay_cash = False
        Fleets_drivers_vehicles_rate.objects.filter(driver=driver, fleet=fleet).update(pay_cash=pay_cash)

    def withdraw_money(self):
        url = NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_1')
        xpath = NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_2')
        self.get_target_element_of_page(url, xpath, ParkSettings.get_value("UKLON_NAME"))
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
        self.get_target_element_of_page(url, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_2'),
                                        ParkSettings.get_value("UKLON_NAME"))
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

    def download_weekly_report(self, day=None):
        try:
            report = NewUklonPaymentsOrder.objects.filter(
                report_file_name=self.file_pattern(self.fleet, self.partner, day=day))
            if not report:
                self.download_payments_order(day=day)
                self.save_report(day=day)
                report = NewUklonPaymentsOrder.objects.filter(
                    report_file_name=self.file_pattern(self.fleet, self.partner, day=day))
            return list(report)
        except Exception as err:
            print(err)
