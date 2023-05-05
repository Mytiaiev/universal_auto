import json
import logging
import os
import re
import time
import datetime

from django.utils import timezone
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException, WebDriverException, InvalidSessionIdException
from translators.server import tss

from app.models import Bolt, Driver, NewUklon, Uber, Fleets_drivers_vehicles_rate, Fleet, Vehicle, SeleniumTools, UaGps, \
    clickandclear, UseOfCars, RentInformation, StatusChange, ParkSettings, NewUklonFleet

LOGGER.setLevel(logging.WARNING)


class Synchronizer:

    def __init__(self, chrome_driver=None):
        if chrome_driver is None:
            super().__init__(driver=True, sleep=5, headless=True)
        else:
            super().__init__(driver=False, sleep=5, headless=True)
            self.driver = chrome_driver

    def try_to_execute(self, func_name, *args, **kwargs):
        if not self.driver.service.is_connectable():
            print('###################### Driver recreating... ########################')
            self.driver = self.build_driver()
            time.sleep(self.sleep)
        try:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located((By.XPATH, '//div')))
        except InvalidSessionIdException:
            print('###################### Session recreating... ########################')
            self.driver = self.build_driver()
            time.sleep(self.sleep)
        except TimeoutException:
            pass
        return getattr(self, func_name)(*args, **kwargs)

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
                self.driver.get(url)
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.logger.info(f'Got the page using authorization {url}')

    def create_driver(self, **kwargs):
        try:
            fleet = Fleet.objects.get(name=kwargs['fleet_name'])
        except Driver.DoesNotExist:
            return
        drivers = Fleets_drivers_vehicles_rate.objects.filter(fleet=fleet,
                                                              driver_external_id=kwargs['driver_external_id'])
        if len(drivers) == 0:
            fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.create(
                fleet=fleet,
                driver=self.get_or_create_driver(**kwargs),
                vehicle=self.get_or_create_vehicle(**kwargs),
                driver_external_id=kwargs['driver_external_id'],
                pay_cash=kwargs['pay_cash'],
                withdraw_money=kwargs['withdraw_money'],
            )
            fleets_drivers_vehicles_rate.save()
            self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
            self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)
        else:
            for fleets_drivers_vehicles_rate in drivers:
                if any([
                    fleets_drivers_vehicles_rate.pay_cash != kwargs['pay_cash'],
                    fleets_drivers_vehicles_rate.withdraw_money != kwargs['withdraw_money']
                ]):
                    fleets_drivers_vehicles_rate.pay_cash = kwargs['pay_cash']
                    fleets_drivers_vehicles_rate.withdraw_money = kwargs['withdraw_money']
                    fleets_drivers_vehicles_rate.save(update_fields=['pay_cash', 'withdraw_money'])
                self.update_driver_fields(fleets_drivers_vehicles_rate.driver, **kwargs)
                self.update_vehicle_fields(fleets_drivers_vehicles_rate.vehicle, **kwargs)

    def update_driver_fields(self, driver, **kwargs):
        update_fields = []
        if driver.phone_number == '' and kwargs['phone_number'] != '':
            driver.phone_number = kwargs['phone_number']
            update_fields.append('phone_number')
        if driver.email == '' and kwargs['email'] != '':
            driver.email = kwargs['email']
            update_fields.append('email')
        if len(update_fields):
            driver.save(update_fields=update_fields)

    def update_vehicle_fields(self, vehicle, **kwargs):
        update_fields = []
        if vehicle.name == '' and kwargs['vehicle_name'] != '':
            vehicle.name = kwargs['vehicle_name']
            update_fields.append('vehicle_name')
        if vehicle.vin_code == '' and kwargs['vin_code'] != '':
            vehicle.vin_code = kwargs['vin_code']
            update_fields.append('vin_code')
        if len(update_fields):
            vehicle.save(update_fields=update_fields)

    def get_or_create_vehicle(self, **kwargs):
        licence_plate = kwargs['licence_plate']
        if len(licence_plate) == 0:
            licence_plate = 'Unknown car'
        try:
            vehicle = Vehicle.objects.get(licence_plate=licence_plate)
        except Vehicle.MultipleObjectsReturned:
            vehicle = Vehicle.objects.filter(licence_plate=licence_plate)[0]
        except Vehicle.DoesNotExist:
            vehicle = Vehicle.objects.create(
                name=kwargs['vehicle_name'],
                model='',
                type='',
                licence_plate=licence_plate,
                vin_code=kwargs['vin_code']
            )
            vehicle.save()
        return vehicle

    def get_driver_by_name(self, name, second_name):
        try:
            return Driver.objects.get(name=name, second_name=second_name)
        except Driver.MultipleObjectsReturned:
            return Driver.objects.filter(name=name, second_name=second_name)[0]

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
                t_name, t_second_name = self.split_name(self.translate_text(f'{kwargs["name"]} {kwargs["second_name"]}', 'uk'))
                try:
                    driver = self.get_driver_by_name(t_name, t_second_name)
                except Driver.DoesNotExist:
                    try:
                        driver = self.get_driver_by_name(t_second_name, t_name)
                    except Driver.DoesNotExist:
                        t_name, t_second_name = self.split_name(self.translate_text(f'{kwargs["name"]} {kwargs["second_name"]}', 'ru'))
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

    def validate_email(self, email):
        if '@' in email:
            return email
        else:
            return ''

    def validate_phone_number(self, phone_number):
        return ''.join([x for x in phone_number if x.isdigit() or x == '+'][:13])

    def get_drivers_table(self):
        raise NotImplementedError

    def synchronize(self):
        drivers = self.get_drivers_table()
        print(f'Received {self.__class__.__name__} drivers: {len(drivers)}')
        for driver in drivers:
            self.create_driver(**driver)


