import string
import random
import csv

import re
from datetime import datetime, date, time
import pendulum
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db import models, IntegrityError, ProgrammingError
from django.db.models import Sum
from django.utils.safestring import mark_safe
from polymorphic.models import PolymorphicModel
from django.contrib.auth.models import User as AuUser


class Role(models.TextChoices):
    CLIENT = 'CLIENT', 'Client'
    DRIVER = 'DRIVER', 'Driver'
    DRIVER_MANAGER = 'DRIVER_MANAGER', 'Driver manager'
    SERVICE_STATION_MANAGER = 'SERVICE_STATION_MANAGER', 'Service station manager'
    SUPPORT_MANAGER = 'SUPPORT_MANAGER', 'Support manager'
    OWNER = 'OWNER', 'Owner'
    INVESTOR = 'INVESTOR', 'Investor'


class Partner(models.Model):
    role = models.CharField(max_length=25, default=Role.OWNER, choices=Role.choices)
    user = models.OneToOneField(AuUser, on_delete=models.SET_NULL, null=True)
    chat_id = models.CharField(blank=True, null=True, max_length=10, verbose_name='Ідентифікатор чата')
    calendar = models.CharField(max_length=255, verbose_name='Календар змін водіїв')

    @classmethod
    def get_partner(cls, pk):
        return cls.objects.get(id=pk)

    @staticmethod
    def get_by_chat_id(chat_id):
        try:
            return Partner.objects.get(chat_id=chat_id)
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return str(self.user.username) if self.user else ''

    class Meta:
        verbose_name = 'Власника'
        verbose_name_plural = 'Власники'


class Payments(models.Model):
    report_from = models.DateField(verbose_name='Дата звіту')
    vendor_name = models.CharField(max_length=30, default='Ninja', verbose_name='Агрегатор')
    full_name = models.CharField(null=True, max_length=255, verbose_name='ПІ водія')
    driver_id = models.CharField(null=True, max_length=50, verbose_name='Унікальний індифікатор водія')
    total_amount_without_fee = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чистий дохід')
    total_amount_cash = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Готівкою')
    total_amount_on_card = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10,
                                               verbose_name='На картку')
    total_amount = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10,
                                       verbose_name='Загальна сума')
    tips = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10, verbose_name='Чайові')
    total_rides = models.PositiveIntegerField(null=True, default=0, verbose_name='Кількість поїздок')
    total_distance = models.DecimalField(null=True, default=0, decimal_places=2,
                                         max_digits=10, verbose_name='Пробіг під замовлення')
    bonuses = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10, verbose_name='Бонуси')
    fee = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10, verbose_name='Комісія')
    fares = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10, verbose_name='Штрафи')
    cancels = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10,
                                  verbose_name='Плата за скасування')
    compensations = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10,
                                        verbose_name='Компенсації')
    refunds = models.DecimalField(null=True, default=0, decimal_places=2, max_digits=10,
                                  verbose_name='Повернення коштів')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Звіт'
        verbose_name_plural = 'Звіти'
        unique_together = ('report_from', 'driver_id')

    class Scopes:
        def filter_by_driver_external_id(self, driver_external_id):
            return self.filter(driver_id=driver_external_id)

    def report_text(self, name=None, rate=0.35):
        return f'{self.vendor_name} {name}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate * 100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные(-{"%.2f" % float(self.total_amount_cash)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate):
        return self.kassa() * rate + float(self.total_amount_cash)

    def kassa(self):
        return float(self.total_amount_without_fee)


class SummaryReport(models.Model):
    report_from = models.DateField(verbose_name='Дата звіту')
    full_name = models.CharField(null=True, max_length=255, verbose_name='ПІ водія')
    total_amount_without_fee = models.DecimalField(decimal_places=2, max_digits=10,
                                                   verbose_name='Чистий дохід', db_index=True)
    total_amount_cash = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Готівкою')
    total_amount_on_card = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='На картку')
    total_amount = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Загальна сума')
    total_rides = models.PositiveIntegerField(null=True, verbose_name='Кількість поїздок')
    total_distance = models.DecimalField(null=True, decimal_places=2,
                                         max_digits=10, verbose_name='Пробіг під замовлення')
    tips = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Чайові')
    bonuses = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Бонуси')
    fee = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Комісія')
    fares = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Штрафи')
    cancels = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Плата за скасування')
    compensations = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Компенсації')
    refunds = models.DecimalField(null=True, decimal_places=2, max_digits=10, verbose_name='Повернення коштів')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Зведений звіт'
        verbose_name_plural = 'Зведені звіти'

    def total_drivers_amount(self, rate):
        return self.get_kasa() * rate + float(self.total_amount_cash)

    def get_kasa(self):
        return float(self.total_amount_without_fee)


