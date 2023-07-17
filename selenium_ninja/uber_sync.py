import csv
import datetime
import json
import os
import time

import redis
from django.db import IntegrityError
from django.utils import timezone
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.models import UberService, ParkSettings, UberTrips, Payments
from scripts.redis_conn import redis_instance
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.synchronizer import Synchronizer


class UberSynchronizer(Synchronizer, SeleniumTools):
    def login(self, link=f"{UberService.get_value('UBER_LOGIN_V3_1')}"):
        self.driver.get(link)
        self.login_form(UberService.get_value('UBER_LOGIN_V3_2.1'), UberService.get_value('UBER_LOGIN_V3_2.2'), By.ID)
        try:
            self.password_form_v3()
        except TimeoutException:
            try:
                el = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.ID, UberService.get_value('UBER_LOGIN_V3_3'))))
                el.click()
                self.password_form_v3()
            except TimeoutException:
                self.otp_code_v2()

    def password_form_v3(self):
        el = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, UberService.get_value('UBER_PASSWORD_FORM_V3_1'))))
        el.clear()
        el.send_keys(ParkSettings.get_value("UBER_PASSWORD", partner=self.id))
        el = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, UberService.get_value('UBER_PASSWORD_FORM_V3_2'))))
        el.click()

    def click_uber_calendar(self, month, year, day):
        self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_11')).click()
        self.driver.find_element(By.XPATH,
                                 f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{month}")]]').click()
        self.driver.find_element(By.XPATH, UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_13")).click()
        self.driver.find_element(By.XPATH,
                                 f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{year}")]]').click()
        self.driver.find_element(By.XPATH,
                                 f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_9")}{day}]').click()

    def generate_payments_order(self, report_en, report_ua, pattern, day):
        url = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_1')}"
        xpath = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_2')}"
        self.get_target_element_of_page(url, xpath)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath))).click()
        try:
            xpath = report_en
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except Exception:
            try:
                xpath = report_en
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()
            except Exception:
                xpath = report_ua
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()
        try:
            self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_5')).click()
        except:
            pass
        self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_6')).click()

        self.click_uber_calendar(day.strftime("%B"),
                                 day.strftime("%Y"),
                                 day.day)
        self.click_uber_calendar(day.strftime("%B"),
                                 day.strftime("%Y"),
                                 day.day)
        self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_14')).click()
        return f'{self.payments_order_file_name(self.fleet, pattern, day)}'

    def download_payments_order(self, report_en, report_ua, pattern="Ninja", day=None):
        if os.path.exists(f'{self.payments_order_file_name(self.fleet, pattern, day)}'):
            self.logger.info('Report already downloaded')
            return

        self.generate_payments_order(report_en, report_ua, pattern, day)
        download_button = f"{UberService.get_value('UBER_DOWNLOAD_PAYMENTS_ORDER_1')}"
        try:
            in_progress_text = f"{UberService.get_value('UBER_DOWNLOAD_PAYMENTS_ORDER_2')}"
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 600).until_not(EC.presence_of_element_located((By.XPATH, in_progress_text)))
        except:
            pass
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, download_button)))
        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, download_button))).click()
        time.sleep(self.sleep)
        if self.remote:
            self.get_last_downloaded_file_frome_remote(self.file_pattern(self.fleet, pattern, day))
        else:
            self.get_last_downloaded_file(self.file_pattern(self.fleet, pattern, day))

    def save_report(self, day):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        file_order = self.payments_order_file_name(self.fleet, self.park_name(), day)
        self.logger.info(self.file_pattern(self.fleet, self.park_name(), day))
        if file_order is not None:
            try:
                with open(file_order, encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        if row[3] == "":
                            continue
                        if row[3] is None:
                            continue
                        order = Payments(
                            report_from=day,
                            vendor_name=self.fleet,
                            driver_id=str(row[0]),
                            full_name=f"{row[1]} {row[2]}",
                            total_amount=row[3],
                            total_amount_without_fee=row[3],
                            total_amount_cash=abs(float(row[6])) if row[6] else 0,
                            bonuses=row[5] or 0,
                            partner=self.get_partner())
                        try:
                            order.total_rides = UberTrips.objects.filter(report_from=day,
                                                                         driver_external_id=str(row[0])).count()
                            order.tips = row[9]
                        except IndexError:
                            order.tips = 0
                        try:
                            order.save()
                        except IntegrityError:
                            pass
                        items.append(order)

                    if not items:
                        order = Payments(
                            report_from=day,
                            vendor_name=self.fleet,
                            driver_id='00000000-0000-0000-0000-000000000000',
                            full_name='',
                            total_amount=0,
                            total_amount_without_fee=0,
                            bonuses=0,
                            total_amount_cash=0,
                            tips=0,
                            partner=self.get_partner())
                        try:
                            order.save()
                        except IntegrityError:
                            pass
            except FileNotFoundError:
                pass
        return items

    def save_trips_report(self, pattern="Trips", day=None):
        items = []

        self.logger.info(self.file_pattern(self.fleet, pattern, day))
        if self.payments_order_file_name(self.fleet, pattern, day) is not None:
            try:
                with open(self.payments_order_file_name(self.fleet, pattern, day), encoding="utf-8") as file:
                    reader = csv.reader(file)
                    next(reader)  # Advance past the header
                    for row in reader:
                        start = timezone.make_aware(datetime.datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S"))
                        trip = UberTrips(
                            report_from=day,
                            driver_external_id=row[1],
                            license_plate=row[5],
                            start_trip=start
                        )
                        if row[8] != '':
                            end = timezone.make_aware(datetime.datetime.strptime(row[8], "%Y-%m-%d %H:%M:%S"))
                            trip.end_trip = end
                        try:
                            trip.save()
                        except IntegrityError:
                            pass
                        items.append(trip)
                    if not items:
                        trip = UberTrips(
                            report_from=day,
                            driver_external_id='00000000-0000-0000-0000-000000000000',
                            license_plate=''
                        )
                        try:
                            trip.save()
                        except IntegrityError:
                            pass

            except FileNotFoundError:
                pass
        return items

    def wait_opt_code(self):

        p = redis_instance.pubsub()
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
                    if not digits or (not all(digits)) or len(digits) != 4:
                        continue
                    break
            except redis.ConnectionError as e:
                self.logger.error(str(e))
                p = redis_instance.pubsub()
                p.subscribe('code')
            time.sleep(1)
        return otpa

    def otp_code_v2(self):
        while True:
            if not self.wait_code_form('PHONE_SMS_OTP-0'):
                break
            otp = self.wait_opt_code()
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_1')).send_keys(otp[0])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_2')).send_keys(otp[1])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_3')).send_keys(otp[2])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_4')).send_keys(otp[3])
            # self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_5')).click()
            break

    def wait_code_form(self, pk):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, pk)))
            self.driver.find_element(By.ID, pk)
            self.driver.get_screenshot_as_file(f'{pk}.png')
            return True
        except Exception as e:
            self.logger.error(str(e))
            self.driver.get_screenshot_as_file(f'{pk}_error.png')
            return False

    def otp_code_v1(self):
        while True:
            if not self.wait_code_form('verificationCode'):
                break
            otp = self.wait_opt_code()
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V1_1')).send_keys(otp)
            self.driver.find_element(By.CLASS_NAME, UberService.get_value('UBER_OTP_CODE_V1_2')).click()
            break

    def force_opt_form(self):
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.ID, UberService.get_value('UBER_FORCE_OPT_FORM'))))
            self.driver.find_element(By.ID, UberService.get_value('UBER_FORCE_OPT_FORM')).click()
        except Exception as e:
            pass

    def password_form(self, pk, button, selector):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, pk)))
            el = self.driver.find_element(By.ID, id)
            el.send_keys(ParkSettings.get_value("UBER_PASSWORD", partner=self.id))
            self.driver.find_element(selector, button).click()
        except Exception as e:
            self.logger.error(str(e))

    def login_form(self, id, button, selector):
        element = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, id)))
        element.send_keys(ParkSettings.get_value("UBER_NAME", partner=self.id))
        e = self.driver.find_element(selector, button)
        e.click()

    def add_driver(self, phone_number, email, name, second_name):
        url = UberService.get_value('UBER_ADD_DRIVER_1')
        self.driver.get(f"{url}")
        if self.sleep:
            time.sleep(self.sleep)
        add_driver = self.driver.find_element(By.XPATH, UberService.get_value('UBER_ADD_DRIVER_2'))
        add_driver.click()
        if self.sleep:
            time.sleep(self.sleep)
        data = self.driver.find_element(By.XPATH, UberService.get_value('UBER_ADD_DRIVER_3'))
        data.click()
        data.send_keys(
            f'{phone_number[4:]}' + Keys.TAB + Keys.TAB + f'{email}' + Keys.TAB + f'{name}' + Keys.TAB + f'{second_name}')
        send_data = self.driver.find_element(By.XPATH, UberService.get_value('UBER_ADD_DRIVER_4'))
        send_data.click()
        if self.sleep:
            time.sleep(self.sleep)

    def get_all_vehicles(self):
        vehicles = {}
        url = UberService.get_value('UBERS_GET_ALL_VEHICLES_1')
        xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_2')
        self.get_target_element_of_page(url, xpath)
        i = 0
        while True:
            i += 1
            try:
                xpath = f'{UberService.get_value("UBERS_GET_ALL_VEHICLES_3")}[{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                try:
                    vehicle_uuid = json.loads(row.get_attribute("data-tracking-payload"))['vehicleUUID']
                except Exception:
                    continue
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_4')
                vehicle_name = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_5')
                vin_code = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_ALL_VEHICLES_6')
                licence_plate = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
            except TimeoutException:
                break
            vehicles[vehicle_uuid] = {'licence_plate': licence_plate, 'vin_code': vin_code, 'vehicle_name': vehicle_name}
        return vehicles

    def get_drivers_table(self):
        drivers = []
        try:
            vehicles = self.get_all_vehicles()
            url = UberService.get_value('UBERS_GET_DRIVERS_TABLE_1')
            xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_2')
            self.get_target_element_of_page(url, xpath)
        except TimeoutException:
            return drivers
        i = 0
        while True:
            i += 1
            try:
                self.driver.refresh()
                time.sleep(self.sleep)
                xpath = f'{UberService.get_value("UBERS_GET_DRIVERS_TABLE_3")}[{i}]'
                row = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_4')
                name = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_5')
                email = WebDriverWait(row, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_6')
                phone_number = WebDriverWait(row, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                try:
                    driver_external_id = json.loads(row.get_attribute("data-tracking-payload"))['driverUUID']
                except Exception:
                    continue
                try:
                    xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_8')
                    WebDriverWait(row, self.sleep).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                    xpath = UberService.get_value('UBERS_GET_DRIVERS_TABLE_9')
                    el = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    vehicle_uuid = json.loads(el.get_attribute("data-tracking-payload"))['vehicleUUID']
                    licence_plate = vehicles[vehicle_uuid]['licence_plate']
                    vehicle_name = vehicles[vehicle_uuid]['vehicle_name']
                    vin_code = vehicles[vehicle_uuid]['vin_code']
                except Exception:
                    licence_plate = ''
                    vehicle_name = ''
                    vin_code = ''
            except TimeoutException:
                break
            s_name = name.split()
            drivers.append({
                'fleet_name': self.fleet,
                'name': self.r_dup(s_name[0]),
                'second_name': self.r_dup(s_name[1]),
                'email': email if email else '',
                'phone_number': f"{phone_number[:4]}{phone_number[5:]}",
                'driver_external_id': driver_external_id,
                'pay_cash': True,
                'licence_plate': licence_plate,
                'vehicle_name': vehicle_name,
                'vin_code': vin_code,
            })

        return drivers

    def get_driver_status_from_map(self, search_text):
        raw_data = []
        try:
            xpath = "//div[@data-baseweb='table-custom']/div[@tabindex='0']"
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except TimeoutException:
            return raw_data
        i = 0
        while True:
            i += 1
            try:
                xpath = "//div[@data-baseweb='typo-labelsmall']"
                driver_name = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located((By.XPATH, xpath))).text
                xpath = "//div[@data-testid='driver-card']"
                card = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                payload_str = card.get_attribute('data-tracking-payload')
                payload_dict = json.loads(payload_str)
            except TimeoutException:
                break
            name_list = [x for x in driver_name.split(' ') if len(x) > 0]
            name, second_name = '', ''
            try:
                name, second_name = name_list[0], name_list[1]
            except IndexError:
                pass
            if payload_dict[f"{search_text}"]:
                raw_data.append((name, second_name))
                raw_data.append((second_name, name))
        return raw_data

    def get_driver_status(self):

        try:

            url = UberService.get_value('UBERS_GET_DRIVER_STATUS_1')
            # url = f"https://supplier.uber.com/orgs/49dffc54-e8d9-47bd-a1e5-52ce16241cb6/livemap"
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            xpath = UberService.get_value('UBERS_GET_DRIVER_STATUS_2')
            self.get_target_element_of_page(url, xpath)
            return {
                'online': self.get_driver_status_from_map('ONLINE'),
                'width_client': self.get_driver_status_from_map('IN_PROGRESS'),
                'wait': self.get_driver_status_from_map('ACCEPTED')
            }
        except WebDriverException as err:
            self.logger.error(err)

    def download_weekly_report(self, day):
        try:
            report = Payments.objects.filter(report_from=day, vendor_name=self.fleet)
            if not report:
                self.download_payments_order(UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_3'),
                                             UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_4'),
                                             day=day)
                self.save_report(day=day)
                report = Payments.objects.filter(report_from=day, vendor_name=self.fleet)
            return list(report)
        except Exception as err:
            self.logger.error(err)

    def download_trips(self, pattern, day):
        report = UberTrips.objects.filter(report_from=day)
        if not report:
            self.download_payments_order(UberService.get_value("UBER_GENERATE_TRIPS_1"),
                                         UberService.get_value("UBER_GENERATE_TRIPS_2"),
                                         pattern, day)
            self.save_trips_report(pattern, day)
            report = UberTrips.objects.filter(report_from=day)
        return list(report)