class BoltSynchronizer(Synchronizer, Bolt):

    def get_drivers_table(self):
        drivers = []
        url = f'{self.base_url}/company/58225/drivers'
        xpath = '//table[@class="table"]'
        self.get_target_element_of_page(url, xpath)
        # self.driver.get_screenshot_as_file('BoltSynchronizer.png')
        i_table = 0
        while True:
            i_table += 1
            try:
                xpath = f'//table[@class="table"][{i_table}]'
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                i = 0
                while True:
                    i += 1
                    try:
                        xpath = f'//table[@class="table"][{i_table}]/tbody/tr[{i}]/td[2]/span'
                        status_class = WebDriverWait(self.driver, self.sleep).until(
                            EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("class")
                        if 'success' not in status_class:
                            continue
                        xpath = f'//table[@class="table"][{i_table}]/tbody/tr[{i}]/td[1]/a'
                        name = WebDriverWait(self.driver, self.sleep).until(
                            EC.presence_of_element_located((By.XPATH, xpath))).text
                        xpath = f'//table[@class="table"][{i_table}]/tbody/tr[{i}]/td[3]/a'
                        email = WebDriverWait(self.driver, self.sleep).until(
                            EC.presence_of_element_located((By.XPATH, xpath))).text
                        xpath = f'//table[@class="table"][{i_table}]/tbody/tr[{i}]/td[4]/a'
                        phone_number = WebDriverWait(self.driver, self.sleep).until(
                            EC.presence_of_element_located((By.XPATH, xpath))).text
                        xpath = f'//table[@class="table"][{i_table}]/tbody/tr[{i}]/td[5]/span'
                        pay_cash = 'success' in WebDriverWait(self.driver, self.sleep).until(
                            EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("class")
                        s_name = self.split_name(name)
                        drivers.append({
                            'fleet_name': 'Bolt',
                            'name': s_name[0],
                            'second_name': s_name[1],
                            'email': self.validate_email(email),
                            'phone_number': self.validate_phone_number(phone_number),
                            'driver_external_id': phone_number,
                            'pay_cash': pay_cash,
                            'withdraw_money': False,
                            'licence_plate': '',
                            'vehicle_name': '',
                            'vin_code': '',

                        })
                    except TimeoutException:
                        break
            except TimeoutException:
                break
        return drivers

    def get_driver_status_from_map(self, search_text):
        raw_data = []
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Close']"))).click()
        except:
            pass
        try:
            xpath = f'//div[contains(@class, "map-overlay")]/div/div[1]/div[@role="tablist"]/div[{search_text}]'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        except TimeoutException:
            return raw_data
        i = 0
        while True:
            i += 1
            try:
                xpath = f'//div[contains(@class, "map-overlay")]/div/div/div[@role="button"][{i}]/div/div/div[1]/span/span'
                driver_name = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'//div[contains(@class, "map-overlay")]/div/div/div[@role="button"][{i}]/div/div/div[2]/span/span'
                driver_car = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                break
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name, car = '', '', ''
            try:
                name, second_name, car = name_list[0], name_list[1], driver_car.split(' ')[0]
            except IndexError:
                pass
            raw_data.append((name, second_name))
            raw_data.append((second_name, name))
        return raw_data

    def get_driver_status(self):
        try:
            url = f'{self.base_url}/v2/liveMap'
            xpath = f'//div[contains(@class, "map-overlay")]'
            self.get_target_element_of_page(url, xpath)
            return {
                'online': self.get_driver_status_from_map('1'),
                'width_client': self.get_driver_status_from_map('2'),
                'wait': self.get_driver_status_from_map('3')
            }
        except (TimeoutException,WebDriverException) as err:
            print(err.msg)

    def download_weekly_report(self):
        if self.payments_order_file_name() not in os.listdir(os.curdir):
            try:
                self.download_payments_order()
                print(f'Bolt weekly report has been downloaded')
            except Exception as err:
                print(err.msg)

    def add_driver(self, jobapplication):
        if not jobapplication.status_bolt:
            url = 'https://fleets.bolt.eu/company/58225/driver/add'
            self.driver.get(f"{url}")
            if self.sleep:
                time.sleep(self.sleep)
            form_email = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, 'email')))
            clickandclear(form_email)
            form_email.send_keys(jobapplication.email)
            form_phone_number = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, 'phone')))
            clickandclear(form_phone_number)
            form_phone_number.send_keys(jobapplication.phone_number)
            button = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, 'ember38')))
            button.click()
            if self.sleep:
                time.sleep(self.sleep)
            self.driver.find_element(By.XPATH, '//a[text()="Продовжити реєстрацію"]').click()
            new_window = self.driver.window_handles[1]
            self.driver.switch_to.window(new_window)
            form_first_name = self.driver.find_element(By.XPATH, '//input[@id="first_name"]')
            clickandclear(form_first_name)
            form_first_name.send_keys(jobapplication.first_name)
            form_last_name = self.driver.find_element(By.XPATH, '//input[@id="last_name"]')
            clickandclear(form_last_name)
            form_last_name.send_keys(jobapplication.last_name)
            self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
            if self.sleep:
                time.sleep(self.sleep)
            elements_to_select = [str(jobapplication.license_expired).split("-")[0],
                                  str(jobapplication.license_expired).split("-")[1],
                                  str(jobapplication.license_expired).split("-")[2],
                                  str(jobapplication.insurance_expired).split("-")[0],
                                  str(jobapplication.insurance_expired).split("-")[1],
                                  str(jobapplication.insurance_expired).split("-")[2]
                                  ]

            form_fields = self.driver.find_elements(By.XPATH, "//div[@class='form-group']")
            for i, select_elem in enumerate(elements_to_select):
                form_fields[i].click()
                dropdown_div = self.driver.find_element(By.XPATH,
                '//div[@class="ember-basic-dropdown-content-wormhole-origin"]/div[contains(@id, "ember-basic-dropdown-content-")]')
                dropdown_div.find_element(By.XPATH, f'.//a[.//span[text()="{select_elem}"]]').click()
            upload_elements = self.driver.find_elements(By.XPATH, "//label[contains(., 'Завантажити файл')]")
            file_paths = [
                            os.getcwd()+f"/data/mediafiles/{jobapplication.driver_license_front}",  #license_front
                            os.getcwd()+f"/data/mediafiles/{jobapplication.driver_license_back}", #license_back
                            os.getcwd()+f"/data/mediafiles/{jobapplication.car_documents}", #car_document
                            os.getcwd()+f"/data/mediafiles/{jobapplication.insurance}", #insurance
            ]
            for i, file_path in enumerate(file_paths):
                upload_element = upload_elements[i]
                upload_element.click()
                upload_input = upload_element.find_element(By.XPATH, "./input")
                # Execute JavaScript code to remove the display property from the element's style
                self.driver.execute_script("arguments[0].style.removeProperty('display');", upload_input)
                upload_input.send_keys(file_path)
            if self.sleep:
                time.sleep(self.sleep)

            submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit.click()
            jobapplication.status_bolt = datetime.datetime.now().date()
            jobapplication.save()