class UberTrips(models.Model):
    report_from = models.DateField(verbose_name="Дата поїздки")
    driver_external_id = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=10)
    start_trip = models.DateTimeField(null=True, blank=True)
    end_trip = models.DateTimeField(null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(auto_now_add=True)


class FileNameProcessed(models.Model):
    filename_weekly = models.CharField(max_length=150, unique=True)

    @staticmethod
    def save_filename_to_db(processed_files: list):
        for name in processed_files:
            order = FileNameProcessed(
                filename_weekly=name)

            order.save()


class User(models.Model):

    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ім'я")
    second_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Прізвище')
    email = models.EmailField(blank=True, null=True, max_length=254, verbose_name='Електронна пошта')
    role = models.CharField(max_length=25, default=Role.CLIENT, choices=Role.choices)
    phone_number = models.CharField(blank=True, null=True, max_length=13, verbose_name='Номер телефона')
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='Ідентифікатор чата')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Користувача'
        verbose_name_plural = 'Користувачі'

    def __str__(self) -> str:
        return self.full_name()

    def full_name(self):
        return f'{self.name} {self.second_name}'

    @classmethod
    def get_by_chat_id(cls, chat_id):
        """
        Returns user by chat_id
        :param chat_id: chat_id by which we need to find the user
        :type chat_id: str
        :return: user object or None if a user with such ID does not exist
        """
        try:
            user = cls.objects.get(chat_id=chat_id)
            return user
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def fill_deleted_at_by_number(number):
        """
        :param number: a number of a user to fill deleted_at
        :type number: str
        """
        user = User.objects.filter(phone_number=number).first()
        user.deleted_at = timezone.localtime()
        user.save()
        return user

    @staticmethod
    def name_and_second_name_validator(name) -> str:
        """This func validator for name and second name"""
        if len(name) <= 255:
            return name.title()

    @staticmethod
    def email_validator(email) -> str:
        pattern = r"^([a-zA-Z0-9]+\.?[a-zA-Z0-9]+)+@([a-zA-Z0-9]+\.)+[a-zA-Z0-9]{2,4}$"
        if re.match(pattern, email) is not None:
            return email

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


