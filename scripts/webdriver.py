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
from fake_useragent import UserAgent
from app.models import *


def clickandclear(element):
    element.click()
    element.clear()


class SeleniumTools:
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
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument("--no-sandbox")
            options.add_argument("--screen-size=1920,1080")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-extensions")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={user_agent}')

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
            shutil.copyfile(files[0], os.path.join(os.getcwd(), fname))
        for filename in files:
            if '.csv' in filename:
                file_path = os.path.join(folder, filename)
                os.remove(file_path)

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.driver = None


class Uber(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False,
                 base_url=f"{UberService.get_value('BASE_URL')}", remote=False, profile=None):
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

    def login_v2(self, link=f"{UberService.get_value('UBER_LOGIN_V2_1')}"):
        self.driver.get(link)
        self.login_form(UberService.get_value('UBER_LOGIN_V2_2.1'), UberService.get_value('UBER_LOGIN_V2_2.2'), By.ID)
        self.force_opt_form()
        self.otp_code_v2()
        # self.otp_code_v1()
        self.password_form(UberService.get_value('UBER_LOGIN_V2_3.1'), UberService.get_value('UBER_LOGIN_V2_3.2'),
                           By.ID)
        if self.sleep:
            time.sleep(self.sleep)

    def login_v3(self, link=f"{UberService.get_value('UBER_LOGIN_V3_1')}"):
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
        if self.sleep:
            time.sleep(self.sleep)

    def password_form_v3(self):
        el = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, UberService.get_value('UBER_PASSWORD_FORM_V3_1'))))
        el.clear()
        el.send_keys(ParkSettings.get_value("UBER_PASSWORD"))
        el = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, UberService.get_value('UBER_PASSWORD_FORM_V3_2'))))
        el.click()

    def login(self, link=f"{UberService.get_value('UBER_LOGIN_1')}"):
        self.driver.get(link)
        self.login_form(UberService.get_value('UBER_LOGIN_2.1'), UberService.get_value('UBER_LOGIN_2.2'), By.CLASS_NAME)
        self.otp_code_v1()
        self.password_form(UberService.get_value('UBER_LOGIN_3.1'), UberService.get_value('UBER_LOGIN_3.2'),
                           By.CLASS_NAME)
        if self.sleep:
            time.sleep(self.sleep)

    def generate_payments_order(self):
        url = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_1')}"
        xpath = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_2')}"
        self.get_target_page_or_login(url, xpath, self.login_v3)
        self.driver.get_screenshot_as_file('generate_payments_order.png')
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        self.driver.find_element(By.XPATH, xpath).click()
        try:
            xpath = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_3')}"
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.driver.find_element(By.XPATH, xpath).click()
        except Exception:
            try:
                xpath = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_3')}"
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()
            except Exception:
                xpath = f"{UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_4')}"
                WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.find_element(By.XPATH, xpath).click()

        if self.day:
            self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_5')).click()
            start = self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_6'))
            start.send_keys(Keys.NULL)
            date_by_def = pendulum.now().start_of('week').subtract(days=7)
            if date_by_def.month - self.day.month == -1:  # if month of day is different from month of last week Monday
                self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_7')).click()
            elif date_by_def.month - self.day.month > 0:
                for _ in range(date_by_def.month - self.day.month):
                    self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_8')).click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_9")}{self.day.strftime("%-d")}]').click()
            end = self.driver.find_element(By.XPATH, UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_10"))
            end.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_9")}"{self.day.strftime("%-d")}"]').click()

        else:
            self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_5')).click()
            start = self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_6'))
            start.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_11')).click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{self.start_of_week().strftime("%B")}")]])').click()
            self.driver.find_element(By.XPATH, UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_13")).click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{self.start_of_week().strftime("%Y")}")]])').click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_9")}{self.start_of_week().day}]').click()
            end = self.driver.find_element(By.XPATH, UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_10"))
            end.send_keys(Keys.NULL)
            self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_11')).click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{self.end_of_week().strftime("%B")}")]])').click()
            self.driver.find_element(By.XPATH, UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_13")).click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_12")}{self.end_of_week().strftime("%Y")}")]])').click()
            self.driver.find_element(By.XPATH,
                                     f'{UberService.get_value("UBER_GENERATE_PAYMENTS_ORDER_9")}{self.end_of_week().day}]').click()

        self.driver.find_element(By.XPATH, UberService.get_value('UBER_GENERATE_PAYMENTS_ORDER_14')).click()
        return f'{self.payments_order_file_name()}'

    def download_payments_order(self):
        if os.path.exists(f'{self.payments_order_file_name()}'):
            print('Report already downloaded')
            return

        self.generate_payments_order()
        download_button = f"{UberService.get_value('UBER_DOWNLOAD_PAYMENTS_ORDER_1')}"
        try:
            in_progress_text = f"{UberService.get_value('UBER_DOWNLOAD_PAYMENTS_ORDER_2')}"
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 600).until_not(EC.presence_of_element_located((By.XPATH, in_progress_text)))
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, download_button)))
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
        start = self.start_of_day() if self.day else self.start_of_week()
        end = self.end_of_day() if self.day else self.end_of_week().end_of('day')

        sd, sy, sm = start.strftime("%d"), start.strftime("%Y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%Y"), end.strftime("%m")
        return f'{sy}{sm}{sd}-{ey}{em}{ed}-payments_driver'

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        self.logger.info(f'Uber {self.file_patern()}.csv')
        start_date = self.start_of_day() if self.day else self.start_of_week()
        end_date = self.end_of_day() if self.day else self.end_of_week()

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
                            report_from=start_date,
                            report_to=end_date,
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
                            report_from=start_date,
                            report_to=end_date,
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
                    if not (digits) or (not all(digits)) or len(digits) != 4:
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
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_1')).send_keys(otp[0])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_2')).send_keys(otp[1])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_3')).send_keys(otp[2])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_4')).send_keys(otp[3])
            # self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_5')).click()
            break

    def wait_code_form(self, id):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, id)))
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
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V1_1')).send_keys(otp)
            self.driver.find_element(By.CLASS_NAME, UberService.get_value('UBER_OTP_CODE_V1_2')).click()
            break

    def force_opt_form(self):
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.presence_of_element_located((By.ID, UberService.get_value('UBER_FORCE_OPT_FORM'))))
            self.driver.find_element(By.ID, UberService.get_value('UBER_FORCE_OPT_FORM')).click()
        except Exception as e:
            # self.logger.error(str(e))
            pass

    def password_form(self, id, button, selector):
        try:
            WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, id)))
            el = self.driver.find_element(By.ID, id)
            el.send_keys(ParkSettings.get_value("UBER_PASSWORD"))
            self.driver.find_element(selector, button).click()
            self.driver.get_screenshot_as_file('UBER_PASSWORD.png')
        except Exception as e:
            self.logger.error(str(e))

    def login_form(self, id, button, selector):
        element = WebDriverWait(self.driver, self.sleep).until(EC.presence_of_element_located((By.ID, id)))
        element.send_keys(ParkSettings.get_value("UBER_NAME"))
        e = self.driver.find_element(selector, button)
        e.click()
        self.driver.get_screenshot_as_file('UBER_NAME.png')

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

    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        """Can download and save weekly report"""
        u = Uber(week_number=week_number, driver=False, sleep=sleep, headless=headless)
        report = UberPaymentsOrder.objects.filter(report_file_name=f'Uber {u.file_patern()}.csv')
        if not report:
            u = Uber(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            u.download_payments_order()
            u.save_report()
            u.quit()
            report = UberPaymentsOrder.objects.filter(report_file_name=f'Uber {u.file_patern()}.csv')
        return list(report)

    @staticmethod
    def download_daily_report(day=None, driver=True, sleep=5, headless=True):
        """Can download and save daily report if day is not None"""
        u = Uber(day=day, driver=False, sleep=sleep, headless=headless)
        report = UberPaymentsOrder.objects.filter(report_file_name=f'Uber {u.file_patern()}.csv')
        if not report:
            u = Uber(day=day, driver=driver, sleep=sleep, headless=headless)
            u.download_payments_order()
            u.save_report()
            u.quit()
            report = UberPaymentsOrder.objects.filter(report_file_name=f'Uber {u.file_patern()}.csv')
        return list(report)


class Bolt(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False,
                 base_url=f"{BoltService.get_value('BASE_URL')}", remote=False, profile=None):
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
        self.driver.get(f"{BoltService.get_value('BOLT_LOGIN_1')}")
        if self.sleep:
            time.sleep(self.sleep)
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_2'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_NAME"))
        element = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_3'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_PASSWORD"))
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_LOGIN_4')).click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        url = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_1')
        xpath = BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_2')
        self.get_target_page_or_login(url, xpath, self.login)
        if self.day:
            self.driver.get(BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_3'))
            if self.sleep:
                time.sleep(self.sleep)
            xpath = f'{BoltService.get_value("BOLT_DOWNLOAD_PAYMENTS_ORDER_4")}"{self.file_patern()}"]'
            element_date = self.driver.find_element(By.XPATH, xpath)
            element_date.find_element(By.XPATH, BoltService.get_value('BOLT_DOWNLOAD_PAYMENTS_ORDER_5')).click()
        else:
            self.driver.get(f"{url}/{self.file_patern()}")

        if self.sleep:
            time.sleep(self.sleep)
        if self.remote:
            self.get_last_downloaded_file_frome_remote(
                save_as=f'Bolt {self.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')
        else:
            self.get_last_downloaded_file(
                save_as=f'Bolt {self.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')

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

        self.logger.info(f'Bolt {self.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')

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


    @staticmethod
    def download_weekly_report(week_number=None, day=None, driver=True, sleep=5, headless=True):
        """Can download and save weekly report"""
        b = Bolt(week_number=week_number, day=day, driver=False, sleep=sleep, headless=headless)
        report = BoltPaymentsOrder.objects.filter(
            report_file_name=f'Bolt {b.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')
        if not report:
            b = Bolt(week_number=week_number, day=day, driver=driver, sleep=sleep, headless=headless)
            b.download_payments_order()
            b.quit()
            b.save_report()
            report = BoltPaymentsOrder.objects.filter(
                report_file_name=f'Bolt {b.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')
        return list(report)

    @staticmethod
    def download_daily_report(day=None, driver=True, sleep=5, headless=True):
        """Can download and save daily report if day is not None"""
        b = Bolt(day=day, driver=False, sleep=sleep, headless=headless)
        report = BoltPaymentsOrder.objects.filter(
            report_file_name=f'Bolt {b.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')
        if not report:
            b = Bolt(day=day, driver=driver, sleep=sleep, headless=headless)
            b.download_payments_order()
            b.quit()
            b.save_report()
            report = BoltPaymentsOrder.objects.filter(
                report_file_name=f'Bolt {b.file_patern()} – Kyiv Fleet 03_232 park Universal-auto.csv')
        return list(report)


class Uklon(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=3, headless=False,
                 base_url="https://partner.uklon.com.ua"):
        super().__init__('uklon', week_number=week_number, day=day)
        self.sleep = sleep
        if driver:
            self.driver = self.build_driver(headless)
        self.base_url = base_url

    def quit(self):
        self.driver.quit()

    def login(self):
        self.driver.get(self.base_url)
        username = self.driver.find_element("name", 'login')
        username.send_keys(ParkSettings.get_value("UKLON_NAME"))
        element = self.driver.find_element("name", "loginPassword")
        element.send_keys(ParkSettings.get_value("UKLON_PASSWORD"))
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
                        total_distance=int(row[3]),
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
        """Can download and save weekly report"""
        u = Uklon(week_number=week_number, day=day, driver=False, sleep=0, headless=headless)
        if u.payments_order_file_name() not in os.listdir(os.curdir):
            u = Uklon(week_number=week_number, day=day, driver=driver, sleep=sleep, headless=headless)
            u.login()
            u.download_payments_order()
        return u.save_report()


class NewUklon(SeleniumTools):
    def __init__(self, week_number=None, day=None, driver=True, sleep=5, headless=False,
                 base_url=f"{NewUklonService.get_value('BASE_URL')}", remote=False, profile=None):
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
        self.driver.get(NewUklonService.get_value('NEWUKLON_LOGIN_1'))
        if self.sleep:
            time.sleep(self.sleep)
        login = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_2'))
        login.send_keys(ParkSettings.get_value("UKLON_NAME"))
        password = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_3'))
        password.send_keys('')
        password.send_keys(ParkSettings.get_value("UKLON_PASSWORD"))

        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_LOGIN_4')).click()
        if self.sleep:
            time.sleep(self.sleep)

    def download_payments_order(self):
        url = NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_1')
        xpath = NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_2')
        self.get_target_page_or_login(url, xpath, self.login)
        self.driver.find_element(By.XPATH, xpath).click()
        if self.day:
            if self.sleep:
                time.sleep(self.sleep)
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_3')))).click()
            input_data = WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_4'))))
            input_data.click()
            input_data.send_keys(self.day.format("DD.MM.YYYY") + Keys.TAB + self.day.format("DD.MM.YYYY"))
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_5')))).click()
        else:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable(
                    (By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_6')))).click()

        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_DOWNLOAD_PAYMENTS_ORDER_7')).click()
        if self.sleep:
            time.sleep(self.sleep)
        if self.remote:
            self.get_last_downloaded_file_frome_remote(save_as=f'Uklon {self.file_patern()}.csv')
        else:
            self.get_last_downloaded_file(save_as=f'Uklon {self.file_patern()}.csv')

    def save_report(self):
        if self.sleep:
            time.sleep(self.sleep)
        items = []

        self.logger.info(f'Uklon {self.file_patern()}.csv')
        report = open(self.report_file_name(f'Uklon {self.file_patern()}.csv'))

        start_date = self.start_of_day() if self.day else self.start_of_week()
        end_date = self.end_of_day() if self.day else self.end_of_week()

        with report as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                order = NewUklonPaymentsOrder(
                    report_from=start_date,
                    report_to=end_date,
                    report_file_name=file.name,
                    full_name=row[0],
                    signal=row[1],
                    total_rides=float((row[2] or '0').replace(',', '')),
                    total_distance=float((row[3] or '0').replace(',', '')),
                    total_amount_cach=float((row[4] or '0').replace(',', '')),
                    total_amount_cach_less=float((row[5] or '0').replace(',', '')),
                    total_amount_on_card=float((row[6] or '0').replace(',', '')),
                    total_amount=float((row[7] or '0').replace(',', '')),
                    tips=float((row[8] or '0').replace(',', '')),
                    bonuses=float((row[9] or '0').replace(',', '')),
                    fares=float((row[10] or '0').replace(',', '')),
                    comission=float((row[11] or '0').replace(',', '')),
                    total_amount_without_comission=float((row[12] or '0').replace(',', '')))
                try:
                    order.save()
                except IntegrityError:
                    pass
                items.append(order)

        if not items:
            order = NewUklonPaymentsOrder(
                report_from=start_date,
                report_to=end_date,
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

    def payments_order_file_name(self):
        return self.report_file_name(self.file_patern())

    def file_patern(self):
        start = self.start_of_day() if self.day else self.start_of_week()
        end = self.end_of_day() if self.day else self.end_of_week().end_of('day')

        sd, sy, sm = start.strftime("%d"), start.strftime("%y"), start.strftime("%m")
        ed, ey, em = end.strftime("%d"), end.strftime("%y"), end.strftime("%m")
        return f'00.00.{sd}.{sm}.{sy} - 23.59.{ed}.{em}.{ey}'

    def wait_otp_code(self, user):
        r = redis.Redis.from_url(os.environ["REDIS_URL"])
        p = r.pubsub()
        p.subscribe(f'{user.phone_number} code')
        p.ping()
        otpa = []
        start = time.time()
        while True:
            try:
                if time.time() - start >= 180:
                    break
                otp = p.get_message()
                if otp:
                    otpa = list(f'{otp["data"]}')
                    otpa = list(filter(lambda d: d.isdigit(), otpa))
                    digits = [s.isdigit() for s in otpa]
                    if not (digits) or (not all(digits)) or len(digits) != 4:
                        continue
                    break
            except redis.ConnectionError as e:
                self.logger.error(str(e))
                p = r.pubsub()
                p.subscribe(f'{user.phone_number} code')
            time.sleep(1)
        return otpa


    @staticmethod
    def download_weekly_report(week_number=None, driver=True, sleep=5, headless=True):
        """Can download and save weekly report"""
        u = NewUklon(week_number=week_number, driver=False, sleep=sleep, headless=headless)
        report = NewUklonPaymentsOrder.objects.filter(report_file_name=f'Uklon {u.file_patern()}.csv')
        if not report:
            u = NewUklon(week_number=week_number, driver=driver, sleep=sleep, headless=headless)
            u.download_payments_order()
            u.quit()
            u.save_report()
            report = NewUklonPaymentsOrder.objects.filter(report_file_name=f'Uklon {u.file_patern()}.csv')
        return list(report)

    @staticmethod
    def download_daily_report(day=None, driver=True, sleep=5, headless=True):
        """Can download and save daily report if day is not None"""
        u = NewUklon(day=day, driver=False, sleep=sleep, headless=headless)
        report = NewUklonPaymentsOrder.objects.filter(report_file_name=f'Uklon {u.file_patern()}.csv')
        if not report:
            u = NewUklon(day=day, driver=driver, sleep=sleep, headless=headless)
            u.download_payments_order()
            u.quit()
            u.save_report()
            report = NewUklonPaymentsOrder.objects.filter(report_file_name=f'Uklon {u.file_patern()}.csv')
        return list(report)


class Privat24(SeleniumTools):
    def __init__(self, card=None, sum=None, driver=True, sleep=3, headless=False, base_url='https://next.privat24.ua/'):
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
        ActionChains(self.driver).move_to_element(password).send_keys(Keys.TAB + Keys.TAB + Keys.ENTER).perform()
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


class UaGps(SeleniumTools):
    def __init__(self, driver=True, sleep=5, headless=False, base_url=f"{UaGpsService.get_value('BASE_URL')}",
                 remote=False, profile=None):
        super().__init__('uagps', profile=profile)
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
        self.driver.get(self.base_url)
        time.sleep(self.sleep)
        user_field = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.ID, UaGpsService.get_value('UAGPS_LOGIN_1'))))
        clickandclear(user_field)
        user_field.send_keys(ParkSettings.get_value("UAGPS_LOGIN"))
        pass_field = self.driver.find_element(By.ID, UaGpsService.get_value('UAGPS_LOGIN_2'))
        clickandclear(pass_field)
        pass_field.send_keys(ParkSettings.get_value("UAGPS_PASSWORD"))
        self.driver.find_element(By.ID, UaGpsService.get_value('UAGPS_LOGIN_3')).click()
        time.sleep(self.sleep)


def get_report(week=False, day=None, week_number=None, driver=True, sleep=5, headless=True):
    owner = {"Fleet Owner": 0}
    reports = {}
    totals = {}
    salary = {}
    fleets = Fleet.objects.filter(deleted_at=None)
    for fleet in fleets:
        if week:
            all_drivers_report = fleet.download_weekly_report(week_number=week_number, driver=driver, sleep=sleep,
                                                              headless=headless)
        else:
            all_drivers_report = fleet.download_daily_report(day=day, driver=driver, sleep=sleep,
                                                             headless=headless)
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
    plan = dict(totals)
    totals = {k: f'Загальна каса {k}: %.2f\n' % v for k, v in totals.items()}
    totals = {k: v + reports[k] for k, v in totals.items()}
    for k, v in totals.items():
        if plan[k] > int(ParkSettings.get_value("DRIVER_PLAN", 10000)):
            totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]}\n" + "-" * 39
        else:
            incomplete = (int(ParkSettings.get_value("DRIVER_PLAN", 10000))-plan[k])/2
            totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]} - План ({'%.2f' % -incomplete}) = {'%.2f' % (salary[k]-incomplete)}\n" + \
                "-" * 39
    return owner, totals, plan


def download_and_save_daily_report(day=None, driver=False, sleep=5, headless=True):
    fleets = Fleet.objects.filter(deleted_at=None)
    for fleet in fleets:
        fleet.download_daily_report(day=day, driver=driver, sleep=sleep, headless=headless)