class UklonSynchronizer(Synchronizer, NewUklon):

    def get_drivers_table(self):
        drivers = []
        url = f'{self.base_url}/workspace/drivers'
        xpath = '//upf-drivers-list[@data-cy="driver-list"]'
        self.get_target_element_of_page(url, xpath)
        # self.driver.get_screenshot_as_file('UklonSynchronizer.png')
        driver_urls = []
        i = 0
        while True:
            i += 1
            try:
                xpath = f'//cdk-row[{i}]/cdk-cell[@data-cy="cell-FullName"]//a'
                url = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("href")
                driver_urls.append(url)
            except TimeoutException:
                break
        for url in driver_urls:
            self.driver.get(url)
            xpath = '//span[@data-cy="driver-name"]'
            self.get_target_element_of_page(url, xpath)
            name = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = '//dd[@data-cy="driver-email"]'
            email = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = '//span[@data-cy="driver-phone"]'
            phone_number = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            xpath = '//dd[@data-cy="driver-signal"]'
            driver_external_id = WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.XPATH, xpath))).text
            try:
                xpath = '//div[@class="mat-tab-labels"]/div[@aria-posinset="4"]'
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                xpath = '//mat-slide-toggle[@formcontrolname="walletToCard"]//input'
                withdraw_money = 'true' in WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("aria-checked")
            except TimeoutException:
                withdraw_money = False
            licence_plate = ''
            vehicle_name = ''
            vin_code = ''
            try:
                xpath = '//div/a[contains(@class, "tw-font-medium")]'
                vehicle_url = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).get_attribute("href")
                self.driver.get(vehicle_url)
                xpath = '//span[@data-cy="license-plate"]'
                self.get_target_element_of_page(vehicle_url, xpath)
                licence_plate = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = '//span[@data-cy="make-model-year"]'
                vehicle_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = '//dd[@data-cy="vin-code"]'
                vin_code = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                pass
            s_name = self.split_name(name)
            drivers.append({
                'fleet_name': 'NewUklon',
                'name': s_name[0],
                'second_name': s_name[1],
                'email': self.validate_email(email),
                'phone_number': self.validate_phone_number(phone_number),
                'driver_external_id': driver_external_id,
                'pay_cash': False,
                'withdraw_money': withdraw_money,
                'licence_plate': licence_plate,
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })
        return drivers

    def get_driver_status_from_table(self):
        online = []
        width_client = []
        try:
            xpath = '//div[@role="tab"]/div[text()="Поїздки"]'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            # xpath = f'//mat-select[@id="mat-select-4"]'
            # WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            # xpath = f'//mat-option[@id="mat-option-2"]'
            # WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            xpath = '//button[@data-cy="order-filter-apply-btn"]'
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
            time.sleep(self.sleep)
        except TimeoutException as err:
            print(err.msg)
            return {
                'online': online,
                'width_client': width_client,
                'wait': []
            }
        i = 0
        while i < 10:
            i += 1
            try:
                xpath = f'//table[@data-cy="trips-list-table"]/tbody/tr[{i}]/td[@data-cy="td-driver"]'
                driver_name = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'//table[@data-cy="trips-list-table"]/tbody/tr[{i}]/td[@data-cy="td-license-plate"]'
                driver_car = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'//table[@data-cy="trips-list-table"]/tbody/tr[{i}]/td[@data-cy="td-pickup-time"]'
                last_action_date = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'//table[@data-cy="trips-list-table"]/tbody/tr[{i}]/td[@data-cy="td-status"]/i'
                status = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).get_attribute('class')
            except TimeoutException:
                break
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name, car = '', '', ''
            try:
                name, second_name, car = name_list[0], name_list[1], driver_car.split(' ')[0]
            except IndexError:
                pass

            match = re.findall(r'(\d{1,2}).(\d{2}).(\d{4}).*(\d{2}):(\d{2})', last_action_date)
            date_time_delta = 1000000
            if len(match) > 0:
                date_time = datetime.datetime.strptime(
                    f'{match[0][0]}.{match[0][1]}.{match[0][2]}-{match[0][3]}:{match[0][4]}', '%d.%m.%Y-%H:%M'
                )
                date_time_delta = (datetime.datetime.now() - date_time).total_seconds()

            if ('blue' in status or date_time_delta < 60*30) and (name, second_name) not in online:
                online.append((name, second_name))
                online.append((second_name, name))

            if ('blue' in status or status == 'i-circle') and (name, second_name) not in width_client:
                width_client.append((name, second_name))
                width_client.append((second_name, name))

        return {
            'online': online,
            'width_client': width_client,
            'wait': []
        }

    def get_driver_status(self):
        try:
            url = f'{self.base_url}/workspace/orders'
            xpath = '//div[@role="tab"]/div[text()="Поїздки"]'
            self.get_target_element_of_page(url, xpath)
            return self.get_driver_status_from_table()
        except WebDriverException as err:
            print(err.msg)

    def withdraw_money(self):
        url = f'{self.base_url}/workspace/finance'
        xpath = "//div[text()='Гаманці водіїв']"
        self.get_target_page_or_login(url, xpath, self.login)
        self.driver.find_element(By.XPATH, xpath).click()
        if self.sleep:
            time.sleep(self.sleep)
        checkbox = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='mat-checkbox-inner-container']")))
        checkbox.click()
        sum_remain = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@formcontrolname='remaining']")))
        clickandclear(sum_remain)
        sum_remain.send_keys(ParkSettings.get_value("Залишок Uklon", 150))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button/span[text()=' Перевод на гаманець автопарку ']"))).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button/span[text()=' Перевести гроші ']"))).click()
        print('withdraw finished')

    def add_driver(self, jobapplication):
        url = 'https://partner-registration.uklon.com.ua/registration'
        self.driver.get(f"{url}")
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Обрати зі списку']"))).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='region-name' and contains(text(),'Київ')]"))).click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()
        form_phone_number = self.driver.find_element(By.XPATH, "//input[@type='tel']")
        clickandclear(form_phone_number)
        form_phone_number.send_keys(jobapplication.phone_number[4:])
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()

        # 2FA
        code = self.wait_otp_code(jobapplication)
        digits = self.driver.find_elements(By.XPATH, "//input")
        for i, element in enumerate(digits):
            element.send_keys(code[i])
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, "//label[@for='registration-type-fleet']").click()
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()
        if self.sleep:
            time.sleep(self.sleep)
        registration_fields = {"firstName": jobapplication.first_name,
                               "lastName": jobapplication.last_name,
                               "email": jobapplication.email,
                               "password": jobapplication.password}
        for field, value in registration_fields.items():
            element = self.driver.find_element(By.ID, field)
            clickandclear(element)
            element.send_keys(value)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()

        file_paths = [
            os.getcwd() + f"/data/mediafiles/{jobapplication.photo}",
            os.getcwd() + f"/data/mediafiles/{jobapplication.driver_license_front}",
            os.getcwd() + f"/data/mediafiles/{jobapplication.driver_license_back}",

        ]
        for i in range(3):
            if self.sleep:
                time.sleep(self.sleep)
            photo_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
            photo_input.send_keys(file_paths[i])
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'green')]"))).click()
            time.sleep(1)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'green')]"))).click()
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()
        fleet_code = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, "mat-input-2")))
        clickandclear(fleet_code)
        fleet_code.send_keys(os.environ.get("UKLON_TOKEN", NewUklonFleet.token))
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@color='accent']"))).click()
        jobapplication.status_uklon = datetime.datetime.now().date()
        jobapplication.save()

    def download_weekly_report(self):
        if self.payments_order_file_name() not in os.listdir(os.curdir):
            try:
                self.download_payments_order()
                print(f'Uklon weekly report has been downloaded')
            except Exception as err:
                print(err.msg)


