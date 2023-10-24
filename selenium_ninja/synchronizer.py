from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from scripts.redis_conn import redis_instance, get_logger
from app.models import Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Role, JobApplication, Partner, \
    DriverReshuffle, Schema, UberSession
import datetime


class AuthenticationError(Exception):
    def __init__(self, message="Authentication error"):
        self.message = message
        super().__init__(self.message)


class InfinityTokenError(Exception):
    def __init__(self, message="No infinity gps token"):
        self.message = message
        super().__init__(self.message)


class Synchronizer:

    def __init__(self, partner_id, fleet):
        self.partner_id = partner_id
        self.fleet = fleet
        self.session = UberSession.objects.filter(partner=self.partner_id).latest('created_at')
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
        driver = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                             driver_external_id=kwargs['driver_external_id'],
                                                             partner=self.partner_id).first()
        if not driver:
            Fleets_drivers_vehicles_rate.objects.create(fleet=fleet,
                                                        driver_external_id=kwargs['driver_external_id'],
                                                        driver=self.get_or_create_driver(**kwargs),
                                                        pay_cash=kwargs['pay_cash'],
                                                        partner=Partner.get_partner(self.partner_id))
        else:
            self.update_driver_fields(driver.driver, **kwargs)
            driver.pay_cash = kwargs["pay_cash"]
            driver.save(update_fields=['pay_cash'])

    def get_or_create_driver(self, **kwargs):
        partner = Partner.get_partner(self.partner_id)
        driver = Driver.objects.filter((Q(name=kwargs['name'], second_name=kwargs['second_name']) |
                                        Q(name=kwargs['second_name'], second_name=kwargs['name']) |
                                        Q(phone_number__icontains=kwargs['phone_number'][-10:])
                                        ) & Q(partner=self.partner_id)).first()
        if not driver and kwargs['email']:
            driver = Driver.objects.filter(email__icontains=kwargs['email']).first()
        if not driver:
            data = {"name": kwargs['name'],
                    "second_name": kwargs['second_name'],
                    "role": Role.DRIVER,
                    "schema": Schema.get_half_schema_id(),
                    "partner": partner
                    }
            if partner.contacts:
                phone_number = kwargs['phone_number'] if len(kwargs['phone_number']) <= 13 else None
                data.update({"phone_number": phone_number,
                             "email": kwargs['email']
                             })
            driver = Driver.objects.create(**data)
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
        swap_vehicle = Vehicle.objects.filter(licence_plate=kwargs['licence_plate']).first()
        reshuffle = DriverReshuffle.objects.filter(swap_vehicle=swap_vehicle,
                                                   swap_time__date=yesterday.date())
        if reshuffle:
            Driver.objects.filter(vehicle=swap_vehicle).update(vehicle=None)
        if driver.partner.contacts:
            if phone_number and not driver.phone_number:
                driver.phone_number = phone_number

            if email and driver.email != email:
                driver.email = email

        driver.worked = worked
        driver.save()

    @staticmethod
    def report_interval(day, start=None):
        report_time = datetime.time.min if start else datetime.time.max
        return int(datetime.datetime.combine(day, report_time).timestamp())
