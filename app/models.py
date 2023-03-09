import csv
import datetime
import glob
import os
import shutil
import sys


from django.db import models, IntegrityError
from django.db.models import Sum, QuerySet
from django.db.models.base import ModelBase
from polymorphic.models import PolymorphicModel
from selenium.common import TimeoutException, WebDriverException


class PaymentsOrder(models.Model):

    class Meta:
        verbose_name = 'Payments order'
        verbose_name_plural = 'Payments order'

    transaction_uuid = models.UUIDField()
    driver_uuid = models.UUIDField()
    driver_name = models.CharField(max_length=30)
    driver_second_name = models.CharField(max_length=30)
    trip_uuid = models.CharField(max_length=255)
    trip_description = models.CharField(max_length=50)
    organization_name = models.CharField(max_length=50)
    organization_nickname = models.CharField(max_length=50)
    transaction_time = models.DateTimeField()
    paid_to_you = models.DecimalField(decimal_places=2, max_digits=10)
    your_earnings = models.DecimalField(decimal_places=2, max_digits=10)
    cash = models.DecimalField(decimal_places=2, max_digits=10)
    fare = models.DecimalField(decimal_places=2, max_digits=10)
    tax = models.DecimalField(decimal_places=2, max_digits=10)
    fare2 = models.DecimalField(decimal_places=2, max_digits=10)
    service_tax = models.DecimalField(decimal_places=2, max_digits=10)
    wait_time = models.DecimalField(decimal_places=2, max_digits=10)
    out_of_city = models.DecimalField(decimal_places=2, max_digits=10)
    tips = models.DecimalField(decimal_places=2, max_digits=10)
    transfered_to_bank = models.DecimalField(decimal_places=2, max_digits=10)
    ajustment_payment = models.DecimalField(decimal_places=2, max_digits=10)
    cancel_payment = models.DecimalField(decimal_places=2, max_digits=10)


class GenericPaymentsOrder(ModelBase):

    _registry = {}

    def __new__(cls, name, bases, attrs):

        if attrs.get('vendor_name') is None:
            raise NotImplementedError(f'vendor_name must be implemented in {name}')
        try:
            if not callable(getattr(attrs.get('Scopes'), 'filter_by_driver_external_id')):
                raise NotImplementedError(f'{name}.Scopes.filter_by_driver_external_id() must be callable')
        except AttributeError:
            raise NotImplementedError(f'{name}.Scopes.filter_by_driver_external_id() must be implemented')

        scopes_bases = filter(None, [attrs.get('Scopes')] +
                              [getattr(b, 'Scopes', None) for b in bases])

        attrs['Scopes'] = type('ScopesFor' + name, tuple(scopes_bases), {})

        ScopedQuerySet = type('ScopedQuerySetFor' + name, (QuerySet, attrs['Scopes']), {})
        ScopedManager = type('ScopedManagerFor' + name, (models.Manager, attrs['Scopes']), {
            'use_for_related_fields': True,
            'get_query_set': lambda self: ScopedQuerySet(self.model, using=self._db)
        })

        attrs['objects'] = ScopedManager()

        vendor_name_ = attrs.get('vendor_name')
        if vendor_name_ in cls._registry:
            raise ValueError(f'{vendor_name_} is already registered for {name}')

        new_cls = ModelBase.__new__(cls, name, bases, attrs)
        cls._registry[vendor_name_] = new_cls

        return new_cls

    @classmethod
    def filter_by_driver(cls, vendor, driver_external_id):
        if vendor in cls._registry:
            return cls._registry[vendor].objects.filter_by_driver_external_id(driver_external_id)
        else:
            raise NotImplementedError(f'{vendor} is not registered in {cls}')


class UklonPaymentsOrder(models.Model, metaclass=GenericPaymentsOrder):

    class Meta:
        verbose_name = 'Payments order: Uklon'
        verbose_name_plural = 'Payments order: Uklon'

    report_from = models.DateTimeField()
    report_to = models.DateTimeField()
    report_file_name = models.CharField(max_length=255)
    signal = models.CharField(max_length=8)
    licence_plate = models.CharField(max_length=8)
    total_rides = models.PositiveIntegerField()
    total_distance = models.PositiveIntegerField()
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10)
    total_amount_cach_less = models.DecimalField(decimal_places=2, max_digits=10)
    total_amount = models.DecimalField(decimal_places=2, max_digits=10)
    total_amount_without_comission = models.DecimalField(decimal_places=2, max_digits=10)
    bonuses = models.DecimalField(decimal_places=2, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    vendor_name = 'Uklon'

    class Scopes:
        def filter_by_driver_external_id(self, driver_external_id):
            return self.filter(signal=driver_external_id)

    class Meta:
        unique_together = (('report_from', 'report_to', 'licence_plate', 'signal'))

    def driver_id(self):
        return self.signal

    def report_text(self, name=None, rate=0.35):
        return f'Uklon {name} {self.signal}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные(-{"%.2f" % float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate=0.35):
        return -(self.kassa()) * rate

    def vendor(self):
        return 'uklon'

    def total_owner_amount(self, rate=0.35):
        return -self.total_drivers_amount(rate)

    def kassa(self):
        return float(self.total_amount) * 0.81


class NewUklonPaymentsOrder(models.Model, metaclass=GenericPaymentsOrder):

    class Meta:
        verbose_name = 'Payments order: NewUklon'
        verbose_name_plural = 'Payments order: NewUklon'

    report_from = models.DateTimeField()
    report_to = models.DateTimeField()
    report_file_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255) # "Водій"
    signal = models.CharField(max_length=8) # "Позивний"
    total_rides = models.PositiveIntegerField() # "Кількість поїздок"
    total_distance = models.DecimalField(decimal_places=2, max_digits=10) # "Пробіг під замовленнями, км"
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10) # "Готівкою, грн"
    total_amount_cach_less = models.DecimalField(decimal_places=2, max_digits=10) # "На гаманець, грн"
    total_amount_on_card = models.DecimalField(decimal_places=2, max_digits=10)   # "На картку, грн"
    total_amount = models.DecimalField(decimal_places=2, max_digits=10) # "Всього, грн"
    tips = models.DecimalField(decimal_places=2, max_digits=10) # "Чайові, грн"
    bonuses = models.DecimalField(decimal_places=2, max_digits=10) # "Бонуси, грн"
    fares = models.DecimalField(decimal_places=2, max_digits=10) # "Штрафи, грн"
    comission  = models.DecimalField(decimal_places=2, max_digits=10) # "Комісія Уклон, грн"
    total_amount_without_comission = models.DecimalField(decimal_places=2, max_digits=10) #" Разом, грн"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    vendor_name = 'NewUklon'

    class Scopes:
        def filter_by_driver_external_id(self, driver_external_id):
            return self.filter(signal=driver_external_id)

    class Meta:
        unique_together = (('report_from', 'report_to', 'full_name', 'signal'))

    def driver_id(self):
        return self.signal

    def report_text(self, name=None, rate=0.35):
        return f'New Uklon {self.full_name} {self.signal}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные(-{"%.2f" % float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate=0.35):
        return -(self.kassa()) * rate

    def vendor(self):
        return 'new_uklon'

    def total_drivers_amount(self, rate=0.35):
        if self.signal == '512329' or self.signal == '542114' or self.signal == '517489':
            return self.kassa() * (1 - rate) - float(self.total_amount_cach)
        else:
            return -(self.kassa()) * rate


    def total_owner_amount(self, rate=0.35):
        return -self.total_drivers_amount(rate)

    def kassa(self, fleet_rate=0.81):
        return float(self.total_amount) * fleet_rate + float(self.tips) + float(self.bonuses)