class UberSynchronizer(Synchronizer, Uber):

    def login(self):
        # """ Don't login in UberSynchronizer cause this instance runs periodically"""
        self.login_v3()
        pass

    def get_all_vehicles(self):
        vehicles = {}
        url = f'{self.base_url}/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/vehicles'
        # url = f'{self.base_url}/orgs/2c5515cd-a4ed-4136-905f-99504677a324/vehicles'  #my
        xpath = '//div[@data-testid="paginated-table"]'
        self.get_target_element_of_page(url, xpath)
        # self.driver.get_screenshot_as_file('UberSynchronizer.png')
        i = 0
        while True:
            i += 1
            try:
                xpath = f'//div[@data-testid="paginated-table"]//div[@data-tracking-name="vehicle-table-row"][{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                try:
                    vehicleUUID = json.loads(row.get_attribute("data-tracking-payload"))['vehicleUUID']
                except Exception:
                    continue
                xpath = f'div/div/div[@data-testid="vehicle-info"]'
                vehicle_name = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'div[3]/div/div[1]'
                vin_code = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'div[3]/div/div[2]'
                licence_plate = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                break
            vehicles[vehicleUUID] = {'licence_plate': licence_plate, 'vin_code': vin_code, 'vehicle_name': vehicle_name}
        return vehicles

    def get_drivers_table(self):
        try:
            vehicles = self.get_all_vehicles()
            drivers = []
            url = f'{self.base_url}/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/drivers'
            # url = f'{self.base_url}/orgs/2c5515cd-a4ed-4136-905f-99504677a324/drivers'  #my
            self.driver.get(url)
            xpath = '//div[@data-testid="paginated-table"]'
            self.get_target_element_of_page(url, xpath)
        except TimeoutException:
            return []
        i = 0
        while True:
            i += 1
            try:
                xpath = f'//div[@data-testid="paginated-table"]//div[@data-tracking-name="driver-table-row"][{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                xpath = f'div[1]/div[2]/div[1]'
                name = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'div[4]/div/div[2]'
                email = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = f'div[4]/div/div[1]'
                phone_number = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                try:
                    driver_external_id = json.loads(row.get_attribute("data-tracking-payload"))['driverUUID']
                except Exception:
                    continue
                licence_plate = ''
                vehicle_name = ''
                vin_code = ''
                try:
                    xpath = f'//div[@data-tracking-name="search"]'
                    WebDriverWait(self.driver, self.sleep).until(
                        EC.presence_of_element_located((By.XPATH, xpath))).click()
                    xpath = f'div[3]'
                    WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
                    xpath = f'//div[@data-baseweb="popover"]//div[@data-testid="vehicle-search-row"][1]'
                    el = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    vehicleUUID = json.loads(el.get_attribute("data-tracking-payload"))['vehicleUUID']
                    licence_plate = vehicles[vehicleUUID]['licence_plate']
                    vehicle_name = vehicles[vehicleUUID]['vehicle_name']
                    vin_code = vehicles[vehicleUUID]['vin_code']
                except Exception:
                    pass
            except TimeoutException:
                break
            s_name = self.split_name(name)
            drivers.append({
                'fleet_name': 'Uber',
                'name': s_name[0],
                'second_name': s_name[1],
                'email': self.validate_email(email),
                'phone_number': self.validate_phone_number(phone_number),
                'driver_external_id': driver_external_id,
                'pay_cash': False,
                'withdraw_money': False,
                'licence_plate': licence_plate,
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })
        return drivers

    def get_driver_status_from_map(self, search_text):
        return []
        # Need to implement

    def get_driver_status(self):

        try:
            url = f"{self.base_url}/orgs/2c5515cd-a4ed-4136-905f-99504677a324/livemap"
            # url = f"https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/livemap"
            xpath = f'//div[@data-tracking-name="livemap"]'
            self.get_target_element_of_page(url, xpath)
            return {
                'online': self.get_driver_status_from_map('Онлайн'),
                'width_client': self.get_driver_status_from_map('У поїздці'),
                'wait': self.get_driver_status_from_map('Очікування')
            }
        except WebDriverException as err:
            print(err.msg)

    def download_weekly_report(self):
        if self.payments_order_file_name() not in os.listdir(os.curdir):
            try:
                self.download_payments_order()
                print(f'Uber weekly report has been downloaded')
            except Exception as err:
                print(err.msg)