class Manager(models.Model):
    login = models.CharField(max_length=255, verbose_name='Логін')
    password = models.CharField(max_length=255, verbose_name='Пароль')
    first_name = models.CharField(max_length=255, verbose_name="Ім'я")
    last_name = models.CharField(max_length=255, verbose_name='Прізвище')
    email = models.EmailField(max_length=254, verbose_name='Електронна пошта')
    phone_number = models.CharField(max_length=13, blank=True, null=True, verbose_name='Номер телефона')
    chat_id = models.CharField(max_length=10, blank=True, null=True, verbose_name='Ідентифікатор чата')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    user = models.OneToOneField(AuUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Користувач')
    role = models.CharField(max_length=25, default=Role.DRIVER_MANAGER, choices=Role.choices)
    calendar = models.CharField(max_length=255, verbose_name='Календар змін водіїв')

    class Meta:
        verbose_name = 'Менеджера'
        verbose_name_plural = 'Менеджери'

    @classmethod
    def get_by_chat_id(cls, chat_id):
        """
        Returns user by chat_id
        :param chat_id: chat_id by which we need to find the user
        :type chat_id: str
        :return: user object or None if a user with such ID does not exist
        """
        try:
            user = cls.objects.get(chat_id=chat_id)
            return user
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Investor(models.Model):
    password = models.CharField(max_length=255, verbose_name='Пароль')
    first_name = models.CharField(max_length=255, verbose_name="Ім'я")
    last_name = models.CharField(max_length=255, verbose_name='Прізвище')
    email = models.EmailField(max_length=254, verbose_name='Електронна пошта')
    phone_number = models.CharField(max_length=13, blank=True, null=True, verbose_name='Номер телефона')
    role = models.CharField(max_length=25, default=Role.INVESTOR, choices=Role.choices)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    user = models.OneToOneField(AuUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Інвестора'
        verbose_name_plural = 'Інвестори'

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Vehicle(models.Model):
    class Currency(models.TextChoices):
        UAH = 'UAH', 'Гривня',
        USD = 'USD', 'Долар',
        EUR = 'EUR', 'Євро',

    name = models.CharField(max_length=255, verbose_name='Назва')
    type = models.CharField(max_length=20, default='Електро', verbose_name='Тип')
    licence_plate = models.CharField(max_length=24, unique=True, verbose_name='Номерний знак', db_index=True)
    registration = models.CharField(null=True, max_length=12, unique=True, verbose_name='Номер документа')
    vin_code = models.CharField(max_length=17, blank=True)
    chat_id = models.CharField(max_length=15, blank=True, null=True, verbose_name="Група автомобіля телеграм")
    gps_id = models.IntegerField(default=0)
    gps_imei = models.CharField(max_length=100, blank=True, default='')
    coord_time = models.DateTimeField(null=True, verbose_name="Час отримання координат")
    lat = models.DecimalField(null=True, decimal_places=6, max_digits=10, default=0, verbose_name="Широта")
    lon = models.DecimalField(null=True, decimal_places=6, max_digits=10, default=0, verbose_name="Довгота")
    car_status = models.CharField(max_length=18, null=False, default="Serviceable", verbose_name='Статус автомобіля')
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Менеджер авто')
    purchase_price = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name="Вартість автомобіля")
    currency = models.CharField(max_length=4, default=Currency.UAH, choices=Currency.choices,
                                verbose_name='Валюта покупки')
    currency_rate = models.DecimalField(decimal_places=2, max_digits=10, default=0,
                                        verbose_name="Курс валюти при покупці (НБУ)")
    car_earnings = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name="Заробіток авто")
    currency_back = models.CharField(max_length=4, default=Currency.USD, choices=Currency.choices,
                                     verbose_name='Валюта повернення коштів')
    investor_car = models.ForeignKey(Investor, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Машина інвестора')
    investor_percentage = models.DecimalField(decimal_places=2, max_digits=10, default=0.35,
                                              verbose_name="Відсоток інвестора")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Додано автомобіль')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Автомобіль'
        verbose_name_plural = 'Автомобілі'

    def __str__(self) -> str:
        return f'{self.licence_plate}'

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

    @staticmethod
    def gps_imei_validator(gps_imei):
        if len(gps_imei) <= 100:
            return gps_imei.upper()
        else:
            return None


class TransactionsConversation(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Автомобіль')
    investor = models.ForeignKey(Investor, on_delete=models.SET_NULL, null=True, verbose_name='Інвестор')
    sum_before_transaction = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сума в гривні")
    currency = models.CharField(max_length=4, verbose_name='Валюта покупки')
    currency_rate = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name="Курс валюти")
    sum_after_transaction = models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сума у валюті")

    class Meta:
        verbose_name = 'Виплату інвестору'
        verbose_name_plural = 'Виплати інвестору'

    def __str__(self) -> str:
        return f'{self.vehicle} {self.sum_before_transaction} {self.currency}'


class VehicleSpending(models.Model):
    class Category(models.TextChoices):
        FUEL = 'FUEL', 'Паливо'
        SERVICE = 'SERVICE', 'Сервісне обслуговування'
        REPAIR = 'REPAIR', 'Ремонт'
        WASHING = 'WASHING', 'Мийка'
        OTHER = 'OTHER', 'Інше'
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, verbose_name='Автомобіль')
    amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сума')
    category = models.CharField(max_length=255, choices=Category.choices, verbose_name='Категорія витрат')
    description = models.TextField(blank=True, null=True, verbose_name='Опис')
    photo = models.ImageField(upload_to='spending/', blank=True, null=True, verbose_name='Фото')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Витрату'
        verbose_name_plural = 'Витрати'

    def __str__(self) -> str:
        return f'{self.vehicle} {self.amount} {self.category}'


