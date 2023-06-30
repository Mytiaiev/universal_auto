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
        try:
            fleet = Fleet.objects.get(name=kwargs['fleet_name'])
        except Fleet.DoesNotExist:
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

    def update_driver_fields(self, driver, **kwargs): #+
        key_phone, key_email = 'phone_number', 'email'
        update_fields, phone_number, email = [], kwargs[key_phone], kwargs[key_email]

        if driver.phone_number != phone_number and phone_number:
            driver.phone_number = phone_number
            update_fields.append(key_phone)
        elif driver.email != email and email:
            driver.email = email
            update_fields.append(key_email)
        elif update_fields:
            driver.save(update_fields=update_fields)

    def update_vehicle_fields(self, vehicle, **kwargs): #+
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


    def get_or_create_vehicle(self, **kwargs): #+
        licence_plate = kwargs['licence_plate']
        if not licence_plate:
            licence_plate = 'Unknown car'
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate, partner=self.get_partner())
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs['vehicle_name'].upper(),
                model='',
                type='',
                licence_plate=licence_plate,
                vin_code=kwargs['vin_code'],
                partner=self.get_partner()
            )
            vehicle.save()
        return vehicle

    def get_driver_by_name(self, name, second_name): #+
        try:
            return Driver.objects.get(name=name, second_name=second_name, partner=self.get_partner())
        except Driver.MultipleObjectsReturned:
            return Driver.objects.filter(name=name, second_name=second_name, partner=self.get_partner())[0]

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

    def validate_phone_number(self, phone_number):
        return ''.join([x for x in phone_number if x.isdigit() or x == '+'][:13])