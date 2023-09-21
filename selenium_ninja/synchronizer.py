from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.utils import timezone

from scripts.redis_conn import redis_instance, get_logger
from app.models import Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Role, JobApplication, Partner, \
    DriverReshuffle
import datetime


class Synchronizer:

    def __init__(self, partner_id, fleet='Uklon'):
        self.partner_id = partner_id
        self.fleet = fleet
        self.redis = redis_instance()
        self.logger = get_logger()

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
        drivers, created = Fleets_drivers_vehicles_rate.objects.get_or_create(
                fleet=fleet,
                driver_external_id=kwargs['driver_external_id'],
                defaults={
                        "fleet": fleet,
                        "driver_external_id": kwargs['driver_external_id'],
                        "driver": self.get_or_create_driver(**kwargs),
                        "pay_cash": kwargs['pay_cash'],
                        "partner": Partner.get_partner(self.partner_id)})

        if not created:
            drivers.partner = Partner.get_partner(self.partner_id)
            drivers.pay_cash = kwargs["pay_cash"]
            drivers.save(update_fields=['pay_cash', 'partner'])

    def get_or_create_driver(self, **kwargs):
        name = self.r_dup(kwargs['name'])
        second_name = self.r_dup(kwargs['second_name'])
        driver = Driver.objects.filter((Q(name=name, second_name=second_name) |
                                        Q(name=second_name, second_name=name) |
                                        Q(phone_number__icontains=kwargs['phone_number'][-10:])
                                        ) & Q(partner=self.partner_id)).first()
        if not driver and kwargs['email']:
            driver = Driver.objects.filter(email__icontains=kwargs['email']).first()
            if not driver:
                driver = Driver.objects.create(name=name,
                                               second_name=second_name,
                                               phone_number=kwargs['phone_number']
                                               if len(kwargs['phone_number']) <= 13 else None,
                                               email=kwargs['email'],
                                               vehicle=self.get_or_create_vehicle(**kwargs),
                                               role=Role.DRIVER,
                                               partner=Partner.get_partner(self.partner_id))
            try:
                client = JobApplication.objects.get(first_name=kwargs['name'], last_name=kwargs['second_name'])
                driver.chat_id = client.chat_id
                driver.save()
                fleet = Fleet.objects.get(name='Ninja')
                Fleets_drivers_vehicles_rate.objects.get_or_create(fleet=fleet,
                                                                   driver_external_id=driver.chat_id,
                                                                   driver=driver,
                                                                   partner=Partner.get_partner(self.partner_id))
            except ObjectDoesNotExist:
                pass
        else:
            self.update_driver_fields(driver, **kwargs)
        return driver

    def get_or_create_vehicle(self, **kwargs):
        licence_plate, v_name, vin = kwargs['licence_plate'], kwargs['vehicle_name'], kwargs['vin_code']

        if licence_plate:
            vehicle, created = Vehicle.objects.get_or_create(licence_plate=licence_plate,
                                                             defaults={
                                                                  "name": v_name.upper(),
                                                                  "licence_plate": licence_plate,
                                                                  "vin_code": vin,
                                                                  "partner": Partner.get_partner(self.partner_id)
                                                             })
            if not created:
                self.update_vehicle_fields(vehicle, **kwargs)
            return vehicle

    def update_vehicle_fields(self, vehicle, **kwargs):
        vehicle_name = kwargs.get('vehicle_name')
        vin_code = kwargs.get('vin_code')

        if vehicle_name and vehicle.name != vehicle_name:
            vehicle.name = vehicle_name

        if vin_code and vehicle.vin_code != vin_code:
            vehicle.vin_code = vin_code

        vehicle.partner = Partner.get_partner(self.partner_id)
        vehicle.save()

    def update_driver_fields(self, driver, **kwargs):
        yesterday = timezone.localtime() - datetime.timedelta(days=1)
        phone_number = kwargs.get('phone_number')
        email = kwargs.get('email')
        worked = kwargs.get('worked')
        reshuffle = DriverReshuffle.objects.filter(swap_vehicle=driver.vehicle,
                                                   swap_time__date=yesterday.date())
        vehicle = None if reshuffle else self.get_or_create_vehicle(**kwargs)
        if reshuffle or driver.vehicle != vehicle:
            driver.vehicle = vehicle
        if phone_number and not driver.phone_number:
            driver.phone_number = phone_number

        if email and driver.email != email:
            driver.email = email

        driver.worked = worked
        driver.save()

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
            text = text[:-3]
        return text
