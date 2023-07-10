import logging
import time
import pendulum
import redis
import requests
import os
import pickle
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import TimeoutException, InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from translators.server import tss

from app.models import BoltService, Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Park


LOGGER.setLevel(logging.WARNING)

class RequestSynchronizer:
    pass


class Synchronizer:
    variables = ('token', 'type')

    def __init__(self, park_id, fleet, chrome_driver=None):
        self.id = park_id
        self.fleet = fleet
        self.redis = redis.Redis.from_url(os.environ["REDIS_URL"])

        if chrome_driver is None:
            super().__init__(partner=park_id, profile=f'Task_{park_id}', driver=True, remote=True, sleep=5, headless=True)
        else:
            super().__init__(partner=park_id, profile=f'Task_{park_id}', driver=False, remote=True, sleep=5, headless=True)
            self.driver = chrome_driver

    def try_to_execute(self, func_name, *args, **kwargs):
        # if not self.driver.service.is_connectable():
        #     print('###################### Driver recreating... ########################')
        #     self.driver = self.build_remote_driver()
        #     time.sleep(self.sleep)
        # try:
        #     WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, '//div')))
        # except InvalidSessionIdException:
        #     print('###################### Session recreating... ########################')
        #     self.driver = self.build_remote_driver()
        #     time.sleep(self.sleep)
        # except TimeoutException:
        #     pass
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
                time.sleep(self.sleep)
                self.driver.get(url)
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.logger.info(f'Got the page using authorization {url}')

    def get_partner(self) -> object:
        park = Park.objects.select_related('partner').get(pk=self.id)
        return park.partner

    def get_drivers_table(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for driver in drivers:
            self.create_driver(**driver)

    def create_driver(self, **kwargs):
        pay_cash, id_, fleet_ = 'pay_cash', 'driver_external_id', 'fleet_name'
        try:
            fleet = Fleet.objects.get(name=kwargs[fleet_])
        except Fleet.DoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs[id_],
                                                              partner=self.get_partner())
        if not drivers:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs[id_],
                pay_cash=kwargs[pay_cash],
                partner=self.get_partner(),
            )
            fleets_drivers_vehicles_rate.save()
            self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
            self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)
        else:
            for fleets_drivers_vehicles_rate in drivers:
                if fleets_drivers_vehicles_rate.pay_cash != kwargs[pay_cash]:
                    fleets_drivers_vehicles_rate.pay_cash = kwargs[pay_cash]
                    fleets_drivers_vehicles_rate.save(update_fields=[pay_cash])
                self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
                self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)

    def check_name(self, name, second_name, partner):
        result = self.translate_text(f'{name} {second_name}', 'uk').split()
        driver = Driver.objects.filter(name=result[0], second_name=result[1], partner=partner)
        if not driver:
            result = self.translate_text(f'{name} {second_name}', 'ru').split()
        return result[0], result[1], partner

    def get_or_create_driver(self, **kwargs):
        name, s_name, phone, email = 'name', 'second_name', 'phone_number', 'email'
        try:
            result = self.check_name(kwargs[name], kwargs[s_name], self.get_partner())
            driver = Driver.objects.get(name=result[0],
                                        second_name=result[1],
                                        partner=result[2])
        except Driver.DoesNotExist:
            driver = Driver.objects.create(
                name=kwargs[name],
                second_name=kwargs[s_name],
                phone_number=kwargs[phone],
                email=kwargs[email],
                partner=self.get_partner(),
            )
            driver.save()
        return driver

    def get_or_create_vehicle(self, **kwargs):
        licence_plate, unk, v_name, vin = kwargs['licence_plate'], 'Unknown car', 'vehicle_name', 'vin_code'
        if not licence_plate:
            licence_plate = unk
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate)
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs[v_name].upper(),
                model='',
                type='',
                licence_plate=licence_plate,
                vin_code=kwargs[vin],
                partner=self.get_partner()
            )
            vehicle.save()
        return vehicle

    @staticmethod
    def update_vehicle_fields(vehicle, **kwargs):
        key_vehicle_name, key_vin = 'vehicle_name', 'vin_code'
        update_fields, vehicle_name, vin_code = [], kwargs[key_vehicle_name], kwargs[key_vin]

        if vehicle.name != vehicle_name and vehicle_name:
            vehicle.name = vehicle_name
            update_fields.append(key_vehicle_name[-4:])
        elif vehicle.vin_code != vin_code and vin_code:
            vehicle.vin_code = vin_code
            update_fields.append(key_vin)
        elif update_fields:
            vehicle.save(update_fields=update_fields)

    @staticmethod
    def update_driver_fields(driver, **kwargs):
        key_phone, key_email = 'phone_number', 'email'
        update_fields, phone_number, email = [], kwargs[key_phone], kwargs[key_email]

        if not driver.phone_number and phone_number:
            driver.phone_number = phone_number
            update_fields.append(key_phone)
        elif driver.email != email and email:
            driver.email = email
            update_fields.append(key_email)
        elif update_fields:
            driver.save(update_fields=update_fields)

    @staticmethod
    def translate_text(text, to_lang):
        try:
            return tss.google(text, to_language=to_lang, if_use_cn_host=False)
        except Exception:
            return text

    # @staticmethod
    # def start_report_interval(start_date):
    #     date = pendulum.from_format(start_date, "YYYY-MM-DD")
    #     return date.in_timezone("Europe/Kiev").start_of("day")
    #
    # @staticmethod
    # def end_report_interval(end_date):
    #     date = pendulum.from_format(end_date, "YYYY-MM-DD")
    #     return date.in_timezone("Europe/Kiev").end_of("day")

    @staticmethod
    def parameters() -> dict:
        params = {
            'limit': '50',
            'offset': '0',
        }
        return params