class BoltPaymentsOrder(models.Model, metaclass=GenericPaymentsOrder):

    class Meta:
        verbose_name = 'Payments order: Bolt'
        verbose_name_plural = 'Payments order: Bolt'

    report_from = models.DateTimeField()
    report_to = models.DateTimeField()
    report_file_name = models.CharField(max_length=255)
    driver_full_name = models.CharField(max_length=24)
    mobile_number = models.CharField(max_length=24)
    range_string = models.CharField(max_length=50)
    total_amount = models.DecimalField(decimal_places=2, max_digits=10)
    cancels_amount = models.DecimalField(decimal_places=2, max_digits=10)
    autorization_payment = models.DecimalField(decimal_places=2, max_digits=10)
    autorization_deduction = models.DecimalField(decimal_places=2, max_digits=10)
    additional_fee = models.DecimalField(decimal_places=2, max_digits=10)
    fee = models.DecimalField(decimal_places=2, max_digits=10)
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10)
    discount_cash_trips = models.DecimalField(decimal_places=2, max_digits=10)
    driver_bonus = models.DecimalField(decimal_places=2, max_digits=10)
    compensation = models.DecimalField(decimal_places=2, max_digits=10)
    refunds = models.DecimalField(decimal_places=2, max_digits=10)
    tips = models.DecimalField(decimal_places=2, max_digits=10)
    weekly_balance = models.DecimalField(decimal_places=2, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    vendor_name = 'Bolt'

    class Scopes:
        def filter_by_driver_external_id(self, driver_external_id):
            return self.filter(mobile_number=driver_external_id)

    class Meta:
        unique_together = (('report_from', 'report_to', 'driver_full_name', 'mobile_number'))

    def driver_id(self):
        return self.mobile_number

    def report_text(self, name=None, rate=0.65):
        name = name or self.full_name()
        return f'Bolt {name}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные({"%.2f" % float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate=0.65):
        res = self.total_cach_less_drivers_amount() * rate + float(self.total_amount_cach)
        return res

    def total_cach_less_drivers_amount(self):
        return float(self.total_amount) + float(self.fee) + float(self.cancels_amount) + float(self.driver_bonus) + float(self.autorization_payment) + float(self.tips)

    def vendor(self):
        return 'bolt'

    def kassa(self):
        return (self.total_cach_less_drivers_amount())

    def total_owner_amount(self, rate=0.65):
        return self.total_cach_less_drivers_amount() * (1 - rate) - self.total_drivers_amount(rate)


class UberPaymentsOrder(models.Model, metaclass=GenericPaymentsOrder):

    class Meta:
        verbose_name = 'Payments order: Uber'
        verbose_name_plural = 'Payments order: Uber'

    report_from = models.DateTimeField()
    report_to = models.DateTimeField()
    report_file_name = models.CharField(max_length=255)
    driver_uuid = models.UUIDField()
    first_name = models.CharField(max_length=24)
    last_name = models.CharField(max_length=24)
    total_amount = models.DecimalField(decimal_places=2, max_digits=10)
    total_clean_amout = models.DecimalField(decimal_places=2, max_digits=10)
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10)
    transfered_to_bank = models.DecimalField(decimal_places=2, max_digits=10)
    returns = models.DecimalField(decimal_places=2, max_digits=10)
    tips = models.DecimalField(decimal_places=2, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    vendor_name = 'Uber'

    class Scopes:
        def filter_by_driver_external_id(self, driver_external_id):
            return self.filter(driver_uuid=driver_external_id)

    class Meta:
        unique_together = (('report_from', 'report_to', 'driver_uuid'))

    def driver_id(self):
        return self.driver_uuid

    def report_text(self, name=None, rate=0.65):
        name = name or self.full_name()
        return f'Uber {name}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные({float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate=0.65):
       return float(self.total_amount) * rate + float(self.total_amount_cach)

    def vendor(self):
        return 'uber'

    def total_owner_amount(self, rate=0.65):
        return float(self.total_amount) * (1 - rate) - self.total_drivers_amount(rate)

    def kassa(self):
        return float(self.total_amount)


class FileNameProcessed(models.Model):
    filename_weekly = models.CharField(max_length=150, unique=True)

    @staticmethod
    def save_filename_to_db(processed_files: list):
        for name in processed_files:

            order = FileNameProcessed(
                filename_weekly=name)

            order.save()


class User(models.Model):
    class Role(models.TextChoices):
        CLIENT = 'CLIENT', 'Client'
        PARTNER = 'PARTNER', 'Partner'
        DRIVER = 'DRIVER', 'Driver'
        DRIVER_MANAGER = 'DRIVER_MANAGER', 'Driver manager'
        SERVICE_STATION_MANAGER = 'SERVICE_STATION_MANAGER', 'Service station manager'
        SUPPORT_MANAGER = 'SUPPORT_MANAGER', 'Support manager'
        OWNER = 'OWNER', 'Owner'

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ім'я")
    second_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Прізвище')
    email = models.EmailField(blank=True, max_length=254, verbose_name='Електрона пошта')
    phone_number = models.CharField(blank=True, max_length=13, verbose_name='Номер телефона')
    chat_id = models.CharField(blank=True, max_length=100, verbose_name='Індетифікатор чата')
    created_at = models.DateTimeField(editable=False, auto_now=datetime.datetime.now(), verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'

    def __str__(self) -> str:
        return self.full_name()

    def full_name(self):
        return f'{self.name} {self.second_name}'

    @staticmethod
    def get_by_chat_id(chat_id):
        """
        Returns user by chat_id
        :param chat_id: chat_id by which we need to find the user
        :type chat_id: str
        :return: user object or None if a user with such ID does not exist
        """
        try:
            user = User.objects.get(chat_id=chat_id)
            return user
        except User.DoesNotExist:
            return None


    @staticmethod
    def fill_deleted_at_by_number(number):
        """
        :param number: a number of a user to fill deleted_at
        :type number: str
        """
        user = User.objects.filter(phone_number=number).first()
        user.deleted_at = datetime.datetime.now()
        user.save()
        return user

    @staticmethod
    def name_and_second_name_validator(name) -> str:
        """This func validator for name and second name"""
        if len(name) <= 255:
            return name.title()
        else:
            return None

    @staticmethod
    def email_validator(email) -> str:
        pattern = r"^([a-zA-Z0-9]+\.?[a-zA-Z0-9]+)+@([a-zA-Z0-9]+\.)+[a-zA-Z0-9]{2,4}$"
        if re.match(pattern, email) is not None:
            return email
        else:
            return None

    @staticmethod
    def phone_number_validator(phone_number) -> str:

        pattern = r"^(\+380|380|80|0)+\d{9}$"
        if re.match(pattern, phone_number) is not None:
            if len(phone_number) == 13:
                return phone_number
            elif len(phone_number) == 10:
                valid_phone_number = f'+38{phone_number}'
                return valid_phone_number
            elif len(phone_number) == 12:
                valid_phone_number = f'+{phone_number}'
                return valid_phone_number
            elif len(phone_number) == 11:
                valid_phone_number = f'+3{phone_number}'
                return valid_phone_number
        else:
            return None


class Driver(User):
    ACTIVE = 'Готовий прийняти заказ'
    WITH_CLIENT = 'В дорозі'
    WAIT_FOR_CLIENT = 'Очікую клієнта'
    OFFLINE = 'Не працюю'

    fleet = models.OneToOneField('Fleet', blank=True, null=True, on_delete=models.SET_NULL)
    #driver_manager_id: ManyToManyField already exists in DriverManager
    #we have to delete this
    driver_manager_id = models.ManyToManyField('DriverManager', blank=True)
    #partner = models.ManyToManyField('Partner', blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.DRIVER)
    driver_status = models.CharField(max_length=35, null=False, default='Offline', verbose_name='Статус водія')

    class Meta:
        verbose_name = 'Водій'
        verbose_name_plural = 'Водії'

    def get_driver_external_id(self, vendor: str) -> str:
        try:
            return Fleets_drivers_vehicles_rate.objects.get(fleet__name=vendor, driver=self, deleted_at=None).driver_external_id
        except Fleets_drivers_vehicles_rate.DoesNotExist:
            return ''

    def get_rate(self, vendor: str) -> float:
        try:
            return float(Fleets_drivers_vehicles_rate.objects.get(fleet__name=vendor.capitalize(), driver=self, deleted_at=None).rate)
        except Fleets_drivers_vehicles_rate.DoesNotExist:
            return 0

    def get_kassa(self, vendor: str, week_number: [str, None] = None) -> float:
        driver_external_id = self.get_driver_external_id(vendor)
        st = SeleniumTools(session='', week_number=week_number)
        qset = GenericPaymentsOrder.filter_by_driver(vendor, driver_external_id)\
            .filter(report_from__lte=st.end_of_week(), report_to__gte=st.start_of_week())
        return sum(map(lambda x: x.kassa(), qset))

    def get_dynamic_rate(self, vendor: str, week_number: [str, None] = None, kassa: float = None) -> float:
        if kassa is None:
            kassa = self.get_kassa(vendor, week_number)
        dct = DriverRateLevels.objects.filter(fleet__name=vendor, threshold_value__gte=kassa,
                                              deleted_at=None).aggregate(Sum('rate_delta'))
        rate = self.get_rate(vendor) + float(dct['rate_delta__sum'] if dct['rate_delta__sum'] is not None else 0)
        return max(rate, 0)

    def get_salary(self, vendor: str, week_number: [str, None] = None) -> float:
        try:
            min_fee = float(Fleet.objects.get(name=vendor).min_fee)
        except Fleet.DoesNotExist:
            min_fee = 0
        kassa = self.get_kassa(vendor, week_number)
        rate = self.get_dynamic_rate(vendor, week_number, kassa)
        salary = kassa * rate
        print(kassa, rate, salary, min(salary, max(kassa - min_fee, 0)))
        return min(salary, max(kassa - min_fee, 0))

    def __str__(self) -> str:
        return f'{self.name} {self.second_name}'


    @staticmethod
    def save_driver_status(status):
        driver = Driver.objects.create(driver_status=status)
        driver.save()

    @staticmethod
    def get_by_chat_id(chat_id):
        """
        Returns user by chat_id
        :param chat_id: chat_id by which we need to find the driver
        :type chat_id: str
        :return: driver object or None if a driver with such ID does not exist
        """
        try:
            driver = Driver.objects.get(chat_id=chat_id)
            return driver
        except Driver.DoesNotExist:
            return None



class Fleet(PolymorphicModel):
    name = models.CharField(max_length=255)
    fees = models.DecimalField(decimal_places=2, max_digits=3, default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    min_fee = models.DecimalField(decimal_places=2, max_digits=15, default=0)

    class Meta:
        verbose_name = 'Автопарк'
        verbose_name_plural = 'Автопарки'

    def __str__(self) -> str:
        return f'{self.name}'


class Client(User):
    #support_manager_id: ManyToManyField already exists in SupportManager
    #we have to delete this
    support_manager_id = models.ManyToManyField('SupportManager',  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.CLIENT)

    class Meta:
        verbose_name = 'Клієнт'
        verbose_name_plural = 'Клієнти'

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            client = Client.objects.get(chat_id=chat_id)
            return client
        except Client.DoesNotExist:
            return None


# class Partner(User):
#     fleet = models.OneToOneField(Fleet,  blank=True, null=True, on_delete=models.SET_NULL)
#     driver = models.ManyToManyField(Driver,  blank=True)
#     role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.PARTNER)


class DriverManager(User):
    driver_id = models.ManyToManyField(Driver, null=True, blank=True, verbose_name='Driver')
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.DRIVER_MANAGER)

    class Meta:
        verbose_name ='Менеджер водія'
        verbose_name_plural = 'Менеджер водіїв'

    def __str__(self):
        return f'{self.name} {self.second_name}'

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            driver_manager = DriverManager.objects.get(chat_id=chat_id)
            return driver_manager
        except DriverManager.DoesNotExist:
            return None


class ServiceStationManager(User):
    car_id = models.ManyToManyField('Vehicle', blank=True)
    fleet_id = models.ManyToManyField(Fleet, blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.SERVICE_STATION_MANAGER)
    service_station = models.OneToOneField('ServiceStation', on_delete=models.RESTRICT, verbose_name='Сервісний центр')

    class Meta:
        verbose_name ='Менеджер сервісного центра'
        verbose_name_plural = 'Менеджери сервісних центрів'

    def __str__(self):
        return self.full_name()


    @staticmethod
    def save_name_of_service_station(name_of_service_station):
        service = ServiceStationManager.objects.create(name_of_service_station=name_of_service_station)
        service.save()

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            manager = ServiceStationManager.objects.get(chat_id=chat_id)
            return manager
        except ServiceStationManager.DoesNotExist:
            return None


class SupportManager(User):
    client_id = models.ManyToManyField(Client,  blank=True)
    driver_id = models.ManyToManyField(Driver,  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.SUPPORT_MANAGER)

    class Meta:
        verbose_name ='Менеджер служби підтримки'
        verbose_name_plural = 'Менеджери служби підтримки'

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            support_manager = SupportManager.objects.get(chat_id=chat_id)
            return support_manager
        except SupportManager.DoesNotExist:
            return None


class Owner(User):
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.OWNER)

    class Meta:
        verbose_name ='Власник'
        verbose_name_plural = 'Власники'

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            owner = Owner.objects.get(chat_id=chat_id)
            return owner
        except Owner.DoesNotExist:
            return None


class UberFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return Uber.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

    def download_daily_report(self, day=None, driver=True, sleep=5, headless=True):
        pass


class BoltFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return Bolt.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

    def download_daily_report(self, day=None, driver=True, sleep=5, headless=True):
        """the same method as weekly report. it gets daily report if day is non None"""
        if day == pendulum.now().start_of('day'):
            return None  # do if you need to get today report
        period = pendulum.now() - day
        if period.in_days() > 30:
            return None  # do if you need to get report elder then 30 days

        return Bolt.download_weekly_report(day=day, driver=driver, sleep=sleep, headless=headless)


class UklonFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return Uklon.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

    def download_daily_report(self, day=None, driver=True, sleep=5, headless=True):
        """the same method as weekly report. it gets daily report if day is non None"""
        return Uklon.download_weekly_report(day=day, driver=driver, sleep=sleep, headless=headless)


class NewUklonFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return NewUklon.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

    def download_daily_report(self, day=None, driver=True, sleep=5, headless=True):
        return NewUklon.download_daily_report(day=day, driver=driver, sleep=sleep, headless=headless)


class Vehicle(models.Model):
    ELECTRO = 'Електро'

    name = models.CharField(max_length=255, verbose_name='Назва')
    model = models.CharField(max_length=50, verbose_name='Модель')
    type = models.CharField(max_length=20, default=ELECTRO, verbose_name='Тип')
    licence_plate = models.CharField(max_length=24, unique=True, verbose_name='Номерний знак')
    vin_code = models.CharField(max_length=17)
    gps_imei = models.CharField(max_length=100, default='')
    car_status = models.CharField(max_length=18, null=False, default="Serviceable", verbose_name='Статус автомобіля')
    driver = models.ForeignKey(Driver, null=True, on_delete=models.RESTRICT, verbose_name='Водій')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name ='Автомобіль'
        verbose_name_plural = 'Автомобілі'

    def __str__(self) -> str:
        return f'{self.licence_plate}'

    @staticmethod
    def get_by_numberplate(licence_plate):
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate)
            return vehicle
        except Vehicle.DoesNotExist:
            pass

    @staticmethod
    def name_validator(name):
        if len(name) <= 255:
            return name.title()
        else:
            return None

    @staticmethod
    def model_validator(model):
        if len(model) <= 50:
            return model.title()
        else:
            return None

    @staticmethod
    def licence_plate_validator(licence_plate):
        if len(licence_plate) <= 24:
            return licence_plate.upper()
        else:
            return None

    @staticmethod
    def vin_code_validator(vin_code):
        if len(vin_code) <= 17:
            return vin_code.upper()
        else:
            return None