class Driver(User):
    ACTIVE = 'Готовий прийняти заказ'
    WITH_CLIENT = 'В дорозі'
    GET_ORDER = 'Приймаю замовлення'
    WAIT_FOR_CLIENT = 'Очікую клієнта'
    OFFLINE = 'Не працюю'
    RENT = 'Орендую авто'

    class Schema(models.TextChoices):
        RENT = 'RENT', 'Схема оренди'
        HALF = 'HALF', 'Схема 50/50'
        # BUYER = 'BUYER', 'Схема під викуп'
        CUSTOM = 'CUSTOM', 'Індивідуальний відсоток'

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Менеджер водіїв')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Автомобіль')
    worked = models.BooleanField(default=True, verbose_name='Працює')
    driver_status = models.CharField(max_length=35, null=False, default=OFFLINE, verbose_name='Статус водія')
    schema = models.CharField(max_length=20, choices=Schema.choices, default=Schema.HALF, verbose_name='Схема роботи')
    plan = models.IntegerField(default=12000, verbose_name='План водія')
    rental = models.IntegerField(default=6000, verbose_name='Вартість прокату')
    rate = models.DecimalField(decimal_places=2, max_digits=3, default=0.5, verbose_name='Відсоток водія')

    class Meta:
        verbose_name = 'Водія'
        verbose_name_plural = 'Водії'

    def get_driver_external_id(self, vendor: str):
        try:
            return Fleets_drivers_vehicles_rate.objects.get(fleet__name=vendor, driver=self,
                                                            partner=self.partner,
                                                            deleted_at=None).driver_external_id
        except ObjectDoesNotExist:
            return

    def get_kassa(self, vendor: str, week_number: [str, None] = None) -> float:
        driver_external_id = self.get_driver_external_id(vendor)
        current_date = pendulum.parse(week_number, tz="Europe/Kiev")
        qset = Payments.objects.filter(vendor_name=vendor, driver_id=driver_external_id) \
            .filter(report_from__lte=current_date.end_of('week'), report_to__gte=current_date.start_of('week'))
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


class DriverReshuffle(models.Model):
    calendar_event_id = models.CharField(max_length=100)
    swap_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, verbose_name="Автомобіль")
    driver_start = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True,
                                     verbose_name="Водій, що приймає авто", related_name="driver_start")
    driver_finish = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True,
                                      verbose_name="Водій, що віддає авто", related_name="driver_finish")
    swap_time = models.DateTimeField(verbose_name="Час початку/завершення зміни")


class RentInformation(models.Model):
    report_from = models.DateField(verbose_name='Дата звіту')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, verbose_name='Водій')
    rent_distance = models.DecimalField(null=True, blank=True, max_digits=6,
                                        decimal_places=2, verbose_name='Орендована дистанція')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Інформацію по оренді'
        verbose_name_plural = 'Інформація по орендах'


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

    class Meta:
        verbose_name = 'Клієнта'
        verbose_name_plural = 'Клієнти'


class ServiceStationManager(User):
    car_id = models.ManyToManyField('Vehicle', blank=True)
    fleet_id = models.ManyToManyField(Fleet, blank=True)
    service_station = models.OneToOneField('ServiceStation', on_delete=models.RESTRICT, verbose_name='Сервісний центр')

    class Meta:
        verbose_name = 'Менеджера сервісного центра'
        verbose_name_plural = 'Менеджери сервісних центрів'

    def __str__(self):
        return self.full_name()

    @staticmethod
    def save_name_of_service_station(name_of_service_station):
        ServiceStationManager.objects.create(name_of_service_station=name_of_service_station)


class SupportManager(User):
    client_id = models.ManyToManyField(Client, blank=True)
    driver_id = models.ManyToManyField(Driver, blank=True)

    class Meta:
        verbose_name = 'Менеджера служби підтримки'
        verbose_name_plural = 'Менеджери служби підтримки'


class BoltFleet(Fleet):
    pass


class NewUklonFleet(Fleet):
    token = models.CharField(max_length=40, default=None, null=True, verbose_name="Код автопарку")


class UberFleet(Fleet):
    pass


class NinjaFleet(Fleet):

    @staticmethod
    def start_report_interval(day):
        return timezone.localize(datetime.combine(day, time.min))

    @staticmethod
    def end_report_interval(day):
        return timezone.localize(datetime.combine(day, time.max))

    def download_report(self, day=None):
        report = Payments.objects.filter(report_from=self.start_report_interval(day),
                                         report_to=self.end_report_interval(day),
                                         vendor_name=self.name)
        return list(report)


