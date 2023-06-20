import csv
import datetime
import os
import pickle
import time
from django.db import IntegrityError
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models import ParkSettings, BoltService, BoltPaymentsOrder
from auto import settings
from selenium_ninja.driver import SeleniumTools, clickandclear
from selenium_ninja.synchronizer import Synchronizer


class BoltSynchronizer(Synchronizer, SeleniumTools):

    def login(self):
        self.driver.get(f"{BoltService.get_value('BOLT_LOGIN_1')}")
        if self.sleep:
            time.sleep(self.sleep)
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_2'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_NAME"))
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_3'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_PASSWORD"))
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_LOGIN_4')).click()
        if self.sleep:
            time.sleep(self.sleep)
        cookie_filename = f'{ParkSettings.get_value("BOLT_NAME")}_cookie'
        cookie_filepath = os.path.join(os.getcwd(), "cookies", cookie_filename)

        pickle.dump(self.driver.get_cookies(), open(cookie_filepath, 'wb'))

    def download_payments_order(self, day=None, interval=None):
        url = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_1')
        xpath = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_2')
        self.get_target_page_or_login(url, xpath, self.login, ParkSettings.get_value("BOLT_NAME"))
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, BoltService.get_value('BOLTS_GET_DRIVER_STATUS_FROM_MAP_1')))).click()
        except:
            pass
        if day:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_3')))).click()
            xpath = f"{BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_4')}[{interval}]"
            date = self.driver.find_element(By.XPATH, xpath)
            if date.text != 'нд':
                date.click()
            else:
                self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_8')).click()
                xpath = f"{BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_4')}[{interval}]"
                self.driver.find_element(By.XPATH, xpath).click()
            self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_5')).click()
        else:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_2')))).click()
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located(
                (By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_6')))).click()
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_7')).click()
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
                    order = BoltPaymentsOrder(
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
            order = BoltPaymentsOrder(
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
        url = BoltService.get_value('BOLTS_GET_DRIVERS_TABLE_1')
        xpath = BoltService.get_value('BOLTS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath, ParkSettings.get_value("BOLT_NAME"))
        # self.driver.get_screenshot_as_file('BoltSynchronizer.png')
        i_table = 0
        while True:
            i_table += 1
            try:
                xpath = f'{BoltService.get_value("BOLTS_GET_DRIVERS_TABLE_3")}[{i_table}]'
                driver_row = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath)))
                name = driver_row.find_element(By.XPATH, BoltService.get_value("BOLTS_GET_DRIVERS_TABLE_4"))
                full_name = name.text
                name.click()
                email = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLTS_GET_DRIVERS_TABLE_5")))).text
                phone_number = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, BoltService.get_value("BOLTS_GET_DRIVERS_TABLE_6")))).text
                elements = self.driver.find_elements(By.XPATH, BoltService.get_value("BOLTS_GET_DRIVERS_TABLE_7"))
                pay_cash = (len(elements) == 2)
                self.driver.back()
                s_name = self.split_name(full_name)
                drivers.append({
                    'fleet_name': 'Bolt',
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
                    (By.XPATH, BoltService.get_value("BOLTS_GET_DRIVER_STATUS_FROM_MAP_1")))).click()
        except:
            pass
        try:
            xpath = f'{BoltService.get_value("BOLTS_GET_DRIVER_STATUS_FROM_MAP_2")}[{search_text}]/div'
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
                el = BoltService.get_value("BOLTS_GET_DRIVER_STATUS_FROM_MAP_3")
                xpath = f'{el}{i}{BoltService.get_value("BOLTS_GET_DRIVER_STATUS_FROM_MAP_3.1")}'
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
            url = BoltService.get_value('BOLTS_GET_DRIVER_STATUS_1')
            xpath = BoltService.get_value('BOLTS_GET_DRIVER_STATUS_2')
            self.get_target_element_of_page(url, xpath, ParkSettings.get_value("BOLT_NAME"))
            return {
                'width_client': self.get_driver_status_from_map('1'),
                'wait': self.get_driver_status_from_map('2')
            }
        except (TimeoutException, WebDriverException) as err:
            self.logger.error(err)

    def download_weekly_report(self, day=None, interval=None):
        try:
            report = BoltPaymentsOrder.objects.filter(
                report_file_name=self.file_pattern(self.fleet, self.partner, day=day))
            if not report:
                self.download_payments_order(day=day, interval=interval)
                self.save_report(day=day)
                report = BoltPaymentsOrder.objects.filter(
                    report_file_name=self.file_pattern(self.fleet, self.partner, day=day))
            return list(report)
        except Exception as err:
            print(err)

    def add_driver(self, jobapplication):
        if not jobapplication.status_bolt:
            url = BoltService.get_value('BOLT_ADD_DRIVER_1')
            self.get_target_element_of_page(url, BoltService.get_value('BOLT_ADD_DRIVER_2.1'),
                                            ParkSettings.get_value("BOLT_NAME"))
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, BoltService.get_value('BOLT_ADD_DRIVER_2.1')))).click()
            form_email = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_ADD_DRIVER_2.2'))))
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
