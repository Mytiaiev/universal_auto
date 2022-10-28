import csv
import datetime
import glob
import os
import sys
from django.db import models
from polymorphic.models import PolymorphicModel



class PaymentsOrder(models.Model):
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


class UklonPaymentsOrder(models.Model):
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
    def driver_id(self):
        return self.signal

    def report_text(self, name = None, rate = 0.35):
        return f'Uklon {name} {self.signal}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные(-{"%.2f" % float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate = 0.35):
        return -(self.kassa()) * rate

    def vendor(self):
        return 'uklon'

    def total_owner_amount(self, rate = 0.35):
        return -self.total_drivers_amount(rate)

    def kassa(self):
        return float(self.total_amount) * 0.81


class BoltPaymentsOrder(models.Model):
    report_from = models.DateTimeField()
    report_to = models.DateTimeField()
    report_file_name = models.CharField(max_length=255)
    driver_full_name = models.CharField(max_length=24)
    mobile_number = models.CharField(max_length=24)
    range_string =  models.CharField(max_length=50)
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

    def driver_id(self):
        return self.mobile_number

    def report_text(self, name=None, rate=0.65):
        name = name or self.driver_full_name
        return f'Bolt {name}: Касса({"%.2f" % self.kassa()}) * {"%.0f" % (rate*100)}% = {"%.2f" % (self.kassa() * rate)} - Наличные({"%.2f" % float(self.total_amount_cach)}) = {"%.2f" % self.total_drivers_amount(rate)}'

    def total_drivers_amount(self, rate = 0.65):
        res = self.total_cach_less_drivers_amount() * rate  + float(self.total_amount_cach)
        return res

    def total_cach_less_drivers_amount(self):
        return float(self.total_amount) + float(self.fee) + float(self.cancels_amount) + float(self.driver_bonus)

    def vendor(self):
        return 'bolt'
    
    def kassa(self):
        return (self.total_cach_less_drivers_amount()) 

    def total_owner_amount(self, rate=0.65):
        return self.total_cach_less_drivers_amount() * (1 - rate) - self.total_drivers_amount(rate)


class UberPaymentsOrder(models.Model):
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

    def driver_id(self):
        return self.driver_uuid

    def report_text(self, name=None, rate=0.65):
        name = name or f'{self.first_name} {self.last_name}'
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

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    second_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, max_length=254)
    phone_number = models.CharField(blank=True, max_length=13)
    chat_id = models.CharField(blank=True, max_length=9)
    created_at = models.DateTimeField(editable=False, auto_now=datetime.datetime.now())
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, editable=True)

    def __str__(self) -> str:
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
            pass


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
        
        
class Driver(User):
    fleet_id = models.ForeignKey('Fleet',  blank=True, null=True, on_delete=models.SET_NULL)
    driver_manager_id = models.ManyToManyField('DriverManager',  blank=True)
    partner_id = models.ManyToManyField('Partner',  blank=True)
    vehicle_id = models.ForeignKey('Vehicle',  blank=True, null=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.DRIVER)

    def get_driver_external_id(self, vendor:str) -> str:
        if Fleets_drivers_vehicles_rate.objects.filter(fleet__name=vendor, driver=self, deleted_at=None).exists():
            driver_external_id = Fleets_drivers_vehicles_rate.objects.get(fleet__name=vendor, driver=self, deleted_at=None).driver_external_id
        return driver_external_id
    
    def get_rate(self, verndor_rate:str) -> float:
        vendor = verndor_rate.vendor().capitalize()
        if Fleets_drivers_vehicles_rate.objects.filter(fleet__name=vendor, driver=self, deleted_at=None).exists():
            rate = float(Fleets_drivers_vehicles_rate.objects.get(fleet__name=vendor, driver=self, deleted_at=None).rate)
        return rate

class Fleet(PolymorphicModel):
    name = models.CharField(max_length=255)
    fees = models.DecimalField(decimal_places=2, max_digits=3, default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.name}'

class Client(User):
    support_manager_id = models.ManyToManyField('SupportManager',  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.CLIENT)

class Partner(User):
    fleet_id = models.ForeignKey(Fleet,  blank=True, null=True, on_delete=models.SET_NULL)
    driver_id = models.ManyToManyField(Driver,  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.PARTNER)