class StatusChange(models.Model):
    driver = models.ForeignKey(Driver, null=True, on_delete=models.SET_NULL)
    vehicle = models.ForeignKey(Vehicle, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Назва статусу')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)


class Fleets_drivers_vehicles_rate(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, verbose_name='Агрегатор')
    driver = models.ForeignKey(Driver, null=True, on_delete=models.SET_NULL, verbose_name='Водій')
    driver_external_id = models.CharField(max_length=255, verbose_name='Унікальний індифікатор по автопарку')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')
    pay_cash = models.BooleanField(default=False, verbose_name='Оплата готівкою')

    def __str__(self) -> str:
        return ''

    class Meta:
        verbose_name = 'Водія в агрегаторах'
        verbose_name_plural = 'Водії в агрегаторах'


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

    def __str__(self):
        return f'{self.data}'


class GPS(PolymorphicModel):
    date_time = models.DateTimeField(null=False)
    lat = models.DecimalField(decimal_places=6, max_digits=10, default=0)
    lat_zone = models.CharField(max_length=1)
    lon = models.DecimalField(decimal_places=6, max_digits=10, default=0)
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
            except IntegrityError as error:
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
        verbose_name = 'Звіт про ремонт'
        verbose_name_plural = 'Звіти про ремонти'

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
        verbose_name = "Сервісний Центр"
        verbose_name_plural = 'Сервісні центри'

    def __str__(self):
        return f'{self.name}'


class Comment(models.Model):
    comment = models.TextField(verbose_name='Відгук')
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='ID в чаті')
    processed = models.BooleanField(default=False, verbose_name='Опрацьовано')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    def __str__(self):
        return self.comment

    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at']


class Order(models.Model):
    WAITING = 'Очікується'
    IN_PROGRESS = 'Виконується'
    COMPLETED = 'Виконаний'
    CANCELED = 'Скасовано клієнтом'
    ON_TIME = 'На певний час'

    STANDARD_TYPE = 'Звичайне замовлення'
    PERSONAL_TYPE = 'Персональний водій'

    from_address = models.CharField(max_length=255, verbose_name='Місце посадки')
    latitude = models.CharField(max_length=10, verbose_name='Широта місця посадки')
    longitude = models.CharField(max_length=10, verbose_name='Довгота місця посадки')
    to_the_address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Місце висадки')
    to_latitude = models.CharField(max_length=10, null=True, verbose_name='Широта місця висадки')
    to_longitude = models.CharField(max_length=10, null=True, verbose_name='Довгота місця висадки')
    phone_number = models.CharField(max_length=13, verbose_name='Номер телефона клієнта')
    chat_id_client = models.CharField(max_length=10, blank=True, null=True, verbose_name='Ідентифікатор чату клієнта')
    type_order = models.CharField(max_length=100, default=STANDARD_TYPE, verbose_name='Тип замовлення')
    info = models.CharField(max_length=255, null=True, verbose_name='Додаткова інформація')
    car_delivery_price = models.IntegerField(default=0, verbose_name='Сума за подачу автомобіля')
    sum = models.IntegerField(default=0, verbose_name='Загальна сума')
    order_time = models.DateTimeField(null=True, blank=True, verbose_name='Час подачі')
    payment_hours = models.IntegerField(null=True, verbose_name='Годин Сплачено')
    payment_method = models.CharField(max_length=70, default="Картка", verbose_name='Спосіб оплати')
    status_order = models.CharField(max_length=70, verbose_name='Статус замовлення')
    distance_gps = models.CharField(max_length=10, blank=True, null=True, verbose_name='Дистанція по GPS')
    distance_google = models.CharField(max_length=10, verbose_name='Дистанція Google')
    driver = models.ForeignKey(Driver, null=True, on_delete=models.RESTRICT, verbose_name='Виконувач')
    accepted_time = models.DateTimeField(blank=True, null=True, verbose_name='Час прийняття замовленя')
    finish_time = models.DateTimeField(blank=True, null=True, verbose_name='Час завершення замовлення')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Cтворено')
    comment = models.OneToOneField(Comment, null=True, on_delete=models.SET_NULL, verbose_name='Відгук')
    checked = models.BooleanField(default=False, verbose_name='Перевірено')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f'Замовлення №{self.pk}'