class Fleets_drivers_vehicles_rate(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver_external_id = models.CharField(max_length=255)
    rate = models.DecimalField(decimal_places=2, max_digits=3, default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    pay_cash = models.BooleanField(default=False)
    withdraw_money = models.BooleanField(default=False)

    def __str__(self) -> str:
        return ''


class DriverRateLevels(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, verbose_name='Автопарк')
    threshold_value = models.DecimalField(decimal_places=2, max_digits=15, default=0)
    rate_delta = models.DecimalField(decimal_places=2, max_digits=3, default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Рівень рейтингу водія'
        verbose_name_plural = 'Рівень рейтингу водіїв'

class RawGPS(models.Model):
    imei = models.CharField(max_length=100)
    client_ip = models.CharField(max_length=100)
    client_port = models.IntegerField()
    data = models.CharField(max_length=1024)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    class Meta:
        verbose_name = 'GPS Raw'
        verbose_name_plural = 'GPS Raw'


class GPS(PolymorphicModel):
    date_time = models.DateTimeField(null=False)
    lat = models.DecimalField(decimal_places=4, max_digits=10, default=0)
    lat_zone = models.CharField(max_length=1)
    lon = models.DecimalField(decimal_places=4, max_digits=10, default=0)
    lon_zone = models.CharField(max_length=1)
    speed = models.IntegerField(default=0)
    course = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    def __str__(self):
        return f'{self.lat}{self.lat_zone}:{self.lon}{self.lon_zone}'


class VehicleGPS(GPS):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    raw_data = models.OneToOneField(RawGPS, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'GPS Vehicle'
        verbose_name_plural = 'GPS Vehicle'


class WeeklyReportFile(models.Model):
    organization_name = models.CharField(max_length=20)
    report_file_name = models.CharField(max_length=255, unique=True)
    report_from = models.CharField(max_length=10)
    report_to = models.CharField(max_length=10)
    file = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def transfer_reports_to_db(self, company_name, report_name, from_date, until_date, header, rows):
        self.organization_name = company_name
        self.report_file_name = report_name
        self.report_from = from_date
        self.report_to = until_date
        self.file = (header + rows)
        self.save()

    # Calculates the number of days in the report
    def check_full_data(self, start, end, file_name):
        start = datetime.strptime(start, '%Y-%m-%d').date()
        end = datetime.strptime(end, '%Y-%m-%d').date()
        difference = end - start
        if difference.days == 7:
            return True
        else:
            print(f"{file_name} include {difference.days} days of the week")
            return False

    # Help separate the date from file name
    def convert_file_name(self, split_symbol, name_list):
        converted_list = []
        for string in name_list:
            string = string.split(split_symbol)
            for part in string:
                converted_list.append(part)
        return converted_list

    def save_weekly_reports_to_db(self):

        for file in csv_list:
            rows = []
            try:
                with open(file, 'r') as report:
                    report_name = report.name
                    csvreader = csv.reader(report)
                    header = next(csvreader)
                    for row in csvreader:
                        rows.append(row)

                    # Checks Uber, Uklon and Bolt name in report and report dates; checks the number of days in
                    # the report. If days are less than seven, code issues a warning message and does not
                    # add file to the database.

                    if "payments_driver" in report.name:
                        company_name = "uber"
                        from_date = report.name[0:4] + '-' + report.name[4:6] + '-' + report.name[6:8]
                        until_date = report.name[9:13] + '-' + report.name[13:15] + '-' + report.name[15:17]
                        if self.check_full_data(start=from_date, end=until_date, file_name=report_name):
                            pass
                        else:
                            continue
                        WeeklyReportFile.transfer_reports_to_db(self=WeeklyReportFile(), company_name=company_name,
                                                                report_name=report_name, from_date=from_date,
                                                                until_date=until_date, header=header, rows=rows)

                    elif "Income" in report.name:
                        company_name = "uklon"
                        refactor_file_name = report.name.split(" ")
                        refactor_file_name = [refactor_file_name[2], refactor_file_name[4]]
                        refactor_file_name = self.convert_file_name('-', refactor_file_name)
                        refactor_file_name.pop(1)
                        refactor_file_name = self.convert_file_name('_', refactor_file_name)
                        refactor_file_name.pop(0)

                        # Adds a zero to a single digit
                        for date in refactor_file_name:
                            if len(date) == 1:
                                refactor_file_name[refactor_file_name.index(date)] = "0" + date

                        from_date = str(
                            refactor_file_name[2] + '-' + refactor_file_name[0] + '-' + refactor_file_name[1])
                        until_date = str(
                            refactor_file_name[-1] + '-' + refactor_file_name[-3] + '-' + refactor_file_name[-2])
                        if self.check_full_data(start=from_date, end=until_date, file_name=report_name):
                            pass
                        else:
                            continue
                        WeeklyReportFile.transfer_reports_to_db(self=WeeklyReportFile(), company_name=company_name,
                                                                report_name=report_name, from_date=from_date,
                                                                until_date=until_date, header=header, rows=rows)

                    elif "Bolt" in report.name:
                        company_name = "bolt"
                        bolt_date_report = rows[1][2]
                        from_date = bolt_date_report[8:18]
                        until_date = bolt_date_report[-10:]
                        if self.check_full_data(start=from_date, end=until_date, file_name=report_name):
                            pass
                        else:
                            continue
                        WeeklyReportFile.transfer_reports_to_db(self=WeeklyReportFile(), company_name=company_name,
                                                                report_name=report_name, from_date=from_date,
                                                                until_date=until_date, header=header, rows=rows)
                    else:
                        continue

            # Catches an error if the filename is already exist in DB
            except django.db.utils.IntegrityError as error:
                print(f"{report_name} already exists in Database")


class UberTransactions(models.Model):
    transaction_uuid = models.UUIDField(unique=True)
    driver_uuid = models.UUIDField()
    driver_name = models.CharField(max_length=50)
    driver_second_name = models.CharField(max_length=50)
    trip_uuid = models.UUIDField()
    trip_description = models.CharField(max_length=50)
    organization_name = models.CharField(max_length=50)
    organization_nickname = models.CharField(max_length=50)
    transaction_time = models.CharField(max_length=50)
    paid_to_you = models.DecimalField(decimal_places=2, max_digits=10)
    your_earnings = models.DecimalField(decimal_places=2, max_digits=10)
    cash = models.DecimalField(decimal_places=2, max_digits=10)
    fare = models.DecimalField(decimal_places=2, max_digits=10)
    tax = models.DecimalField(decimal_places=2, max_digits=10)
    fare2 = models.DecimalField(decimal_places=2, max_digits=10)
    service_tax = models.DecimalField(decimal_places=2, max_digits=10)
    wait_time = models.DecimalField(decimal_places=2, max_digits=10)
    transfered_to_bank = models.DecimalField(decimal_places=2, max_digits=10)
    peak_rate = models.DecimalField(decimal_places=2, max_digits=10)
    tips = models.DecimalField(decimal_places=2, max_digits=10)
    cancel_payment = models.DecimalField(decimal_places=2, max_digits=10)

    @staticmethod
    def save_transactions_to_db(file_name):
        with open(file_name, 'r', encoding='utf-8') as fl:
            reader = csv.reader(fl)
            next(reader)
            for row in reader:
                try:
                    transaction = UberTransactions(transaction_uuid=row[0],
                                                   driver_uuid=row[1],
                                                   driver_name=row[2],
                                                   driver_second_name=row[3],
                                                   trip_uuid=row[4],
                                                   trip_description=row[5],
                                                   organization_name=row[6],
                                                   organization_nickname=row[7],
                                                   transaction_time=row[8],
                                                   paid_to_you=row[9],
                                                   your_earnings=row[10],
                                                   cash=row[11],
                                                   fare=row[12],
                                                   tax=row[13],
                                                   fare2=row[14],
                                                   service_tax=row[15],
                                                   wait_time=row[16],
                                                   transfered_to_bank=row[17],
                                                   peak_rate=row[18],
                                                   tips=row[19],
                                                   cancel_payment=row[20])
                    transaction.save()
                except IntegrityError:
                    print(f"{row[0]} transaction is already in DB")


class BoltTransactions(models.Model):
    driver_name = models.CharField(max_length=50)
    driver_number = models.CharField(max_length=13)
    trip_date = models.CharField(max_length=50)
    payment_confirmed = models.CharField(max_length=50)
    boarding = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=30)
    requsted_time = models.CharField(max_length=5)
    fare = models.DecimalField(decimal_places=2, max_digits=10)
    payment_authorization = models.DecimalField(decimal_places=2, max_digits=10)
    service_tax = models.DecimalField(decimal_places=2, max_digits=10)
    cancel_payment = models.DecimalField(decimal_places=2, max_digits=10)
    tips = models.DecimalField(decimal_places=2, max_digits=10)
    order_status = models.CharField(max_length=50)
    car = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=30)

    class Meta:
        unique_together = (('driver_name', 'driver_number', 'trip_date', 'payment_confirmed', 'boarding'))

    @staticmethod
    def save_transactions_to_db(file_name):
        with open(file_name, 'r', encoding='utf-8') as fl:
            reader = csv.reader(fl)
            for row in reader:
                if row[17] == "" and row[0] != "" and row[0] != "Ім'я водія":
                    try:
                        transaction = BoltTransactions(driver_name=row[0],
                                                       driver_number=row[1],
                                                       trip_date=row[2],
                                                       payment_confirmed=row[3],
                                                       boarding=row[4],
                                                       payment_method=row[5],
                                                       requsted_time=row[6],
                                                       fare=row[7],
                                                       payment_authorization=row[8],
                                                       service_tax=row[9],
                                                       cancel_payment=row[10],
                                                       tips=row[11],
                                                       order_status=row[12],
                                                       car=row[13],
                                                       license_plate=row[14])
                        transaction.save()
                    except IntegrityError:
                        print(f"Transaction is already in DB")


class RepairReport(models.Model):
    repair = models.CharField(max_length=255, verbose_name='Фото звіту про ремонт')
    numberplate = models.CharField(max_length=12, unique=True, verbose_name='Номер автомобіля')
    start_of_repair = models.DateTimeField(blank=True, null=False, verbose_name='Початок ремонту')
    end_of_repair = models.DateTimeField(blank=True, null=False, verbose_name='Закінчення ремонту')
    status_of_payment_repair = models.BooleanField(default=False, verbose_name='Статус оплати')  # Paid, Unpaid
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE, verbose_name='Водій')

    class Meta:
        verbose_name='Звіт про ремонт'
        verbose_name_plural='Звіти про ремонти'

    def __str__(self):
        return f'{self.numberplate}'


class ServiceStation(models.Model):
    name = models.CharField(max_length=120, verbose_name='Назва')
    owner = models.CharField(max_length=150, verbose_name='Власник')
    lat = models.DecimalField(decimal_places=4, max_digits=10, default=0, verbose_name='Широта')
    lat_zone = models.CharField(max_length=1, verbose_name='Пояс-Широти')
    lon = models.DecimalField(decimal_places=4, max_digits=10, default=0, verbose_name='Довгота')
    lon_zone = models.CharField(max_length=1, verbose_name='Пояс-Довготи')
    description = models.CharField(max_length=255, verbose_name='Опис')

    class Meta:
        verbose_name="Сервісний Центр"
        verbose_name_plural='Сервісні центри'

    def __str__(self):
        return f'{self.name}'


class Comment(models.Model):
    comment = models.TextField(verbose_name='Відгук')
    chat_id = models.CharField(blank=True, max_length=9, verbose_name='ID в чаті')
    processed = models.BooleanField(default=False, verbose_name='Опрацьовано')

    created_at = models.DateTimeField(editable=False, auto_now=datetime.datetime.now(), verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at']


class Order(models.Model):
    CARD = 'Картка'
    CASH = 'Готівка'

    from_address = models.CharField(max_length=255)
    latitude = models.CharField(max_length=10)
    longitude = models.CharField(max_length=10)
    to_the_address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=13)
    chat_id_client = models.CharField(max_length=15)
    sum = models.CharField(max_length=30)
    payment_method = models.CharField(max_length=70)
    status_order = models.CharField(max_length=70)
    driver = models.ForeignKey(Driver, null=True, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    @staticmethod
    def get_order(chat_id_client, sum, status_order):
        try:
            order = Order.objects.get(chat_id_client=chat_id_client, sum=sum, status_order=status_order)
            return order
        except Order.DoesNotExist:
            return None


class Report_of_driver_debt(models.Model):
    driver = models.CharField(max_length=255, verbose_name='Водій')
    image = models.ImageField(upload_to='.', verbose_name='Фото')

    created_at = models.DateTimeField(editable=False, auto_now=datetime.datetime.now(), verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Звіт заборгованості водія'
        verbose_name_plural = 'Звіти заборгованості водіїв'
        ordering = ['driver']


class Event(models.Model):
    full_name_driver = models.CharField(max_length=255, verbose_name='Водій')
    event = models.CharField(max_length=20, verbose_name='Подія')
    chat_id = models.CharField(blank=True, max_length=9, verbose_name='Індетифікатор чата')
    status_event = models.BooleanField(default=False, verbose_name='Працює')

    created_at = models.DateTimeField(editable=False, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Подія'
        verbose_name_plural = 'Події'



class SubscribeUsers(models.Model):
    email = models.EmailField(max_length=254, verbose_name='Електрона пошта')
    created_at = models.DateTimeField(editable=False, auto_now=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Підписник'
        verbose_name_plural = 'Підписники'

    @staticmethod
    def get_by_email(email):
        """
        Returns subscriber by email
        :param email: email by which we need to find the subscriber
        :type email: str
        :return: subscriber object or None if a subscriber with such email does not exist
        """
        try:
            subscriber = SubscribeUsers.objects.get(email=email)
            return subscriber
        except SubscribeUsers.DoesNotExist:
            return None


class JobApplication(models.Model):
    first_name = models.CharField(max_length=255, verbose_name='Ім\'я')
    last_name = models.CharField(max_length=255, verbose_name='Прізвище')
    email = models.EmailField(max_length=255, verbose_name='Електронна пошта')
    phone_number = models.CharField(max_length=20, verbose_name='Телефон')
    role = models.CharField(max_length=255, verbose_name='Роль')
    status_job_application = models.BooleanField(default=False, verbose_name='Опрацьована')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачі заявки')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver import DesiredCapabilities

import time
import csv
import datetime
import sys
import os
import re
import itertools
import logging
import redis
import pendulum
import base64

from django.db import models
from app.models import Fleet


class SeleniumTools():
    def __init__(self, session, week_number=None, day=None, profile=None):
        self.session_file_name = session
        self.day = day  # if not None then we work with daly reports
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        if week_number:
            self.current_date = pendulum.parse(week_number, tz="Europe/Kiev")
        else:
            self.current_date = pendulum.now().start_of('week').subtract(days=3)
        self.profile = 'Profile 1' if profile is None else profile

    def report_file_name(self, patern):
        filenames = os.listdir(os.curdir)
        for file in filenames:
            if re.search(patern, file):
                return file 

    def week_number(self):
        return f'{self.start_of_week().strftime("%W")}'

    def start_report_interval(self):
        """

        :return: report interval depends on type report (use in Bolt)
        """
        if self.day:
            return self.day.start_of("day")
        return self.current_date.start_of('week')

    def end_report_interval(self):
        if self.day:
            return self.day.end_of("day")
        return self.current_date.end_of('week')

    def start_of_week(self):
        return self.current_date.start_of('week')

    def end_of_week(self):
        return self.current_date.end_of('week')

    def start_of_day(self):
        return self.day.start_of("day")

    def end_of_day(self):
        return self.day.end_of("day")

    def remove_session(self):
        os.remove(self.session_file_name)
    
    # def retry(self, fun, headless=False):
    #     for i in range(2):
    #         try:
    #            time.sleep(0.3)
    #            return fun(headless)
    #         except Exception:
    #             try:
    #                 self.remove_session()
    #                 return fun(headless)
    #             except FileNotFoundError:
    #                 return fun(headless)
    #             continue

    def build_driver(self, headless=True):
        options = Options()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {
            "download.default_directory": os.path.join(os.getcwd(), "LastDownloads"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
        })
        options.add_argument("--disable-infobars")
        options.add_argument("--enable-file-cookies")
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument(f'user-data-dir={os.path.join(os.getcwd(), "_SeleniumChromeUsers", self.profile)}')
        
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument("--no-sandbox")
            options.add_argument("--screen-size=1920,1080")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-extensions")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=options, port=9514)
        return driver

    def build_remote_driver(self, headless=True):

        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("--enable-file-cookies")
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument(f'--user-data-dir=home/seluser/{self.profile}')
        options.add_argument(f'--profile-directory={self.profile}')
        # if headless:
        #     options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

        driver = webdriver.Remote(
            os.environ['SELENIUM_HUB_HOST'],
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options
        )
        return driver

    def get_target_page_or_login(self, url, xpath, login):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.logger.info(f'Got the page without authorization {url}')
        except TimeoutException:
            login()
            self.driver.get(url)
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.logger.info(f'Got the page using authorization {url}')

    def get_downloaded_files(self, driver):
        if not self.driver.current_url.startswith("chrome://downloads"):
            self.driver.get("chrome://downloads/")

        return self.driver.execute_script( \
            "return  document.querySelector('downloads-manager')  "
            " .shadowRoot.querySelector('#downloadsList')         "
            " .items.filter(e => e.state === 'COMPLETE')          "
            " .map(e => e.filePath || e.file_path || e.fileUrl || e.file_url); ")

    def get_file_content(self, path):
        try:
            elem = self.driver.execute_script( \
                "var input = window.document.createElement('INPUT'); "
                "input.setAttribute('type', 'file'); "
                "input.hidden = true; "
                "input.onchange = function (e) { e.stopPropagation() }; "
                "return window.document.documentElement.appendChild(input); ")
            elem._execute('sendKeysToElement', {'value': [path], 'text': path})
            result = self.driver.execute_async_script( \
                "var input = arguments[0], callback = arguments[1]; "
                "var reader = new FileReader(); "
                "reader.onload = function (ev) { callback(reader.result) }; "
                "reader.onerror = function (ex) { callback(ex.message) }; "
                "reader.readAsDataURL(input.files[0]); "
                "input.remove(); "
                , elem)
            if not result.startswith('data:'):
                raise Exception("Failed to get file content: %s" % result)
            return base64.b64decode(result[result.find('base64,') + 7:])
        finally:
            pass

    def get_last_downloaded_file_frome_remote(self, save_as=None):
        try:
            files = WebDriverWait(self.driver, 30, 1).until(lambda driver: self.get_downloaded_files(driver))
        except TimeoutException:
            return
        content = self.get_file_content(files[0])
        if len(files):
            fname = os.path.basename(files[0]) if save_as is None else save_as
            with open(os.path.join(os.getcwd(), fname), 'wb') as f:
                f.write(content)

    def get_last_downloaded_file(self, save_as=None):
        folder = os.path.join(os.getcwd(), "LastDownloads")
        files = [os.path.join(folder, f) for f in os.listdir(folder)]  # add path to each file
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        if len(files):
            fname = os.path.basename(files[0]) if save_as is None else save_as
            shutil.copyfile(files[0],os.path.join(os.getcwd(), fname))
        for filename in files:
            if '.csv' in filename:
                file_path = os.path.join(folder, filename)
                os.remove(file_path)

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.driver = None


class Uber(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False, base_url="https://supplier.uber.com", remote=False, profile=None):
        super().__init__('uber', week_number=week_number, day=day, profile=profile)
        self.sleep = sleep
        if driver:
            if remote:
                self.driver = self.build_remote_driver(headless)
            else:
                self.driver = self.build_driver(headless)
        self.remote = remote
        self.base_url = base_url

    def quit(self):
        self.driver.quit()
        self.driver = None

    def login_v2(self, link="https://drivers.uber.com/"):
        self.driver.get(link)
        self.login_form('PHONE_NUMBER_or_EMAIL_ADDRESS', 'forward-button', By.ID)  
        self.force_opt_form()
        self.otp_code_v2()
        # self.otp_code_v1()
        self.password_form('PASSWORD', 'forward-button', By.ID)
        if self.sleep:
            time.sleep(self.sleep)

    def login_v3(self, link="https://auth.uber.com/v2/"):
        self.driver.get(link)
        self.login_form('PHONE_NUMBER_or_EMAIL_ADDRESS', 'forward-button', By.ID)
        try:
            self.password_form_v3()
        except TimeoutException:
            try:
                el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'alt-PASSWORD')))
                el.click()
                self.password_form_v3()
            except TimeoutException:
                self.otp_code_v2()
        if self.sleep:
            time.sleep(self.sleep)

    def password_form_v3(self):
        el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'PASSWORD')))
        el.clear()
        el.send_keys(os.environ["UBER_PASSWORD"])
        el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'forward-button')))
        el.click()

    def login(self, link="https://auth.uber.com/login/"):
        self.driver.get(link)
        self.login_form('userInput', 'next-button-wrapper', By.CLASS_NAME)
        self.otp_code_v1()
        self.password_form('password', 'next-button-wrapper', By.CLASS_NAME)
        if self.sleep:
            time.sleep(self.sleep)
    
    def generate_payments_order(self):
        url = f"{self.base_url}/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/reports"
        # url = f"{self.base_url}/orgs/2c5515cd-a4ed-4136-905f-99504677a324/reports"  #my
        xpath = '//div[@data-testid="report-type-dropdown"]/div/div'
        self.get_target_page_or_login(url, xpath, self.login_v3)
        self.driver.get_screenshot_as_file('generate_payments_order.png')
        menu = '//div[@data-testid="report-type-dropdown"]/div/div'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, menu)))
        self.driver.find_element(By.XPATH, menu).click()   
        try:
            xpath = '//ul/li/div[text()[contains(.,"Payments Driver")]]'
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except Exception:
            try:
                xpath = '//ul/li/div[text()[contains(.,"Payments driver")]]'
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()
            except Exception:
                xpath = '//ul/li/div[text()[contains(.,"Платежи (водитель)")]]'
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()

        if self.day:
            start = self.driver.find_element(By.XPATH,'(//input[@aria-describedby="datepicker--screenreader--message--input"])[1]')
            start.send_keys(Keys.NULL)
            date_by_def = pendulum.now().start_of('week').subtract(days=7)
            if date_by_def.month - self.day.month == -1:  # if month of day is different from month of last week Monday
                self.driver.find_element(By.XPATH, f'//button[@aria-label="Next month."]').click()
            elif date_by_def.month - self.day.month > 0:
                for _ in range(date_by_def.month - self.day.month):
                    self.driver.find_element(By.XPATH, f'//button[@aria-label="Previous month."]').click()
            self.driver.find_element(By.XPATH, f'//div[@aria-roledescription="button"]/div[text()={self.day.strftime("%-d")}]').click()
            end = self.driver.find_element(By.XPATH,'(//input[@aria-describedby="datepicker--screenreader--message--input"])[2]')
            end.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH,f'//div[@aria-roledescription="button"]/div[text()="{self.day.strftime("%-d")}"]').click()
        else:
            start = self.driver.find_element(By.XPATH, '(//input[@aria-describedby="datepicker--screenreader--message--input"])[1]')
            start.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH, '(//button[@aria-live="polite"])[1]').click()
            self.driver.find_element(By.XPATH, f'(//li[@role="option" and text()[contains(.,"{self.start_of_week().strftime("%B")}")]])').click()
            self.driver.find_element(By.XPATH, '(//button[@aria-live="polite"])[2]').click()
            self.driver.find_element(By.XPATH, f'(//li[@role="option" and text()[contains(.,"{self.start_of_week().strftime("%Y")}")]])').click()
            self.driver.find_element(By.XPATH, f'//div[@aria-roledescription="button"]/div[text()={self.start_of_week().day}]').click()
            end = self.driver.find_element(By.XPATH, '(//input[@aria-describedby="datepicker--screenreader--message--input"])[2]')
            end.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH, '(//button[@aria-live="polite"])[1]').click()
            self.driver.find_element(By.XPATH, f'(//li[@role="option" and text()[contains(.,"{self.end_of_week().strftime("%B")}")]])').click()
            self.driver.find_element(By.XPATH, '(//button[@aria-live="polite"])[2]').click()
            self.driver.find_element(By.XPATH, f'(//li[@role="option" and text()[contains(.,"{self.end_of_week().strftime("%Y")}")]])').click()
            self.driver.find_element(By.XPATH, f'//div[@aria-roledescription="button"]/div[text()={self.end_of_week().day}]').click()
        self.driver.find_element(By.XPATH, '//button[@data-testid="generate-report-button"]').click()

        return f'{self.payments_order_file_name()}'

    def download_payments_order(self):
        if os.path.exists(f'{self.payments_order_file_name()}'):
            print('Report already downloaded')
            return

        self.generate_payments_order()
        download_button = '(//div[@data-testid="paginated-table"]//button)[1]'
        try:
            # in_progress_text = '//div[1][@data-testid="payment-reporting-table-row"]/div/div/div/div[text()[contains(.,"In progress")]]'
            in_progress_text = '//i[@class="_css-bvkFtm"]'
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 600).until_not(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            expected_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, download_button)))
            WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, download_button))).click()
            time.sleep(self.sleep)
            if self.remote:
                self.get_last_downloaded_file_frome_remote(f'Uber {self.file_patern()}.csv')
            else:
                self.get_last_downloaded_file(f'Uber {self.file_patern()}.csv')

        except Exception as e:
            self.logger.error(str(e))
            pass 

    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def file_patern(self):
        if self.day:
            start = self.start_of_day()
            end = self.end_of_day()
        else:
            start = self.start_of_week()
            end = self.end_of_week()
        sd, sy, sm = start.strftime("%d"), start.strftime("%Y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%Y"), end.strftime("%m")
        return f'{sy}{sm}{sd}-{ey}{em}{ed}-payments_driver'

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        if self.payments_order_file_name() is not None:
            try:
                with open(self.payments_order_file_name(), encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        if row[3] == "":
                            continue
                        if row[3] is None:
                            continue
                        order = UberPaymentsOrder(
                            report_from=self.start_of_week(),
                            report_to=self.end_of_week(),
                            report_file_name=self.payments_order_file_name(),
                            driver_uuid=row[0],
                            first_name=row[1],
                            last_name=row[2],
                            total_amount=row[3],
                            total_clean_amout=row[4] or 0,
                            returns=row[5] or 0,
                            total_amount_cach=row[6] or 0,
                            transfered_to_bank=row[7] or 0,
                            tips=row[8] or 0)
                        try:
                            order.save()
                        except IntegrityError:
                            pass
                        items.append(order)

                    if not items:
                        order = UberPaymentsOrder(
                            report_from=self.start_of_week(),
                            report_to=self.end_of_week(),
                            report_file_name=self.payments_order_file_name(),
                            driver_uuid='00000000-0000-0000-0000-000000000000',
                            first_name='',
                            last_name='',
                            total_amount=0,
                            total_clean_amout=0,
                            returns=0,
                            total_amount_cach=0,
                            transfered_to_bank=0,
                            tips=0)
                        try:
                            order.save()
                        except IntegrityError:
                            pass
            except FileNotFoundError:
                pass
        return items

    def wait_opt_code(self):
        r = redis.Redis.from_url(os.environ["REDIS_URL"])
        p = r.pubsub()
        p.subscribe('code')
        p.ping()
        otpa = []
        while True:
            try:
                otp = p.get_message()
                if otp:
                    otpa = list(f'{otp["data"]}')
                    otpa = list(filter(lambda d: d.isdigit(), otpa))
                    digits = [s.isdigit() for s in otpa]
                    if not(digits) or (not all(digits)) or len(digits) != 4:
                        continue
                    break 
            except redis.ConnectionError as e:
                self.logger.error(str(e))
                p = r.pubsub()
                p.subscribe('code')
            time.sleep(1)  
        return otpa 

    def otp_code_v2(self):
        while True:
            if not self.wait_code_form('PHONE_SMS_OTP-0'):
                break
            otp = self.wait_opt_code()
            self.driver.find_element(By.ID, 'PHONE_SMS_OTP-0').send_keys(otp[0])
            self.driver.find_element(By.ID, 'PHONE_SMS_OTP-1').send_keys(otp[1])
            self.driver.find_element(By.ID, 'PHONE_SMS_OTP-2').send_keys(otp[2])
            self.driver.find_element(By.ID, 'PHONE_SMS_OTP-3').send_keys(otp[3])
            # self.driver.find_element(By.ID, "forward-button").click()
            break
    
    def wait_code_form(self, id):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, id)))
            self.driver.find_element(By.ID, id)
            self.driver.get_screenshot_as_file(f'{id}.png')
            return True
        except Exception as e:
            self.logger.error(str(e))
            self.driver.get_screenshot_as_file(f'{id}_error.png')
            return False

    def otp_code_v1(self):
        while True:
            if not self.wait_code_form('verificationCode'):
                break
            otp = self.wait_opt_code()
            self.driver.find_element(By.ID, 'verificationCode').send_keys(otp)
            self.driver.find_element(By.CLASS_NAME, "next-button-wrapper").click()
            break
    
    def force_opt_form(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'alt-PHONE-OTP')))
            el = self.driver.find_element(By.ID, 'alt-PHONE-OTP').click()
        except Exception as e:
            # self.logger.error(str(e))
            pass
    
    def password_form(self, id, button, selector):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, id)))
            el = self.driver.find_element(By.ID, id).send_keys(os.environ["UBER_PASSWORD"])
            self.driver.find_element(selector, button).click()
            self.driver.get_screenshot_as_file('UBER_PASSWORD.png')
        except Exception as e:
            self.logger.error(str(e))

    def login_form(self, id, button, selector):
        element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, id)))
        element.send_keys(os.environ["UBER_NAME"])
        e = self.driver.find_element(selector, button)
        e.click() 
        self.driver.get_screenshot_as_file('UBER_NAME.png')

    def add_driver(self, phone_number, email, name, second_name):
        url = 'https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/drivers'
        self.driver.get(f"{url}")
        if self.sleep:
            time.sleep(self.sleep)
        add_driver = self.driver.find_element(By.XPATH, '//button')
        add_driver.click()
        if self.sleep:
            time.sleep(self.sleep)
        data = self.driver.find_element(By.XPATH, '//div[2]/div/input')
        data.click()
        data.send_keys(f'{phone_number[4:]}' + Keys.TAB + Keys.TAB + f'{email}' + Keys.TAB + f'{name}' + Keys.TAB + f'{second_name}')
        send_data = self.driver.find_element(By.XPATH, '//div[5]/div[2]/button')
        send_data.click()
        if self.sleep:
            time.sleep(self.sleep)


    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        u = Uber(week_number=week_number, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir) and driver:
            u = Uber(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            # u.login_v2()
            u.download_payments_order()
            u.quit()
        return u.save_report()


class Bolt(SeleniumTools):    
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False, base_url="https://fleets.bolt.eu", remote=False, profile=None):
        super().__init__('bolt', week_number=week_number, day=day, profile=profile)
        self.sleep = sleep
        if driver:
            if remote:
                self.driver = self.build_remote_driver(headless)
            else:
                self.driver = self.build_driver(headless)
        self.remote = remote
        self.base_url = base_url
    
    def quit(self):
        self.driver.quit()
        self.driver = None

    def login(self):
        self.driver.get(f"{self.base_url}/login")
        if self.sleep:
            time.sleep(self.sleep)
        element = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, 'username')))
        element.clear()
        element.send_keys(os.environ["BOLT_NAME"])
        element = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, 'password')))
        element.clear()
        element.send_keys(os.environ["BOLT_PASSWORD"])
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        url = f"{self.base_url}/company/58225/reports/weekly"
        xpath = '//div/div/table'
        self.get_target_page_or_login(url, xpath, self.login)
        if self.day:
            self.driver.get(f"{self.base_url}/company/58225/reports/dayly/")
            if self.sleep:
                time.sleep(self.sleep)
            xpath = f'//table/tbody/tr/td[text()="{self.file_patern()}"]'
            element_date = self.driver.find_element(By.XPATH, xpath)
            element_date.find_element(By.XPATH, "./../td/a").click()
        else:
            self.driver.get(f"{self.base_url}/company/58225/reports/weekly/{self.file_patern()}")
            time.sleep(self.sleep)
            if self.remote:
                self.get_last_downloaded_file_frome_remote()
            else:
                self.get_last_downloaded_file()

    def file_patern(self):
        if self.day:
            return self.day.format("DD.MM.YYYY")
        return f"{self.current_date.strftime('%Y')}W{self.week_number()}"

    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        if self.payments_order_file_name() is not None:
            with open(self.payments_order_file_name(), encoding="utf-8") as file:
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
                        report_from=self.start_report_interval(),
                        report_to=self.end_report_interval(),
                        report_file_name=file.name,
                        driver_full_name=row[0][:24],
                        mobile_number=row[1],
                        range_string=row[2],
                        total_amount=float(row[3].replace(',', '.')),
                        cancels_amount=float(row[4].replace(',', '.')),
                        autorization_payment=float(row[5].replace(',', '.')),
                        autorization_deduction=float(row[6].replace(',', '.')),
                        additional_fee=float(row[7].replace(',', '.')),
                        fee=float(row[8].replace(',', '.')),
                        total_amount_cach=float(row[9].replace(',', '.')),
                        discount_cash_trips=float(row[10].replace(',', '.')),
                        driver_bonus=float(row[11].replace(',', '.')),
                        compensation=float(str(row[12] or 0).replace(',', '.')),
                        refunds=float(row[13].replace(',', '.')),
                        tips=float(row[14].replace(',', '.')),
                        weekly_balance=float(row[15].replace(',', '.')))
                    try:
                        order.save()
                    except IntegrityError:
                        pass
                    items.append(order)
        else:
            order = BoltPaymentsOrder(
                report_from=self.start_report_interval(),
                report_to=self.end_report_interval(),
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

    def add_driver(self, email, phone_number):
        """phone number exmp +380.."""

        url = 'https://fleets.bolt.eu/company/58225/driver/add'
        self.driver.get(f"{url}")
        if self.sleep:
            time.sleep(self.sleep)
        form_email = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'email')))
        form_email.click()
        form_email.clear()
        form_email.send_keys(email)
        form_phone_number = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'phone')))
        form_phone_number.click()
        form_phone_number.clear()
        form_phone_number.send_keys(phone_number)
        button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'ember38')))
        button.click()
        if self.sleep:
            time.sleep(self.sleep)


    @staticmethod
    def download_weekly_report(week_number=None, day=None,  driver=True, sleep=5, headless=True):
        """Can save weekly and daily report"""
        b = Bolt(week_number=week_number, day=day, driver=False, sleep=0, headless=headless)
        if b.payments_order_file_name() not in os.listdir(os.curdir) and driver:
            b = Bolt(week_number=week_number, day=day, driver=driver, sleep=sleep, headless=headless)
            # b.login()
            b.download_payments_order()
            b.quit()
        return b.save_report()


