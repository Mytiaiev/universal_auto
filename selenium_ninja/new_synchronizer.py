import redis
import requests
import pendulum
import os


class Synchronizer_V2:
    variables = ('token', 'type')

    def __init__(self, fleet=None, park_id=1, connect=redis.Redis.from_url(os.environ["REDIS_URL"]),
                 session=requests.Session(), day=True) -> None:
        self.id = park_id
        self.session = session
        self.redis = connect
        self.day = day
        self.fleet = fleet

    def get_partner(self) -> object:
        park = Park.objects.select_related('partner').get(pk=self.id)
        return park.partner.pk

    def interval(self) -> pendulum.DateTime:
        if self.day:
            return pendulum.now().start_of('day').subtract(days=1)
        return pendulum.now().start_of('week').subtract(days=4)

    def start(self) -> pendulum.DateTime:
        if self.day:
            return self.interval().start_of("day")
        return self.interval().start_of('week')

    def end(self) -> pendulum.DateTime:
        if self.day:
            return self.interval().end_of("day")
        return self.interval().end_of('week')

    def parameters(self) -> dict:
        params = {
            'limit': '50',
            'offset': '0',
        }
        return params

    def get_drivers_table(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for driver in drivers:
            self.create_driver(**driver)

    def create_driver(self, **kwargs):
        pay_cash, id, fleet_ = 'pay_cash', 'driver_external_id', 'fleet_name'
        try:
            fleet = Fleet.objects.get(name=kwargs[fleet_])
        except Fleet.DoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs[id],
                                                              partner=self.get_partner())
        if not drivers:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs[id],
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

    def update_driver_fields(self, driver, **kwargs):
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

    def update_vehicle_fields(self, vehicle, **kwargs):
        key_vehicle_name, key_vin = 'vehicle_name',  'vin_code'
        update_fields, vehicle_name, vin_code = [], kwargs[key_vehicle_name], kwargs[key_vin]

        if vehicle.name != vehicle_name and vehicle_name:
            vehicle.name = vehicle_name
            update_fields.append(key_vehicle_name[-4:])
        elif vehicle.vin_code != vin_code and vin_code:
            vehicle.vin_code = vin_code
            update_fields.append(key_vin)
        elif update_fields:
            vehicle.save(update_fields=update_fields)

    def get_or_create_vehicle(self, **kwargs):
        licence_plate, unk, v_name, vin = kwargs['licence_plate'], 'Unknown car', 'vehicle_name', 'vin_code'
        if not licence_plate:
            licence_plate = unk
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate, partner=self.get_partner())
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

    def get_or_create_driver(self, **kwargs):
        name, s_name, phone, email = 'name', 'second_name', 'phone_number', 'email'
        try:
            driver = Driver.objects.get(name=kwargs[name],
                                        second_name=kwargs[s_name],
                                        partner=self.get_partner())
        except Driver.DoesNotExist:
            driver = Driver.objects.create(
                name=kwargs[name],
                second_name=kwargs[s_name],
                phone_number=kwargs[phone],
                email=kwargs[email],
                partner=self.get_partner()
            )
            driver.save()
        return driver

    def validate_phone_number(self, phone_number):
        return ''.join([x for x in phone_number if x.isdigit() or x == '+'][:13])