class ReportTelegramPayments(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Замовлення')

    provider_payment_charge_id = models.CharField(max_length=50,
                                                  verbose_name='Унікальний індитифікатор оплати в провайдері')
    telegram_payment_charge_id = models.CharField(max_length=50,
                                                  verbose_name='Унікальний індитифікатор оплати в телеграмі')
    currency = models.CharField(max_length=24, verbose_name='Валюта')
    total_amount = models.PositiveIntegerField(verbose_name='Сума оплати')

    class Meta:
        verbose_name = 'Звіт про оплату в телеграмі'
        verbose_name_plural = 'Звіти про оплату в телеграмі'

    def __str__(self):
        return self.provider_payment_charge_id


class FleetOrder(models.Model):
    SYSTEM_CANCEL = 'Скасовано системою'
    COMPLETED = 'Виконаний'
    CLIENT_CANCEL = 'Скасовано клієнтом'
    DRIVER_CANCEL = 'Скасовано водієм'

    order_id = models.CharField(max_length=50, verbose_name='Ідентифікатор замовлення')
    fleet = models.CharField(max_length=20, verbose_name='Агрегатор замовлення')
    driver = models.CharField(max_length=255, verbose_name='Водій')
    from_address = models.CharField(max_length=255, null=True, verbose_name='Місце посадки')
    destination = models.CharField(max_length=255, blank=True, null=True, verbose_name='Місце висадки')
    accepted_time = models.DateTimeField(blank=True, null=True, verbose_name='Час прийняття замовленя')
    finish_time = models.DateTimeField(blank=True, null=True, verbose_name='Час завершення замовлення')
    distance = models.DecimalField(null=True, decimal_places=2, max_digits=6, verbose_name="Відстань за маршрутом")
    state = models.CharField(max_length=255, blank=True, null=True, verbose_name='Статус замовлення')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Cтворено')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    class Meta:
        verbose_name = 'Стороннє замовлення'
        verbose_name_plural = 'Сторонні замовлення'


class Report_of_driver_debt(models.Model):
    driver = models.CharField(max_length=255, verbose_name='Водій')
    image = models.ImageField(upload_to='.', verbose_name='Фото')
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Видалено')

    class Meta:
        verbose_name = 'Звіт заборгованості водія'
        verbose_name_plural = 'Звіти заборгованості водіїв'
        ordering = ['driver']


class Event(models.Model):
    SICK_DAY = "Лікарняний"
    DAY_OFF = "Вихідний"
    full_name_driver = models.CharField(max_length=255, verbose_name='Водій')
    event = models.CharField(max_length=20, verbose_name='Подія')
    event_date = models.DateTimeField(null=True, blank=True, verbose_name='Час події')
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='Ідентифікатор чата')
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        verbose_name = 'Відпочинок і лікування'
        verbose_name_plural = 'Відпочинки і лікування'


class SubscribeUsers(models.Model):
    email = models.EmailField(max_length=254, verbose_name='Електронна пошта')
    created_at = models.DateTimeField(editable=False, auto_now=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Підписника'
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
        except ObjectDoesNotExist:
            return None


class JobApplication(models.Model):
    first_name = models.CharField(max_length=255, verbose_name='Ім\'я')
    last_name = models.CharField(max_length=255, verbose_name='Прізвище')
    email = models.EmailField(max_length=255, verbose_name='Електронна пошта')
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='Ідентифікатор чата')
    password = models.CharField(max_length=12, verbose_name='Пароль Uklon')
    phone_number = models.CharField(max_length=20, verbose_name='Телефон')
    license_expired = models.DateField(blank=True, verbose_name='Термін дії посвідчення')
    driver_license_front = models.ImageField(blank=True, upload_to='job/licenses/front',
                                             verbose_name='Лицьова сторона посвідчення')
    driver_license_back = models.ImageField(blank=True, upload_to='job/licenses/back',
                                            verbose_name='Тильна сторона посвідчення')
    photo = models.ImageField(blank=True, upload_to='job/photo', verbose_name='Фото водія')
    car_documents = models.ImageField(blank=True, upload_to='job/car', default="docs/default_car.jpg",
                                      verbose_name='Фото техпаспорту',)
    insurance = models.ImageField(blank=True, upload_to='job/insurance', default="docs/default_insurance.png",
                                  verbose_name='Автоцивілка')
    insurance_expired = models.DateField(default=date(2023, 12, 15), verbose_name='Термін дії автоцивілки')
    role = models.CharField(max_length=255, verbose_name='Роль')
    status_bolt = models.DateField(null=True, verbose_name='Опрацьована BOLT')
    status_uklon = models.DateField(null=True, verbose_name='Опрацьована Uklon')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачі заявки')

    def save(self, *args, **kwargs):
        if not self.pk:
            self.password = self.generate_password()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_password(length=12):
        chars = string.ascii_lowercase + string.digits
        password = ''.join(random.choice(chars) for _ in range(length - 2))
        password += random.choice(string.ascii_uppercase)
        password += random.choice(string.digits)
        return ''.join(random.sample(password, len(password)))

    def admin_photo(self):
        return admin_image_preview(self.photo)

    def admin_front(self):
        return admin_image_preview(self.driver_license_front)

    def admin_back(self):
        return admin_image_preview(self.driver_license_back)

    def admin_insurance(self):
        return admin_image_preview(self.insurance)

    def admin_car_document(self):
        return admin_image_preview(self.car_documents)

    admin_back.short_description = 'License back'
    admin_photo.short_description = 'Photo'
    admin_front.short_description = 'License front'
    admin_insurance.short_description = 'Insurance'
    admin_car_document.short_description = 'Car document'

    class Meta:
        verbose_name = 'Заявку'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