class Uklon(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False, base_url="https://partner.uklon.com.ua"):
        super().__init__('uklon', week_number=week_number, day=day)
        self.sleep = sleep
        if driver:
            self.driver = self.build_driver(headless)
        self.base_url = base_url

    def quit(self):
        self.driver.quit()


    def login(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element("name", 'login').send_keys(os.environ["UKLON_NAME"])
        element = self.driver.find_element("name", "loginPassword").send_keys(os.environ["UKLON_PASSWORD"])
        self.driver.find_element("name", "Login").click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        """
        Download report file to folder
        :return: None
        """
        if self.day:
            url = f"{self.base_url}/partner/export/fares?page=1&pageSize=20&" \
                  f"startDate={self.start_of_day_timestamp()}&" \
                  f"endDate={self.end_of_day_timestamp()}&format=csv"
        else:
            url = f"{self.base_url}/partner/export/fares?page=1&pageSize=20&" \
                  f"startDate={self.start_of_week_timestamp()}&" \
                  f"endDate={self.end_of_week_timestamp()}&format=csv"
        self.driver.get(url)

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        report_file = self.report_file_name(self.file_patern())
        if report_file is not None:
            report = open(report_file)

            with report as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    row = row[0].split('||')
                    order = UklonPaymentsOrder(
                                               report_from=self.start_of_week(),
                                               report_to=self.end_of_week(),
                                               report_file_name=file.name,
                                               signal=row[0],
                                               licence_plate=row[1],
                                               total_rides=row[2],
                                               total_distance = int(row[3]),
                                               total_amount_cach=row[4],
                                               total_amount_cach_less=row[5],
                                               total_amount=row[6],
                                               total_amount_without_comission=row[7],
                                               bonuses=row[8])
                    try:
                        order.save()
                    except IntegrityError:
                        pass
                    items.append(order)

        else:
            # create an empty record to avoid reloading
            order = UklonPaymentsOrder(
                report_from=self.start_of_week(),
                report_to=self.end_of_week(),
                report_file_name='',
                signal='',
                licence_plate='',
                total_rides=0,
                total_distance=0,
                total_amount_cach=0,
                total_amount_cach_less=0,
                total_amount=0,
                total_amount_without_comission=0,
                bonuses=0)
            try:
                order.save()
            except IntegrityError:
                pass
        return items

    def start_of_day_timestamp(self):
        return round(self.start_of_day().timestamp())

    def end_of_day_timestamp(self):
        return round(self.end_of_day().timestamp())

    def start_of_week_timestamp(self):
        return round(self.start_of_week().timestamp())

    def end_of_week_timestamp(self):
        return round(self.end_of_week().timestamp())
    
    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def file_patern(self):
        if self.day:
            start = self.start_of_day()
            end = self.end_of_day()
        else:
            start = self.start_of_week()
            end = self.end_of_week().end_of('day').add(hours=4)
        sd, sy, sm = start.strftime("%d"), start.strftime("%Y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%Y"), end.strftime("%m")
        return f'{start.strftime("%m")}_{start.strftime("%d")}_{sy}-{end.strftime("%m")}_{end.strftime("%d")}_{ey}'

    @staticmethod
    def download_weekly_report(week_number=None, day=None, driver=True, sleep=5, headless=True):
        """Can save weekly and daily report"""
        u = Uklon(week_number=week_number, day=day, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir):
            u = Uklon(week_number=week_number, day=day, driver=driver, sleep=sleep, headless=headless)
            u.login()
            u.download_payments_order()
        return u.save_report()

    def status(self):
        pass


class NewUklon(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False, base_url="https://fleets.uklon.com.ua", remote=False, profile=None):
        super().__init__('nuklon', week_number=week_number, day=day, profile=profile)
        self.sleep = sleep
        if driver:
            if remote:
                self.driver = self.build_remote_driver(headless)
            else:
                self.driver = self.build_driver(headless)
        self.remote = remote
        self.base_url = base_url

    def login(self):
        self.driver.get(self.base_url + '/auth/login')
        if self.sleep:
            time.sleep(self.sleep)
        element = self.driver.find_element(By.ID, 'mat-input-1')

        element.send_keys(os.environ["UKLON_NAME"])
        element = self.driver.find_element(By.ID, "password")

        element.send_keys('')
        element.send_keys(os.environ["UKLON_PASSWORD"])

        self.driver.find_element(By.XPATH, '//button[@data-cy="login-btn"]').click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        url = f'{self.base_url}/workspace/orders'
        xpath = '//flt-group-filter[1]/flt-date-range-filter/mat-form-field/div'
        self.get_target_page_or_login(url, xpath, self.login)

        self.driver.find_element(By.XPATH, '//flt-group-filter[1]/flt-date-range-filter/mat-form-field/div').click()
        self.driver.find_element(By.XPATH, '//mat-option[@id="mat-option-7"]/span').click()  #Минулий тиждень
        self.driver.find_element(By.XPATH, '//flt-filter-group/div/div/button').click()  #Експорт CSV
        time.sleep(self.sleep)
        if self.remote:
            self.get_last_downloaded_file_frome_remote(save_as=f'Uklon {self.file_patern()}.csv')
        else:
            self.get_last_downloaded_file(save_as=f'Uklon {self.file_patern()}.csv')

    def download_payments_day_order(self):
        actions = ActionChains(self.driver)
        actions.move_by_offset(500, 500).perform()
        if self.sleep:
            time.sleep(self.sleep)
        url = f'{self.base_url}/workspace/orders'
        self.driver.get(url)
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH,
                                 '//upf-order-reports/section[1]/flt-filter-group/form/flt-group-filter[1]/flt-date-range-filter/mat-form-field/div').click()
        self.driver.find_element(By.XPATH, '//mat-option/span/div[text()=" Вибрати період "]').click()
        e = self.driver.find_element(By.XPATH, '//input').click()

        sh, sm, eh, em = '00', '00', '23', '59'  # s - start/e - end/h - hours/m - minutes
        e.send_keys(self.day.format("DD.MM.YYYY") + Keys.TAB + self.day.format("DD.MM.YYYY") + Keys.TAB + Keys.TAB + f'{sh}' + Keys.SPACE + f'{sm}' + Keys.TAB + f'{eh}' + Keys.SPACE + f'{em}')

        self.driver.find_element(By.XPATH, '//span[text()= " Застосувати "]').click()
        if self.sleep:
            time.sleep(self.sleep)
        actions.click().perform()
        self.driver.find_element(By.XPATH, '//span[text()="Експорт CSV"]').click()

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        file = self.report_file_name('01.70.csv')
        os.rename(file, f'Звіт по поїздкам - {self.file_patern()}.csv')

        self.logger.info(self.file_patern())
        report = open(self.report_file_name(self.file_patern()))

        with report as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                print(row)

                order = NewUklonPaymentsOrder(
                    report_from=self.start_of_week(),
                    report_to=self.end_of_week(),
                    report_file_name=file.name,
                    full_name=row[0],
                    signal=row[1],
                    total_rides=float((row[2] or '0').replace(',','')),
                    total_distance=float((row[3] or '0').replace(',','')),
                    total_amount_cach=float((row[4] or '0').replace(',','')),
                    total_amount_cach_less=float((row[5] or '0').replace(',','')),
                    total_amount_on_card=float((row[6] or '0').replace(',','')),
                    total_amount=float((row[7] or '0').replace(',','')),
                    tips=float((row[8] or '0').replace(',','') ),
                    bonuses=float((row[9] or '0').replace(',','')),
                    fares=float((row[10] or '0').replace(',','')),
                    comission=float((row[11] or '0').replace(',','')),
                    total_amount_without_comission=float((row[12] or '0').replace(',','')))
                order.save()
                items.append(order)

        return items

    def save_report_v2(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        if self.payments_order_file_name() is not None:
            with open(self.payments_order_file_name(), encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    order = NewUklonPaymentsOrder(
                        report_from=self.start_of_week(),
                        report_to=self.end_of_week(),
                        report_file_name=file.name,
                        full_name=row[0],
                        signal=row[1],
                        total_rides=float((row[2] or '0').replace(',','')),
                        total_distance=float((row[3] or '0').replace(',','')),
                        total_amount_cach=float((row[4] or '0').replace(',','')),
                        total_amount_cach_less=float((row[5] or '0').replace(',','')),
                        total_amount_on_card=float((row[6] or '0').replace(',','')),
                        total_amount=float((row[7] or '0').replace(',','')),
                        tips=float((row[8] or '0').replace(',','') ),
                        bonuses=float((row[9] or '0').replace(',','')),
                        fares=float((row[10] or '0').replace(',','')),
                        comission=float((row[11] or '0').replace(',','')),
                        total_amount_without_comission=float((row[12] or '0').replace(',','')))
                    try:
                        order.save()
                    except IntegrityError:
                        pass
                    items.append(order)


        if not items:
            order = NewUklonPaymentsOrder(
                report_from=self.start_of_week(),
                report_to=self.end_of_week(),
                report_file_name='',
                full_name='',
                signal='',
                total_rides=0,
                total_distance=0,
                total_amount_cach=0,
                total_amount_cach_less=0,
                total_amount_on_card=0,
                total_amount=0,
                tips=0,
                bonuses=0,
                fares=0,
                comission=0,
                total_amount_without_comission=0)
            try:
                order.save()
            except IntegrityError:
                pass

        return items

    def start_of_week_timestamp(self):
        return round(self.start_of_week().timestamp())

    def end_of_week_timestamp(self):
        return round(self.end_of_week().timestamp())

    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def file_patern(self):
        if self.day:
            start = self.start_of_day()
            end = self.end_of_day()
        else:
            start = self.start_of_week()
            end = self.end_of_week().end_of('day')
        sd, sy, sm = start.strftime("%d"), start.strftime("%y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%y"), end.strftime("%m")
        return f'00.00.{sd}.{sm}.{sy} - 23.59.{ed}.{em}.{ey}'


    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        u = NewUklon(week_number=week_number, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir) and driver:
            u = NewUklon(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            # u.login()
            u.download_payments_order()
            u.quit()
        # return u.save_report()
        return u.save_report_v2()

    @staticmethod
    def download_daily_report(day=None, driver=True, sleep=5, headless=True):
        u = NewUklon(day=day, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir):
            u = NewUklon(day=day, driver=driver, sleep=sleep, headless=headless)
            u.login()
            u.download_payments_day_order()
        return u.save_report()


class Privat24(SeleniumTools):
    def __init__(self, card=None, sum=None, driver=True, sleep=3, headless=False, base_url ='https://next.privat24.ua/'):
        self.sleep = sleep
        self.card = card
        self.sum = sum
        if driver:
            self.driver = self.build_driver(headless)
        self.base_url = base_url

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.get(self.base_url)
        if self.sleep:
            time.sleep(self.sleep)
        e = self.driver.find_element(By.XPATH, '//div/button')
        e.click()
        if self.sleep:
            time.sleep(self.sleep)
        login = self.driver.find_element(By.XPATH, '//div[3]/div[1]/input')
        ActionChains(self.driver).move_to_element(login).send_keys(os.environ["PRIVAT24_NAME"]).perform()
        if self.sleep:
            time.sleep(self.sleep)


    def password(self):
        password = self.driver.find_element(By.XPATH, '//input')
        ActionChains(self.driver).move_to_element(password).send_keys('').perform()
        ActionChains(self.driver).move_to_element(password).send_keys('PRIVAT24_PASSWORD').perform()
        ActionChains(self.driver).move_to_element(password).send_keys( Keys.TAB + Keys.TAB + Keys.ENTER).perform()
        if self.sleep:
            time.sleep(self.sleep)


    def money_transfer(self):
        if self.sleep:
            time.sleep(25)
        url = f'{self.base_url}money-transfer/card'
        self.driver.get(url)
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.get_screenshot_as_file(f'privat_1.png')
        e = self.driver.find_element(By.XPATH, '//div[2]/div/div[1]/div[2]/div/div[2]')
        e.click()
        card = self.driver.find_element(By.XPATH, '//div[1]/div[2]/input')
        card.click()
        self.driver.get_screenshot_as_file(f'privat_2.png')
        card.send_keys(f"{self.card}" + Keys.TAB + f'{self.sum}')
        self.driver.get_screenshot_as_file(f'privat_3.png')
        button = self.driver.find_element(By.XPATH, '//div[4]/div/button')
        button.click()

    def transfer_confirmation(self):
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, '//div[3]/div[3]/button').click()
        if self.sleep:
            time.sleep(self.sleep)
        try:
            xpath = '//div/div[4]/div[2]/button'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        except TimeoutException:
            pass
        finally:
            if self.sleep:
                time.sleep(self.sleep)
            self.driver.find_element(By.XPATH, '//div[2]/div[2]/div/div[2]/button').click()


    @staticmethod
    def card_validator(card):
        pattern = '^([0-9]{4}[- ]?){3}[0-9]{4}$'
        result = re.match(pattern, card)
        if True:
            return result
        else:
            return None


def get_report(week_number = None, driver=True, sleep=5, headless=True):
    driver = False
    owner =   {"Fleet Owner": 0}
    reports = {}
    totals =  {}
    salary =  {}
    fleets =  Fleet.objects.filter(deleted_at=None)
    for fleet in fleets:
        all_drivers_report = fleet.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
        for rate in Fleets_drivers_vehicles_rate.objects.filter(fleet_id=fleet.id, deleted_at=None):
            r = list((r for r in all_drivers_report if r.driver_id() == rate.driver_external_id))
            if r:
                r = r[0]
                # print(r)
                name = rate.driver.full_name()
                reports[name] = reports.get(name, '') + r.report_text(name, float(rate.rate)) + '\n'
                totals[name] = totals.get(name, 0) + r.kassa()
                salary[name] = salary.get(name, 0) + r.total_drivers_amount(float(rate.rate))
                owner["Fleet Owner"] += r.total_owner_amount(float(rate.rate))

    totals = {k: v for k, v in totals.items() if v != 0.0}
    totals = {k: f'Общаяя касса {k}: %.2f\n' % v for k, v in totals.items()}
    totals = {k: v + reports[k] for k, v in totals.items()}
    totals = {k: v + f'Зарплата за тиждень {k}: %.2f\n' % salary[k] for k, v in totals.items()}

    return owner, totals



def download_and_save_daily_report(driver=True, sleep=5, headless=True, day=None):
    fleets = Fleet.objects.filter(deleted_at=None)
    for fleet in fleets:
        fleet.download_daily_report(day=day, driver=driver, sleep=sleep, headless=headless)


