import logging
import time
import requests
import os
import pickle
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import TimeoutException, InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from translators.server import tss

from app.models import BoltService, Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle


LOGGER.setLevel(logging.WARNING)


class Synchronizer:

    def __init__(self, chrome_driver=None, fleet=None):
        self.fleet = fleet
        if chrome_driver is None:
            super().__init__(session='Ninja', driver=True, sleep=5, headless=True)
        else:
            super().__init__(session='Ninja', driver=False, sleep=5, headless=True)
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

    def get_target_element_of_page(self, url, xpath, cookies_name):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except TimeoutException:
            try:
                self.driver.get(url)
                time.sleep(self.sleep)
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.logger.info(f'Got the page without authorization {url}')
            except (TimeoutException, FileNotFoundError):
                try:
                    for cookie in pickle.load(open(os.path.join(os.getcwd(), "cookies",
                                                                f'{cookies_name}_cookies'), 'rb')):
                        self.driver.add_cookie(cookie)
                    time.sleep(self.sleep)
                    self.driver.get(url)
                    time.sleep(self.sleep)
                    self.driver.get_screenshot_as_file(f'{cookies_name}.png')
                    WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    self.logger.info(f'Got the page using cookie {url}')
                except (TimeoutException, FileNotFoundError)as e:
                    print(e)
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
            )
            fleets_drivers_vehicles_rate.save()
            self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
            self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)
        else:
            for fleets_drivers_vehicles_rate in drivers:
                if fleets_drivers_vehicles_rate.pay_cash != kwargs['pay_cash']:
                    fleets_drivers_vehicles_rate.pay_cash = kwargs['pay_cash']
                    fleets_drivers_vehicles_rate.save(update_fields=['pay_cash'])
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
            update_fields.append('name')
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