def admin_image_preview(image, default_image=None):
    if image:
        url = image.url
        return mark_safe(f'<a href="{url}"><img src="{url}" width="200" height="150"></a>')
    return None


class CarEfficiency(models.Model):
    report_from = models.DateField(verbose_name='Звіт за')
    vehicle = models.ForeignKey(Vehicle, null=True, on_delete=models.CASCADE, verbose_name='Автомобіль', db_index=True)
    total_kasa = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name='Каса')
    clean_kasa = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name='Чистий дохід')
    total_spending = models.DecimalField(null=True, decimal_places=2, max_digits=10, default=0, verbose_name='Витрати')
    mileage = models.DecimalField(decimal_places=2, max_digits=6, default=0, verbose_name='Пробіг, км')
    efficiency = models.DecimalField(decimal_places=2, max_digits=4, default=0, verbose_name='Ефективність, грн/км')
    partner = models.ForeignKey(Partner, null=True, on_delete=models.SET_NULL, verbose_name='Партнер')

    class Meta:
        verbose_name = 'Ефективність автомобіля'
        verbose_name_plural = 'Ефективність автомобілів'

    def __str__(self):
        return str(self.vehicle)


class DriverEfficiency(models.Model):
    report_from = models.DateField(verbose_name='Звіт за')
    driver = models.ForeignKey(Driver, null=True, on_delete=models.SET_NULL, verbose_name='Водій', db_index=True)
    total_kasa = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name='Каса')
    total_orders = models.IntegerField(default=0, verbose_name="Замовлень за день")
    accept_percent = models.IntegerField(default=0, verbose_name="Відсоток прийнятих замовлень")
    average_price = models.DecimalField(decimal_places=2, max_digits=6, default=0, verbose_name='Середній чек, грн')
    mileage = models.DecimalField(decimal_places=2, max_digits=6, default=0, verbose_name='Пробіг, км')
    efficiency = models.DecimalField(decimal_places=2, max_digits=6, default=0, verbose_name='Ефективність, грн/км')
    road_time = models.DurationField(null=True, blank=True, verbose_name='Час в дорозі')
    online_time = models.DurationField(null=True, blank=True, verbose_name='Час онлайн')
    partner = models.ForeignKey(Partner, null=True, on_delete=models.CASCADE, verbose_name='Партнер')

    class Meta:
        verbose_name = 'Ефективність водія'
        verbose_name_plural = 'Ефективність водіїв'

    def __str__(self):
        return f"{self.driver}"


class UseOfCars(models.Model):
    user_vehicle = models.CharField(max_length=255, verbose_name='Користувач автомобіля')
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='Індетифікатор чата')
    licence_plate = models.CharField(max_length=24, verbose_name='Номерний знак')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата використання авто')
    end_at = models.DateTimeField(null=True, blank=True, verbose_name='Кінець використання авто')

    class Meta:
        verbose_name = 'Користувача автомобіля'
        verbose_name_plural = 'Користувачі автомобілів'

    def __str__(self):
        return f"{self.user_vehicle}: {self.licence_plate}"


