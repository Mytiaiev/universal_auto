import logging
import time
import requests
import os
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from scripts.redis_conn import redis_instance
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import TimeoutException, InvalidSessionIdException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from app.models import Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Role, JobApplication, Partner
import datetime

LOGGER.setLevel(logging.WARNING)


class Synchronizer:

    def __init__(self, partner_id, fleet, chrome_driver=None):
        self.partner_id = partner_id
        self.fleet = fleet
        self.redis = redis_instance
        if chrome_driver is not None:
            self.logger = logging.getLogger(__name__)
            self.sleep = 5
            self.driver = chrome_driver

    def try_to_execute(self, func_name, *args, **kwargs):
        # if not self.driver.service.is_connectable():
        #     print('###################### Driver recreating... ########################')
        #     self.driver = self.build_driver()
        #     time.sleep(self.sleep)
        # try:
        #     WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, '//div')))
        # except InvalidSessionIdException:
        #     print('###################### Session recreating... ########################')
        #     self.driver = self.build_driver()
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
            except:
                self.login()
                time.sleep(self.sleep)
                self.driver.get(url)
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))

    def get_partner(self) -> object:
        return Partner.objects.get(pk=self.partner_id)

    def get_drivers_table(self):
        raise NotImplementedError

    def get_vehicles(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        vehicles = self.get_vehicles()
        print(f'Received {self.__class__.__name__} vehicles: {len(vehicles)}')
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for vehicle in vehicles:
            self.get_or_create_vehicle(**vehicle)
        for driver in drivers:
            self.create_driver(**driver)


    def create_driver(self, **kwargs):
        try:
            fleet = Fleet.objects.get(name=kwargs['fleet_name'])
        except ObjectDoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs['driver_external_id'],
                                                              partner=self.get_partner())
        if not drivers:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs['driver_external_id'],
                pay_cash=kwargs['pay_cash'],
                partner=self.get_partner(),
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

    def get_driver_by_name(self, name, second_name, partner):
        try:
            return Driver.objects.get(name=name, second_name=second_name, partner=partner)
        except MultipleObjectsReturned:
            return Driver.objects.filter(name=name, second_name=second_name, partner=partner)[0]

    def get_driver_by_phone_or_email(self, phone_number, email, partner):
        try:
            if phone_number:
                return Driver.objects.get(phone_number__icontains=phone_number[-10::], partner=partner)
            else:
                raise ObjectDoesNotExist
        except (MultipleObjectsReturned, ObjectDoesNotExist):
            try:
                return Driver.objects.get(email__icontains=email, partner=partner)
            except MultipleObjectsReturned:
                raise ObjectDoesNotExist

    def get_or_create_driver(self, **kwargs):
        try:
            driver = self.get_driver_by_name(kwargs['name'],
                                             kwargs['second_name'],
                                             partner=self.get_partner())
        except ObjectDoesNotExist:
            try:
                driver = self.get_driver_by_name(kwargs['second_name'],
                                                 kwargs['name'],
                                                 partner=self.get_partner())
            except ObjectDoesNotExist:
                try:
                    driver = self.get_driver_by_phone_or_email(kwargs['phone_number'],
                                                               kwargs['email'],
                                                               partner=self.get_partner())
                except ObjectDoesNotExist:
                    driver = Driver.objects.create(name=kwargs['name'],
                                                   second_name=kwargs['second_name'],
                                                   phone_number=kwargs['phone_number'],
                                                   email=kwargs['email'],
                                                   role=Role.DRIVER,
                                                   partner=self.get_partner())
                    try:
                        client = JobApplication.objects.get(first_name=kwargs['name'], last_name=kwargs['second_name'])
                        driver.chat_id = client.chat_id
                        driver.save()
                    except ObjectDoesNotExist:
                        pass
        return driver

    def get_or_create_vehicle(self, **kwargs):
        licence_plate, unk, v_name, vin = kwargs['licence_plate'], 'Unknown car', 'vehicle_name', 'vin_code'
        if not licence_plate:
            licence_plate = unk
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate, partner=self.get_partner())
        except ObjectDoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs[v_name].upper(),
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
    def start_report_interval(day):
        return datetime.datetime.combine(day, datetime.time.min)

    @staticmethod
    def end_report_interval(day):
        return datetime.datetime.combine(day, datetime.time.max)

    @staticmethod
    def parameters() -> dict:
        params = {
            'limit': '50',
            'offset': '0',
        }
        return params

    def r_dup(self, text):
        if 'DUP' in text:
            return text[:-3]
        return text