class DriverManager(User):
    driver_id = models.ManyToManyField(Driver,  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.DRIVER_MANAGER)

class ServiceStationManager(User):
    driver_id = models.ManyToManyField(Driver,  blank=True)
    fleet_id = models.ManyToManyField(Fleet,  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.SERVICE_STATION_MANAGER)

class SupportManager(User):
    client_id = models.ManyToManyField(Client,  blank=True)
    driver_id = models.ManyToManyField(Driver,  blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices, default=User.Role.SUPPORT_MANAGER)

class UberFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
       return Uber.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

class BoltFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return Bolt.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)

class UklonFleet(Fleet):
    def download_weekly_report(self, week_number=None, driver=True, sleep=5, headless=True):
        return Uklon.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep, headless=headless)


class Vehicle(models.Model):
    name = models.CharField(max_length=255)
    licence_plate = models.CharField(max_length=24)
    vin_code = models.CharField(max_length=17)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.licence_plate} {self.name}'

class Fleets_drivers_vehicles_rate(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver_external_id = models.CharField(max_length=255)
    rate = models.DecimalField(decimal_places=2, max_digits=3, default=0)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.driver.full_name} {self.fleet.name} {int(self.rate * 100)}%'

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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

from django.db import models
from app.models import Fleet


class SeleniumTools():
    def __init__(self, session, week_number=None):
        self.session_file_name = session
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        if(week_number):
            self.current_date = pendulum.parse(week_number, tz="Europe/Kiev")
        else:
            self.current_date = pendulum.now().start_of('week').subtract(days=3)
    
    def report_file_name(self, patern):
        filenames = os.listdir(os.curdir)
        for file in filenames:
            if re.search(patern, file):
                return file 

    def week_number(self):
        return f'{int(self.start_of_week().strftime("%W"))}'

    def start_of_week(self):
        return self.current_date.start_of('week')

    def end_of_week(self):
        return self.current_date.end_of('week')

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

    def build_driver(self, headless=False):
        options = Options()
        options = webdriver.ChromeOptions();
        options.add_experimental_option("prefs", {
            "download.default_directory": os.getcwd(),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })
        options.add_argument("--disable-infobars")
        options.add_argument("--enable-file-cookies")
        options.add_argument('--disable-blink-features=AutomationControlled')

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument("--no-sandbox")
            options.add_argument("--screen-size=1920,1080")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-extensions")
            options.add_argument('--disable-dev-shm-usage')    
            options.add_argument('--disable-software-rasterizer')
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")
            options.add_argument("--disable-notifications")

        driver = webdriver.Chrome(options=options, port=9514)
        return driver

