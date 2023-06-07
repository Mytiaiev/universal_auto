import json
import logging
import os
import re
import time
import datetime

import requests
from django.utils import timezone
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException, WebDriverException, InvalidSessionIdException
from translators.server import tss
from app.models import Driver, Fleets_drivers_vehicles_rate, Fleet, Vehicle, UseOfCars, RentInformation, StatusChange, \
    ParkSettings, UberService, UaGpsService, NewUklonService, BoltService, NewUklonFleet, Bolt, NewUklon, Uber, \
    SeleniumTools, UaGps, clickandclear, BoltPaymentsOrder, NewUklonPaymentsOrder, UberPaymentsOrder
from auto import settings
from auto_bot.main import bot

LOGGER.setLevel(logging.WARNING)


class Synchronizer:

    def __init__(self, chrome_driver=None):
        if chrome_driver is None:
            super().__init__(driver=True, sleep=5, headless=True)
        else:
            super().__init__(driver=False, sleep=5, headless=True)
            self.driver = chrome_driver

    def try_to_execute(self, func_name, *args, **kwargs):
        if not self.driver.service.is_connectable():
            print('###################### Driver recreating... ########################')
            self.driver = self.build_driver()
            time.sleep(self.sleep)
        try:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, '//div')))
        except InvalidSessionIdException:
            print('###################### Session recreating... ########################')
            self.driver = self.build_driver()
            time.sleep(self.sleep)
        except TimeoutException:
            pass
        return getattr(self, func_name)(*args, **kwargs)

    @staticmethod
    def download_from_bucket(path, filename):
        response = requests.get(path)
        local_path = os.path.join(os.getcwd(), f"Temp/{filename}.jpg")
        with open(local_path, "wb") as file:
            file.write(response.content)
        return local_path

    def get_target_element_of_page(self, url, xpath):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except TimeoutException:
            try:
                self.driver.get(url)
                time.sleep(self.sleep)
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.logger.info(f'Got the page without authorization {url}')
            except (TimeoutException, FileNotFoundError):
                    self.login()
                    try:
                        WebDriverWait(self.driver, self.sleep).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, BoltService.get_value('BOLTS_GET_DRIVER_STATUS_FROM_MAP_1')))).click()
                    except:
                        pass
                    self.driver.get(url)
                    WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    self.logger.info(f'Got the page using authorization {url}')

    def create_driver(self, **kwargs):
        try:
            fleet = Fleet.objects.get(name=kwargs['fleet_name'])
        except Driver.DoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs['driver_external_id'])
        if len(drivers) == 0:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs['driver_external_id'],
                pay_cash=kwargs['pay_cash'],
                withdraw_money=kwargs['withdraw_money'],
            )
            fleets_drivers_vehicles_rate.save()
            self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
            self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)
        else:
            for fleets_drivers_vehicles_rate in drivers:
                if any([
                    fleets_drivers_vehicles_rate.pay_cash != kwargs['pay_cash'],
                    fleets_drivers_vehicles_rate.withdraw_money != kwargs['withdraw_money']
                ]):
                    fleets_drivers_vehicles_rate.pay_cash = kwargs['pay_cash']
                    fleets_drivers_vehicles_rate.withdraw_money = kwargs['withdraw_money']
                    fleets_drivers_vehicles_rate.save(update_fields=['pay_cash', 'withdraw_money'])
                self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
                self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)

    def update_driver_fields(self, driver, **kwargs):
        update_fields = []
        if driver.phone_number == '' and kwargs['phone_number'] != '':
            driver.phone_number = kwargs['phone_number']
            update_fields.append('phone_number')
        if driver.email == '' and kwargs['email'] != '':
            driver.email = kwargs['email']
            update_fields.append('email')
        if len(update_fields):
            driver.save(update_fields=update_fields)

    def update_vehicle_fields(self, vehicle, **kwargs):
        update_fields = []
        if vehicle.name == '' and kwargs['vehicle_name'] != '':
            vehicle.name = kwargs['vehicle_name']
            update_fields.append('vehicle_name')
        if vehicle.vin_code == '' and kwargs['vin_code'] != '':
            vehicle.vin_code = kwargs['vin_code']
            update_fields.append('vin_code')
        if len(update_fields):
            vehicle.save(update_fields=update_fields)

    def get_or_create_vehicle(self, **kwargs):
        licence_plate = kwargs['licence_plate']
        if len(licence_plate) == 0:
            licence_plate = 'Unknown car'
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate)
        except Vehicle.MultipleObjectsReturned:
            vehicle = Vehicle.objects.filter(licence_plate=licence_plate)[0]
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs['vehicle_name'],
                model='',
                type='',
                licence_plate=licence_plate,
                vin_code=kwargs['vin_code']
            )
            vehicle.save()
        return vehicle

    def get_driver_by_name(self, name, second_name):
        try:
            return Driver.objects.get(name=name, second_name=second_name)
        except Driver.MultipleObjectsReturned:
            return Driver.objects.filter(name=name, second_name=second_name)[0]

    def get_driver_by_phone_or_email(self, phone_number, email):
        try:
            if len(phone_number):
                return Driver.objects.get(phone_number__icontains=phone_number[-10::])
            else:
                raise Driver.DoesNotExist
        except (Driver.MultipleObjectsReturned, Driver.DoesNotExist):
            try:
                return Driver.objects.get(email__icontains=email)
            except Driver.MultipleObjectsReturned:
                raise Driver.DoesNotExist

    def get_or_create_driver(self, **kwargs):
        try:
            driver = self.get_driver_by_name(kwargs['name'], kwargs['second_name'])
        except Driver.DoesNotExist:
            try:
                driver = self.get_driver_by_name(kwargs['second_name'], kwargs['name'])
            except Driver.DoesNotExist:
                t_name, t_second_name = self.split_name(
                    self.translate_text(f'{kwargs["name"]} {kwargs["second_name"]}', 'uk'))
                try:
                    driver = self.get_driver_by_name(t_name, t_second_name)
                except Driver.DoesNotExist:
                    try:
                        driver = self.get_driver_by_name(t_second_name, t_name)
                    except Driver.DoesNotExist:
                        t_name, t_second_name = self.split_name(
                            self.translate_text(f'{kwargs["name"]} {kwargs["second_name"]}', 'ru'))
                        try:
                            driver = self.get_driver_by_name(t_name, t_second_name)
                        except Driver.DoesNotExist:
                            try:
                                driver = self.get_driver_by_name(t_second_name, t_name)
                            except Driver.DoesNotExist:
                                try:
                                    driver = self.get_driver_by_phone_or_email(kwargs['phone_number'], kwargs['email'])
                                except Driver.DoesNotExist:
                                    driver = Driver.objects.create(
                                        name=kwargs['name'],
                                        second_name=kwargs['second_name'],
                                        phone_number=kwargs['phone_number'],
                                        email=kwargs['email']
                                    )
                                    driver.save()
        return driver

    def translate_text(self, text, to_lang):
        try:
            return tss.google(text, to_language=to_lang, if_use_cn_host=False)
        except Exception:
            return text

    def split_name(self, name):
        name_list = [x for x in name.split(' ') if len(x) > 0]
        name = ''
        second_name = ''
        try:
            name = name_list[0]
            second_name = name_list[1]
        except IndexError:
            pass
        res = (name, second_name)
        return res

    def validate_email(self, email):
        if '@' in email:
            return email
        else:
            return ''

    def validate_phone_number(self, phone_number):
        return ''.join([x for x in phone_number if x.isdigit() or x == '+'][:13])

    def get_drivers_table(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for driver in drivers:
            self.create_driver(**driver)


class BoltSynchronizer(Synchronizer, Bolt):

    def get_drivers_table(self):
        drivers = []
        url = BoltService.get_value('BOLTS_GET_DRIVERS_TABLE_1')
        xpath = BoltService.get_value('BOLTS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath)
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
                    'withdraw_money': False,
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
            xpath = f'{BoltService.get_value("BOLTS_GET_DRIVER_STATUS_FROM_MAP_2")}[{search_text}]'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        except TimeoutException:
            return raw_data
        i = 0
        while True:
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
            self.get_target_element_of_page(url, xpath)
            return {
                'width_client': self.get_driver_status_from_map('2'),
                'wait': self.get_driver_status_from_map('3')
            }
        except (TimeoutException, WebDriverException) as err:
            print(err.msg)

    def download_weekly_report(self, day=None, interval=None):
        try:
            report = BoltPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            if not report:
                self.download_payments_order(day=day, interval=interval)
                self.save_report(day=day)
                report = BoltPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            return list(report)
        except Exception as err:
            print(err)

    def add_driver(self, jobapplication):
        if not jobapplication.status_bolt:
            url = BoltService.get_value('BOLT_ADD_DRIVER_1')
            self.get_target_element_of_page(url, BoltService.get_value('BOLT_ADD_DRIVER_2.1'))
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


class UklonSynchronizer(Synchronizer, NewUklon):

    def get_drivers_table(self):
        drivers = []
        url = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_1')
        xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_2')
        self.get_target_element_of_page(url, xpath)
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
            self.get_target_element_of_page(url, xpath)
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
                withdraw_money = 'true' in WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-checked")
            except TimeoutException:
                withdraw_money = False
            licence_plate = ''
            vehicle_name = ''
            vin_code = ''
            try:
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_10')
                vehicle_url = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("href")
                self.driver.get(vehicle_url)
                xpath = NewUklonService.get_value('NEWUKLONS_GET_DRIVERS_TABLE_11')
                self.get_target_element_of_page(vehicle_url, xpath)
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
                'pay_cash': False,
                'withdraw_money': withdraw_money,
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

            self.get_target_element_of_page(url, xpath)
            return {
                'width_client': self.get_driver_status_from_map('1'),
                'wait': self.get_driver_status_from_map('2')
            }
        except WebDriverException as err:
            print(err.msg)

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
        sum_remain.send_keys(ParkSettings.get_value("Залишок Uklon", 150))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLONS_WITHDRAW_MONEY_5')))).click()
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

    def download_weekly_report(self, day=None):
        try:
            report = NewUklonPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            if not report:
                self.download_payments_order(day=day)
                self.save_report(day=day)
                report = NewUklonPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            return list(report)
        except Exception as err:
            print(err)


class UberSynchronizer(Synchronizer, Uber):

    def login(self):
        # """ Don't login in UberSynchronizer cause this instance runs periodically"""
        self.login_v3()
        pass

    def get_all_vehicles(self):
        vehicles = {}
        url = UberService.get_value('UBERS_GET_ALL_VEHICLES_1')
        xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_2')
        self.get_target_element_of_page(url, xpath)
        # self.driver.get_screenshot_as_file('UberSynchronizer.png')
        i = 0
        while True:
            i += 1
            try:
                xpath = f'{UberService.get_value("UBERS_GET_ALL_VEHICLES_3")}[{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                try:
                    vehicleUUID = json.loads(row.get_attribute("data-tracking-payload"))['vehicleUUID']
                except Exception:
                    continue
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_4')
                vehicle_name = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_5')
                vin_code = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_6')
                licence_plate = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                break
            vehicles[vehicleUUID] = {'licence_plate': licence_plate, 'vin_code': vin_code, 'vehicle_name': vehicle_name}
        return vehicles

    def get_drivers_table(self):
        try:
            vehicles = self.get_all_vehicles()
            drivers = []
            url = UberService.get_value('UBERS_GET_DRIVERS_TABLE_1')
            # url = f'{self.base_url}/orgs/2c5515cd-a4ed-4136-905f-99504677a324/drivers'  #my
            self.driver.get(url)
            xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_2')
            self.get_target_element_of_page(url, xpath)
        except TimeoutException:
            return []
        i = 0
        while True:
            i += 1
            try:
                xpath = f'{UberService.get_value("UBERS_GET_DRIVERS_TABLE_3")}[{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_4')
                name = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_5')
                email = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_6')
                phone_number = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                try:
                    driver_external_id = json.loads(row.get_attribute("data-tracking-payload"))['driverUUID']
                except Exception:
                    continue
                licence_plate = ''
                vehicle_name = ''
                vin_code = ''
                try:
                    xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_7')
                    WebDriverWait(self.driver, self.sleep).until(
                        EC.presence_of_element_located((By.XPATH, xpath))).click()
                    xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_8')
                    WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                    xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_9')
                    el = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    vehicleUUID = json.loads(el.get_attribute("data-tracking-payload"))['vehicleUUID']
                    licence_plate = vehicles[vehicleUUID]['licence_plate']
                    vehicle_name = vehicles[vehicleUUID]['vehicle_name']
                    vin_code = vehicles[vehicleUUID]['vin_code']
                except Exception:
                    pass
            except TimeoutException:
                break
            s_name = self.split_name(name)
            drivers.append({
                'fleet_name': 'Uber',
                'name': s_name[0],
                'second_name': s_name[1],
                'email': self.validate_email(email),
                'phone_number': self.validate_phone_number(phone_number),
                'driver_external_id': driver_external_id,
                'pay_cash': False,
                'withdraw_money': False,
                'licence_plate': licence_plate,
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })
        return drivers

    def get_driver_status_from_map(self, search_text):
        raw_data = []
        try:
            xpath = "//div[@data-baseweb='table-custom']/div[@tabindex='0']"
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except TimeoutException:
            return raw_data
        i = 0
        while True:
            i += 1
            try:
                xpath = "//div[@data-baseweb='typo-labelsmall']"
                driver_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = "//div[@data-testid='driver-card']"
                card = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                payload_str = card.get_attribute('data-tracking-payload')
                payload_dict = json.loads(payload_str)
            except TimeoutException:
                break
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name = '', ''
            try:
                name, second_name = name_list[0], name_list[1]
            except IndexError:
                pass
            if payload_dict[f"{search_text}"]:
                raw_data.append((name, second_name))
                raw_data.append((second_name, name))
        return raw_data

    def get_driver_status(self):

        try:

            url = UberService.get_value('UBERS_GET_DRIVER_STATUS_1')
            # url = f"https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/livemap"
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            xpath = UberService.get_value('UBERS_GET_DRIVER_STATUS_2')
            self.get_target_element_of_page(url, xpath)
            return {
                'online': self.get_driver_status_from_map('ONLINE'),
                'width_client': self.get_driver_status_from_map('IN_PROGRESS'),
                'wait': self.get_driver_status_from_map('ACCEPTED')
            }
        except WebDriverException as err:
            print(err.msg)

    def download_weekly_report(self, day=None):
        try:
            report = UberPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            if not report:
                self.download_payments_order(day=day)
                self.save_report(day=day)
                report = UberPaymentsOrder.objects.filter(report_file_name=self.file_pattern(day=day))
            return list(report)
        except Exception as err:
            print(err.msg)


class UaGpsSynchronizer(Synchronizer, UaGps):

    def generate_report(self, start_time, end_time, report_object):

        """
        :param start_time: time from which we need to get report
        :type start_time: datetime.datetime
        :param end_time: time to which we need to get report
        :type end_time: datetime.datetime
        :param report_object: license plate
        :type report_object: str
        :return: distance and time in rent
        """
        xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
        self.get_target_page_or_login(self.base_url, xpath, self.login)
        self.driver.find_element(By.XPATH, xpath).click()
        unit = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_2'))))
        unit.click()
        try:
            self.driver.find_element(By.XPATH,
                                     f'{UaGpsService.get_value("UAGPSS_GENERATE_REPORT_3")} "{report_object}")]').click()
        except:
            return 0, datetime.timedelta()
        from_field = self.driver.find_element(By.ID, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_4'))
        clickandclear(from_field)
        from_field.send_keys(start_time.strftime("%d %B %Y %H:%M"))
        from_field.send_keys(Keys.ENTER)
        to_field = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.ID, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_5'))))
        clickandclear(to_field)
        to_field.send_keys(end_time.strftime("%d %B %Y %H:%M"))
        to_field.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_6')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        road_distance = self.driver.find_element(By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_7')).text
        rent_distance = float(road_distance.split(' ')[0])
        roadtimestr = self.driver.find_element(By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_8')).text
        roadtime = [int(i) for i in roadtimestr.split(':')]
        rent_time = datetime.timedelta(hours=roadtime[0], minutes=roadtime[1], seconds=roadtime[2])
        return rent_distance, rent_time

    # def get_rent_distance(self):
    #     now = timezone.localtime()
    #     start = timezone.datetime.combine(now, datetime.datetime.min.time()).astimezone()
    #     for _driver in Driver.objects.all():
    #         rent_distance = 0
    #         rent_time = datetime.timedelta()
    #         # car that have worked at that day
    #         working_cars = UseOfCars.objects.filter(created_at__gte=start,
    #                                                 created_at__lte=now)
    #         vehicles = Vehicle.objects.filter(driver=_driver)
    #         if vehicles:
    #             for vehicle in vehicles:
    #                 # check driver's car before they start work
    #                 first_use = working_cars.filter(licence_plate=vehicle.licence_plate).first()
    #                 if first_use:
    #                     rent_before = self.generate_report(start,
    #                                                        timezone.localtime(first_use.created_at),
    #                                                        vehicle.licence_plate)
    #                     rent_distance += rent_before[0]
    #                     rent_time += rent_before[1]
    #                     # check driver's car after work
    #                     last_use = list(working_cars.filter(licence_plate=vehicle.licence_plate))[-1]
    #                     if last_use.end_at:
    #                         rent_after = self.generate_report(timezone.localtime(last_use.end_at),
    #                                                           now,
    #                                                           vehicle.licence_plate)
    #                         rent_distance += rent_after[0]
    #                         rent_time += rent_after[1]
    #                 #  car not used in that day
    #                 else:
    #                     rent = self.generate_report(start, now, vehicle.licence_plate)
    #                     rent_distance += rent[0]
    #                     rent_time += rent[1]
    #         # driver work at that day
    #         driver_use = working_cars.filter(user_vehicle=_driver)
    #         if driver_use:
    #             for car in driver_use:
    #                 if car.end_at:
    #                     end = car.end_at
    #                 else:
    #                     end = now
    #                 rent_statuses = StatusChange.objects.filter(driver=_driver.id,
    #                                                             name__in=[Driver.ACTIVE, Driver.OFFLINE, Driver.RENT],
    #                                                             start_time__gte=timezone.localtime(car.created_at),
    #                                                             start_time__lte=timezone.localtime(end))
    #                 for status in rent_statuses:
    #                     if status.end_time:
    #                         end = status.end_time
    #                     else:
    #                         end = now
    #                     status_report = self.generate_report(timezone.localtime(status.start_time),
    #                                                          timezone.localtime(end),
    #                                                          car.licence_plate)
    #                     rent_distance += status_report[0]
    #                     rent_time += status_report[1]
    #         #             update today rent in db
    #         rent_today = RentInformation.objects.filter(driver_name=_driver,
    #                                                     created_at__date=timezone.now().date()).first()
    #         if rent_today:
    #             rent_today.rent_time = rent_time
    #             rent_today.rent_distance = rent_distance
    #             rent_today.save()
    #         else:
    #             #  create rent file for today
    #             RentInformation.objects.create(driver_name=_driver,
    #                                            driver=_driver,
    #                                            rent_time=rent_time,
    #                                            rent_distance=rent_distance)

    def get_rent_distance(self):
        now = timezone.localtime()
        start = timezone.datetime.combine(now, datetime.datetime.min.time()).astimezone()
        for _driver in Driver.objects.all():
            rent_distance = 0
            rent_time = datetime.timedelta()
            # car that have worked at that day
            working_cars = UseOfCars.objects.filter(created_at__gte=start,
                                                    created_at__lte=now)
            vehicles = Vehicle.objects.filter(driver=_driver)
            if vehicles:
                for vehicle in vehicles:
                    # check driver's car before they start work
                    first_use = working_cars.filter(licence_plate=vehicle.licence_plate).first()
                    if first_use:
                        rent_before = self.generate_report(start,
                                                           timezone.localtime(first_use.created_at),
                                                           vehicle.licence_plate)
                        rent_distance += rent_before[0]
                        rent_time += rent_before[1]
                        # check driver's car after work
                        last_use = list(working_cars.filter(licence_plate=vehicle.licence_plate))[-1]
                        if last_use.end_at:
                            rent_after = self.generate_report(timezone.localtime(last_use.end_at),
                                                              now,
                                                              vehicle.licence_plate)
                            rent_distance += rent_after[0]
                            rent_time += rent_after[1]
                    #  car not used in that day
                    else:
                        # driver work at that day
                        rent_statuses = StatusChange.objects.filter(driver=_driver.id,
                                                                    name__in=[Driver.ACTIVE, Driver.OFFLINE,
                                                                              Driver.RENT],
                                                                    start_time__gte=timezone.localtime(start),
                                                                    start_time__lte=timezone.localtime(now))
                        for status in rent_statuses:
                            if status.end_time:
                                end = status.end_time
                            else:
                                end = now
                            status_report = self.generate_report(timezone.localtime(status.start_time),
                                                                 timezone.localtime(end),
                                                                 vehicle.licence_plate)
                            rent_distance += status_report[0]
                            rent_time += status_report[1]
            #             update today rent in db
            rent_today = RentInformation.objects.filter(driver_name=_driver,
                                                        created_at__date=timezone.localtime().date()).first()
            if rent_today:
                rent_today.rent_time = rent_time
                rent_today.rent_distance = rent_distance
                rent_today.save()
            else:
                #  create rent file for today
                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=rent_time,
                                               rent_distance=rent_distance)
