from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from scripts.redis_conn import redis_instance, get_logger
from app.models import Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Role, JobApplication, Partner
import datetime


class Synchronizer:

    def __init__(self, partner_id, fleet='Uklon'):
        self.partner_id = partner_id
        self.fleet = fleet
        self.redis = redis_instance
        self.logger = get_logger()

    def get_drivers_table(self):
        raise NotImplementedError

    def get_vehicles(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for driver in drivers:
            self.create_driver(**driver)

    def create_driver(self, **kwargs):
        try:
            fleet = Fleet.objects.get(name=kwargs['fleet_name'])
        except ObjectDoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs['driver_external_id'],
                                                              partner=self.partner_id)
        if not drivers:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs['driver_external_id'],
                pay_cash=kwargs['pay_cash'],
                partner=Partner.get_partner(self.partner_id),
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

    @staticmethod
    def get_driver_by_name(name, second_name, partner):
        try:
            return Driver.objects.get(name=name, second_name=second_name, partner=partner)
        except MultipleObjectsReturned:
            return Driver.objects.filter(name=name, second_name=second_name, partner=partner)[0]

    @staticmethod
    def get_driver_by_phone_or_email(phone_number, email, partner):
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
                                             partner=self.partner_id)
        except ObjectDoesNotExist:
            try:
                driver = self.get_driver_by_name(kwargs['second_name'],
                                                 kwargs['name'],
                                                 partner=self.partner_id)
            except ObjectDoesNotExist:
                try:
                    driver = self.get_driver_by_phone_or_email(kwargs['phone_number'],
                                                               kwargs['email'],
                                                               partner=self.partner_id)
                except ObjectDoesNotExist:
                    driver = Driver.objects.create(name=kwargs['name'],
                                                   second_name=kwargs['second_name'],
                                                   phone_number=kwargs['phone_number'],
                                                   email=kwargs['email'],
                                                   role=Role.DRIVER,
                                                   partner=Partner.get_partner(self.partner_id))
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
            vehicle = Vehicle.objects.get(licence_plate=licence_plate)
        except ObjectDoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs[v_name].upper(),
                licence_plate=licence_plate,
                vin_code=kwargs[vin],
                partner=Partner.get_partner(self.partner_id)
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

    @staticmethod
    def r_dup(text):
        if 'DUP' in text:
            return text[:-3]
        return text