class UaGpsSynchronizer(Synchronizer, UaGps):

    def generate_report(self, start_time, end_time, report_object):

        """
        :param start_time: time from which we need to get report
        :type start_time: datetime.datetime
        :param end_time: time to which we need to get report
        :type end_time: datetime.datetime
        :param report_object: license plate
        :type report_object: str
        :return: distance and time in rent
        """
        xpath = "//div[@title='Reports']"
        self.get_target_element_of_page(self.base_url, xpath)
        self.driver.find_element(By.XPATH, xpath).click()
        unit = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@id='report_templates_filter_units']")))
        unit.click()
        try:
            self.driver.find_element(By.XPATH, f'//div[starts-with(text(), "{report_object}")]').click()
        except:
            return 0, datetime.timedelta()
        from_field = self.driver.find_element(By.ID, "time_from_report_templates_filter_time")
        clickandclear(from_field)
        from_field.send_keys(start_time.strftime("%d %B %Y %H:%M"))
        from_field.send_keys(Keys.ENTER)
        to_field = WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.ID, "time_to_report_templates_filter_time")))
        clickandclear(to_field)
        to_field.send_keys(end_time.strftime("%d %B %Y %H:%M"))
        from_field.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, '//input[@value="Execute"]'))).click()
        if self.sleep:
            time.sleep(self.sleep)
        road_distance = self.driver.find_element(By.XPATH, "//tr[@pos='5']/td[2]").text
        rent_distance = float(road_distance.split(' ')[0])
        roadtimestr = self.driver.find_element(By.XPATH, "//tr[@pos='4']/td[2]").text
        roadtime = [int(i) for i in roadtimestr.split(':')]
        rent_time = datetime.timedelta(hours=roadtime[0], minutes=roadtime[1], seconds=roadtime[2])
        return rent_distance, rent_time

    # def get_rent_distance(self):
    #     now = timezone.localtime()
    #     start = timezone.datetime.combine(now, datetime.datetime.min.time()).astimezone()
    #     for _driver in Driver.objects.all():
    #         rent_distance = 0
    #         rent_time = datetime.timedelta()
    #         # car that have worked at that day
    #         working_cars = UseOfCars.objects.filter(created_at__gte=start,
    #                                                 created_at__lte=now)
    #         vehicles = Vehicle.objects.filter(driver=_driver)
    #         if vehicles:
    #             for vehicle in vehicles:
    #                 # check driver's car before they start work
    #                 first_use = working_cars.filter(licence_plate=vehicle.licence_plate).first()
    #                 if first_use:
    #                     rent_before = self.generate_report(start,
    #                                                        timezone.localtime(first_use.created_at),
    #                                                        vehicle.licence_plate)
    #                     rent_distance += rent_before[0]
    #                     rent_time += rent_before[1]
    #                     # check driver's car after work
    #                     last_use = list(working_cars.filter(licence_plate=vehicle.licence_plate))[-1]
    #                     if last_use.end_at:
    #                         rent_after = self.generate_report(timezone.localtime(last_use.end_at),
    #                                                           now,
    #                                                           vehicle.licence_plate)
    #                         rent_distance += rent_after[0]
    #                         rent_time += rent_after[1]
    #                 #  car not used in that day
    #                 else:
    #                     rent = self.generate_report(start, now, vehicle.licence_plate)
    #                     rent_distance += rent[0]
    #                     rent_time += rent[1]
    #         # driver work at that day
    #         driver_use = working_cars.filter(user_vehicle=_driver)
    #         if driver_use:
    #             for car in driver_use:
    #                 if car.end_at:
    #                     end = car.end_at
    #                 else:
    #                     end = now
    #                 rent_statuses = StatusChange.objects.filter(driver=_driver.id,
    #                                                             name__in=[Driver.ACTIVE, Driver.OFFLINE, Driver.RENT],
    #                                                             start_time__gte=timezone.localtime(car.created_at),
    #                                                             start_time__lte=timezone.localtime(end))
    #                 for status in rent_statuses:
    #                     if status.end_time:
    #                         end = status.end_time
    #                     else:
    #                         end = now
    #                     status_report = self.generate_report(timezone.localtime(status.start_time),
    #                                                          timezone.localtime(end),
    #                                                          car.licence_plate)
    #                     rent_distance += status_report[0]
    #                     rent_time += status_report[1]
    #         #             update today rent in db
    #         rent_today = RentInformation.objects.filter(driver_name=_driver,
    #                                                     created_at__date=timezone.now().date()).first()
    #         if rent_today:
    #             rent_today.rent_time = rent_time
    #             rent_today.rent_distance = rent_distance
    #             rent_today.save()
    #         else:
    #             #  create rent file for today
    #             RentInformation.objects.create(driver_name=_driver,
    #                                            driver=_driver,
    #                                            rent_time=rent_time,
    #                                            rent_distance=rent_distance)

    def get_rent_distance(self):
        now = timezone.localtime()
        start = timezone.datetime.combine(now, datetime.datetime.min.time()).astimezone()
        for _driver in Driver.objects.all():
            rent_distance = 0
            rent_time = datetime.timedelta()
            # car that have worked at that day
            working_cars = UseOfCars.objects.filter(created_at__gte=start,
                                                    created_at__lte=now)
            vehicles = Vehicle.objects.filter(driver=_driver)
            if vehicles:
                for vehicle in vehicles:
                    # check driver's car before they start work
                    first_use = working_cars.filter(licence_plate=vehicle.licence_plate).first()
                    if first_use:
                        rent_before = self.generate_report(start,
                                                           timezone.localtime(first_use.created_at),
                                                           vehicle.licence_plate)
                        rent_distance += rent_before[0]
                        rent_time += rent_before[1]
                        # check driver's car after work
                        last_use = list(working_cars.filter(licence_plate=vehicle.licence_plate))[-1]
                        if last_use.end_at:
                            rent_after = self.generate_report(timezone.localtime(last_use.end_at),
                                                              now,
                                                              vehicle.licence_plate)
                            rent_distance += rent_after[0]
                            rent_time += rent_after[1]
                    #  car not used in that day
                    else:
            # driver work at that day
                        rent_statuses = StatusChange.objects.filter(driver=_driver.id,
                                                                    name__in=[Driver.ACTIVE, Driver.OFFLINE, Driver.RENT],
                                                                    start_time__gte=timezone.localtime(start),
                                                                    start_time__lte=timezone.localtime(now))
                        for status in rent_statuses:
                            if status.end_time:
                                end = status.end_time
                            else:
                                end = now
                            status_report = self.generate_report(timezone.localtime(status.start_time),
                                                                 timezone.localtime(end),
                                                                 vehicle.licence_plate)
                            rent_distance += status_report[0]
                            rent_time += status_report[1]
            #             update today rent in db
            rent_today = RentInformation.objects.filter(driver_name=_driver,
                                                        created_at__date=timezone.now().date()).first()
            if rent_today:
                rent_today.rent_time = rent_time
                rent_today.rent_distance = rent_distance
                rent_today.save()
            else:
                #  create rent file for today
                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=rent_time,
                                               rent_distance=rent_distance)