class ParkSettings(models.Model):
    key = models.CharField(max_length=255, verbose_name='Ключ')
    value = models.CharField(max_length=255, verbose_name='Значення')
    description = models.CharField(max_length=255, null=True, verbose_name='Опиc')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    class Meta:
        verbose_name = 'Налаштування автопарка'
        verbose_name_plural = 'Налаштування автопарків'

    def __str__(self):
        return f'{self.value}'

    @staticmethod
    def get_value(key, default=None, **kwargs):
        try:
            setting = ParkSettings.objects.get(key=key, **kwargs)
        except ObjectDoesNotExist:
            return default
        return setting.value

    @classmethod
    def get_key(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            print(setting.key)
        except (ProgrammingError, ObjectDoesNotExist):
            return default


class Service(PolymorphicModel):
    key = models.CharField(max_length=255, verbose_name='Ключ')
    value = models.CharField(max_length=255, verbose_name='Значення')
    description = models.CharField(max_length=255, null=True, verbose_name='Опиc')

    class Meta:
        verbose_name = 'Сервіс'
        verbose_name_plural = 'Сервіси'

    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
        except (ProgrammingError, ObjectDoesNotExist):
            return default
        return setting.value


class BoltService(Service):
    pass


class NewUklonService(Service):
    pass


class UaGpsService(Service):
    pass


class UberService(Service):
    pass


class UberSession(models.Model):
    session = models.CharField(max_length=255, verbose_name='Ідентифікатор сесії')
    cook_session = models.CharField(max_length=255, verbose_name='Ідентифікатор cookie')
    uber_uuid = models.UUIDField(verbose_name="Код автопарку Uber")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')


class NewUklonPaymentsOrder(models.Model):
    report_from = models.DateTimeField(verbose_name='Репорт з')
    report_to = models.DateTimeField(verbose_name='Репорт по')
    report_file_name = models.CharField(max_length=255, verbose_name='Назва файлу')
    full_name = models.CharField(max_length=255, verbose_name='ПІ водія')
    signal = models.CharField(max_length=8, verbose_name='Унікальний індифікатор водія')
    total_rides = models.PositiveIntegerField(verbose_name='Кількість поїздок')
    total_distance = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Пробіг під замовлення')
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Готівкою')
    total_amount_cach_less = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='На гаманець')
    total_amount_on_card = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='На картку')
    total_amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна сума')
    tips = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові')
    bonuses = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Бонуси')
    fares = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Штрафи')
    comission = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Комісія Uklon')
    total_amount_without_comission = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Разом')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    vendor_name = 'NewUklon'


class BoltPaymentsOrder(models.Model):
    report_from = models.DateTimeField(verbose_name='Репорт з')
    report_to = models.DateTimeField(verbose_name='Репорт по')
    report_file_name = models.CharField(max_length=255, verbose_name='Назва файлу')
    driver_full_name = models.CharField(max_length=24, verbose_name='ПІ водія')
    mobile_number = models.CharField(max_length=24, verbose_name='Унікальний індифікатор водія')
    range_string = models.CharField(max_length=50, verbose_name='Період')
    total_amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальний тариф')
    cancels_amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Плата за скасування')
    autorization_payment = models.DecimalField(decimal_places=2, max_digits=10,
                                               verbose_name='Авторизаційцний платіж (платіж)')
    autorization_deduction = models.DecimalField(decimal_places=2, max_digits=10,
                                                 verbose_name='Авторизаційцний платіж (відрахування)')
    additional_fee = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Додатковий збір')
    fee = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Комісія Bolt')
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Поїздки за готівку')
    discount_cash_trips = models.DecimalField(decimal_places=2, max_digits=10,
                                              verbose_name='Сума знижки Bolt за готівкові поїздки')
    driver_bonus = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Водійський бонус')
    compensation = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Компенсації')
    refunds = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Повернення коштів')
    tips = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові')
    weekly_balance = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Тижневий баланс')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    vendor_name = 'Bolt'


class UberPaymentsOrder(models.Model):
    report_from = models.DateTimeField(verbose_name='Репорт з')
    report_to = models.DateTimeField(verbose_name='Репорт по')
    report_file_name = models.CharField(max_length=255, verbose_name='Назва файла')
    driver_uuid = models.UUIDField(verbose_name='Унікальний індитифікатор водія')
    first_name = models.CharField(max_length=24, verbose_name='Імя водія')
    last_name = models.CharField(max_length=24, verbose_name='Прізвище водія')
    total_amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна дохід')
    total_clean_amout = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна дохід - Чистий тариф')
    total_amount_cach = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Виплати')
    transfered_to_bank = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Перераховано на банківський рахунок')
    returns = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Відшкодування та витрати')
    tips = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові')
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Партнер')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    vendor_name = 'Uber'


class UserBank(models.Model):
    chat_id = models.CharField(blank=True, max_length=10, verbose_name='Індетифікатор чата')
    duty = models.IntegerField(default=0, verbose_name='Борг')

    class Meta:
        verbose_name = 'Банк боргів'
        verbose_name_plural = 'Банк боргів'


    @staticmethod
    def get_duty(chat_id):
        return UserBank.objects.filter(chat_id=chat_id).first()