class Uber(SeleniumTools):    
    def __init__(self, week_number=None, driver=True, sleep=3, headless=False, base_url="https://supplier.uber.com"):
        super().__init__('uber', week_number=week_number)
        self.sleep = sleep
        print(driver)
        if driver:
            self.driver = self.build_driver(headless)
            self.base_url = base_url

    def quit(self):
        self.driver.quit()

    def login_v2(self, link = "https://drivers.uber.com/"):
        self.driver.get(link)
        self.login_form('PHONE_NUMBER_or_EMAIL_ADDRESS', 'forward-button', By.ID)  
        self.force_opt_form()
        self.otp_code_v2()
        self.otp_code_v1()
        self.password_form('PASSWORD', 'forward-button', By.ID)
        if self.sleep:
            time.sleep(self.sleep)

    def login(self, link = "https://auth.uber.com/login/"):
        self.driver.get(link)
        self.login_form('userInput', 'next-button-wrapper', By.CLASS_NAME)
        self.otp_code_v1()
        self.password_form('password', 'next-button-wrapper', By.CLASS_NAME)
        if self.sleep:
            time.sleep(self.sleep)
    
    def generate_payments_order(self):
        self.driver.get(f"{self.base_url}/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/reports")
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.get_screenshot_as_file('generate_payments_order.png')
        menu = '//div[@data-testid="report-type-dropdown"]/div/div'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, menu)))
        self.driver.find_element(By.XPATH, menu).click()   
        try:
            xpath = '//ul/li/div[text()[contains(.,"Payments Driver")]]'
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except Exception:
            xpath = '//ul/li/div[text()[contains(.,"Payments driver")]]'
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        start = self.driver.find_element(By.XPATH, '(//input[@aria-describedby="datepicker--screenreader--message--input"])[1]')
        start.send_keys(Keys.NULL)
        self.driver.find_element(By.XPATH, f'//div[@aria-roledescription="button"]/div[text()={self.start_of_week().strftime("%-d")}]').click()
        end = self.driver.find_element(By.XPATH, '(//input[@aria-describedby="datepicker--screenreader--message--input"])[2]')
        end.send_keys(Keys.NULL)
        self.driver.find_element(By.XPATH, f'//div[@aria-roledescription="button"]/div[text()="{self.end_of_week().strftime("%-d")}"]').click()
        self.driver.find_element(By.XPATH, '//button[@data-testid="generate-report-button"]').click()

        return f'{self.payments_order_file_name()}'

    def download_payments_order(self):
        if os.path.exists(f'{self.payments_order_file_name()}'):
            print('Report already downloaded')
            return 
        self.generate_payments_order()
        download_button = '(//div[@data-testid="payment-reporting-table-row"]/div/div/div/div/button)[1]'
        try:
            in_progress_text = '//div[1][@data-testid="payment-reporting-table-row"]/div/div/div/div[text()[contains(.,"In progress")]]'
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 300).until_not(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, download_button)))
        except Exception as e:
            self.logger.error(str(e))
            pass 
        self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.XPATH, download_button))

    def payments_order_file_name(self):
        start = self.start_of_week()
        end  = self.end_of_week()
        sd, sy, sm = start.strftime("%d"), start.strftime("%Y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%Y"), end.strftime("%m")
        return f'{sy}{sm}{sd}-{ey}{em}{ed}-payments_driver-___.csv'

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        with open(self.payments_order_file_name()) as file:
            reader = csv.reader(file)
            next(reader)  # Advance past the header
            for row in reader:
                if row[3] == "":
                    continue
                if row[3] is None:
                    continue    
                order = UberPaymentsOrder(
                    report_from = self.start_of_week(),
                    report_to = self.end_of_week(),
                    report_file_name = self.payments_order_file_name(),
                    driver_uuid = row[0],
                    first_name = row[1],
                    last_name = row[2],
                    total_amount = row[3],
                    total_clean_amout = row[4] or 0,
                    returns = row[5] or 0,
                    total_amount_cach = row[6] or 0,
                    transfered_to_bank = row[7] or 0,
                    tips = row[8] or 0)

                order.save()
                items.append(order)
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
                    otpa = list(filter(lambda d: d.isdigit() , otpa))
                    digits = [s.isdigit() for s in otpa]
                    if not(digits) or (not all(digits)) or len(digits)!=4:
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
            self.driver.find_element(By.ID, "forward-button").click() 
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
            self.driver.find_element(By.CLASS_NAME,"next-button-wrapper").click()
            break
    
    def force_opt_form(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'alt-PHONE-OTP')))
            el = self.driver.find_element(By.ID, 'alt-PHONE-OTP').click()
        except Exception as e:
            self.logger.error(str(e))
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
        element = self.driver.find_element(By.ID, id)
        element.send_keys(os.environ["UBER_NAME"])
        self.driver.find_element(selector, button).click() 
        self.driver.get_screenshot_as_file('UBER_NAME.png')

    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        u = Uber(week_number=week_number, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir):
            u = Uber(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            u.login_v2()
            u.download_payments_order()
            u.quit()
        return u.save_report()


class Bolt(SeleniumTools):    
    def __init__(self, week_number=None, driver=True, sleep=3, headless=False, base_url="https://fleets.bolt.eu"):
        super().__init__('bolt', week_number=week_number)
        self.sleep = sleep
        if driver:
            self.driver = self.build_driver(headless)
            self.base_url = base_url
    
    def quit(self):
        self.driver.quit() 

    def login(self):
        self.driver.get(f"{self.base_url}/login")
        if self.sleep:
            time.sleep(self.sleep)
        element = self.driver.find_element(By.ID,'username')
        element.send_keys('')
        element.send_keys(os.environ["BOLT_NAME"])
        self.driver.find_element(By.ID, "password").send_keys(os.environ["BOLT_PASSWORD"])
        self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        self.driver.get(f"{self.base_url}/company/58225/reports/weekly/{self.file_patern()}")
    
    def file_patern(self):
        return f"{self.current_date.strftime('%Y')}W{self.week_number()}"
   
    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    
    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        with open(self.payments_order_file_name()) as file:
            reader = csv.reader(file)
            next(reader)
            next(reader)
            for row in reader:
                if row[0] == "":
                    break
                if row[0] is None:
                    break
                order = BoltPaymentsOrder(
                    report_from = self.start_of_week(),
                    report_to = self.end_of_week(),
                    report_file_name = file.name,
                    driver_full_name = row[0],
                    mobile_number = row[1],
                    range_string =  row[2],
                    total_amount = row[3],
                    cancels_amount = row[4],
                    autorization_payment = row[5],
                    autorization_deduction = row[6],
                    additional_fee=row[7],
                    fee=row[8],
                    total_amount_cach=row[9],
                    discount_cash_trips=row[10],
                    driver_bonus=row[11],
                    compensation=row[12] or 0,
                    refunds=row[13],
                    tips=row[14],
                    weekly_balance=row[15])
                order.save()
                items.append(order)
        return items

    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        b = Bolt(week_number=week_number, driver=False, sleep=0, headless=headless)
        if b.payments_order_file_name() not in os.listdir(os.curdir):
            b = Bolt(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            b.login()
            b.download_payments_order()
        return b.save_report()


class Uklon(SeleniumTools):    
    def __init__(self, week_number=None, driver=True, sleep=3, headless=False, base_url="https://partner.uklon.com.ua"):
        super().__init__('uklon', week_number=week_number)
        self.sleep = sleep
        if driver:
            self.driver = self.build_driver(headless)
            self.base_url = base_url

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element("name",'login').send_keys(os.environ["UKLON_NAME"])
        element = self.driver.find_element("name", "loginPassword").send_keys(os.environ["UKLON_PASSWORD"])
        self.driver.find_element("name", "Login").click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        url = f"{self.base_url}/partner/export/fares?page=1&pageSize=20&startDate={self.start_of_week_timestamp()}&endDate={self.end_of_week_timestamp()}&format=csv"
        self.driver.get(url)

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []
        report = open(self.report_file_name(self.file_patern()))

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
                                           total_distance=row[3],
                                           total_amount_cach=row[4],
                                           total_amount_cach_less=row[5],
                                           total_amount=row[6],
                                           total_amount_without_comission=row[7],
                                           bonuses=row[8])
                order.save()
                items.append(order)

        return items
    
    def start_of_week_timestamp(self):
        return round(self.start_of_week().timestamp())

    def end_of_week_timestamp(self):
        return round(self.end_of_week().timestamp())
    
    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def file_patern(self):
        start = self.start_of_week()
        end = self.end_of_week().end_of('day').add(hours=4)
        sd, sy, sm = start.strftime("%d"), start.strftime("%Y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%Y"), end.strftime("%m")
        return f'{sd}.{sm}.{sy}.+{ed}.{em}.{ey}|{start.strftime("%-m")}_{start.strftime("%-d")}_{sy}.+{end.strftime("%-m")}_{end.strftime("%-d")}_{ey}'

    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        u = Uklon(week_number=week_number, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir):
            u = Uklon(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            u.login()
            u.download_payments_order()
        return u.save_report()

def get_report(week_number = None, driver=True, sleep=5, headless=True):
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
                name = rate.driver.full_name
                reports[name] = reports.get(name, '') + r.report_text(name, float(rate.rate)) + '\n'
                totals[name] = totals.get(name, 0) + r.kassa()
                salary[name] = salary.get(name, 0) + r.total_drivers_amount(float(rate.rate))
                owner["Fleet Owner"] += r.total_owner_amount(float(rate.rate))
   
    totals = {k: f'Общаяя касса {k}: %.2f\n' % v  for k, v in totals.items()}
    totals = {k: v + reports[k]  for k, v in totals.items()}
    totals = {k: v + f'Зарплата за неделю {k}: %.2f\n' % salary[k] for k, v in totals.items()}
    return f'Fleet Owner: {"%.2f" % owner["Fleet Owner"]}\n\n' + '\n'.join(totals.values())
