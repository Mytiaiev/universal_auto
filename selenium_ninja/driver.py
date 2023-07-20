import re
import time
import os
from datetime import datetime

import redis
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver import DesiredCapabilities
from selenium.common import TimeoutException

from app.models import ParkSettings, UberService, UberSession, Partner, BoltService, NewUklonService, NewUklonFleet
from auto import settings
from scripts.redis_conn import redis_instance, get_logger


class SeleniumTools:
    def __init__(self, partner=None, remote=True, driver=True, sleep=5):
        self.partner = partner
        self.remote = remote
        self.sleep = sleep
        self.logger = get_logger()
        if driver:
            if self.remote:
                self.driver = self.build_remote_driver()
            else:
                self.driver = self.build_driver()

    @staticmethod
    def build_driver():
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
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_argument("--screen-size=1920,1080")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('''user-agent=Mozilla/5.0
         (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36''')

        driver = webdriver.Chrome(options=options, port=9514)
        return driver

    @staticmethod
    def build_remote_driver():
        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("--enable-file-cookies")
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')

        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('''user-agent=Mozilla/5.0
         (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36''')

        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptInsecureCerts'] = True

        driver = webdriver.Remote(
            os.environ['SELENIUM_HUB_HOST'],
            desired_capabilities=capabilities,
            options=options
        )
        return driver

    @staticmethod
    def download_from_bucket(path, filename):
        response = requests.get(path)
        local_path = os.path.join(os.getcwd(), f"Temp/{filename}.jpg")
        with open(local_path, "wb") as file:
            file.write(response.content)
        return local_path

    def quit(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.driver = None

    def bolt_login(self):
        self.driver.get(f"{BoltService.get_value('BOLT_LOGIN_URL')}")
        if self.sleep:
            time.sleep(self.sleep)
        element = WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_1'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_NAME", partner=self.partner))
        element = WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.ID, BoltService.get_value('BOLT_LOGIN_2'))))
        element.clear()
        element.send_keys(ParkSettings.get_value("BOLT_PASSWORD", partner=self.partner))
        self.driver.find_element(By.XPATH, BoltService.get_value('BOLT_LOGIN_3')).click()
        self.quit()

    def uklon_login(self):
        self.driver.get(NewUklonService.get_value('UKLON_LOGIN_1'))
        if self.sleep:
            time.sleep(self.sleep)
        login = self.driver.find_element(By.XPATH, NewUklonService.get_value('UKLON_LOGIN_2'))
        login.send_keys(ParkSettings.get_value("UKLON_NAME", partner=self.partner)[4:])
        password = self.driver.find_element(By.XPATH, NewUklonService.get_value('UKLON_LOGIN_3'))
        clickandclear(password)
        password.send_keys(ParkSettings.get_value("UKLON_PASSWORD", partner=self.partner))
        self.driver.find_element(By.XPATH, NewUklonService.get_value('UKLON_LOGIN_4')).click()
        self.quit()

    def add_driver(self, job_application):

        url = NewUklonService.get_value('NEWUKLON_ADD_DRIVER_1')
        self.driver.get(url)
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_2')))).click()
        WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_3')))).click()
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        form_phone_number = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_5'))
        clickandclear(form_phone_number)
        form_phone_number.send_keys(job_application.phone_number[4:])
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()

        # 2FA
        code = self.wait_otp_code(f'{job_application.phone_number} code')
        digits = self.driver.find_elements(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_6'))
        for i, element in enumerate(digits):
            element.send_keys(code[i])
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_7')).click()
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        registration_fields = {"firstName": job_application.first_name,
                               "lastName": job_application.last_name,
                               "email": job_application.email,
                               "password": job_application.password}
        for field, value in registration_fields.items():
            element = self.driver.find_element(By.ID, field)
            clickandclear(element)
            element.send_keys(value)
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()

        file_paths = [
            f"{settings.MEDIA_URL}{job_application.photo}",
            f"{settings.MEDIA_URL}{job_application.driver_license_front}",
            f"{settings.MEDIA_URL}{job_application.driver_license_back}",

        ]
        for i, file_path in enumerate(file_paths):
            if self.sleep:
                time.sleep(self.sleep)
            local_path = self.download_from_bucket(file_path, i)
            photo_input = self.driver.find_element(By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_8'))
            photo_input.send_keys(local_path)
            WebDriverWait(self.driver, self.sleep).until(
                ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_9')))).click()
            time.sleep(1)
            WebDriverWait(self.driver, self.sleep).until(
                ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_9')))).click()
            WebDriverWait(self.driver, self.sleep).until(
                ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        fleet_code = WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.ID, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_10'))))
        clickandclear(fleet_code)
        fleet_code.send_keys(ParkSettings.get_value("UKLON_TOKEN", NewUklonFleet.token))
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, NewUklonService.get_value('NEWUKLON_ADD_DRIVER_4')))).click()
        job_application.status_uklon = datetime.now().date()
        job_application.save()
        self.quit()

    def uber_login(self):
        self.driver.get(UberService.get_value('UBER_LOGIN_URL'))
        time.sleep(self.sleep)
        input_login = WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.XPATH, UberService.get_value('UBER_LOGIN_1'))))
        clickandclear(input_login)
        input_login.send_keys(ParkSettings.get_value("UBER_NAME", partner=self.partner))
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, UberService.get_value('UBER_LOGIN_2')))).click()
        try:
            self.password_form()
        except TimeoutException:
            try:
                el = WebDriverWait(self.driver, self.sleep).until(
                    ec.presence_of_element_located((By.XPATH, UberService.get_value('UBER_LOGIN_4'))))
                el.click()
                self.password_form()
            except TimeoutException:
                WebDriverWait(self.driver, self.sleep).until(
                    ec.presence_of_element_located((By.XPATH, UberService.get_value('UBER_LOGIN_5')))).click()
                WebDriverWait(self.driver, self.sleep).until(
                    ec.presence_of_element_located((By.XPATH, UberService.get_value('UBER_LOGIN_6')))).click()
                self.password_form()
        time.sleep(self.sleep)
        self.save_uber()
        self.quit()

    def save_uber(self):
        url = UberService.get_value('BASE_URL')
        self.driver.get(url)
        time.sleep(self.sleep)
        new_url = self.driver.current_url
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuid_list = re.findall(uuid_pattern, new_url)
        sid = None
        csid = None
        if uuid_list:
            uuid = uuid_list[0]
            for cookie in self.driver.get_cookies():
                if cookie['name'] == 'sid':
                    sid = cookie['value']
                elif cookie['name'] == 'csid':
                    csid = cookie['value']
            if sid and csid:
                UberSession.objects.create(session=sid,
                                           cook_session=csid,
                                           uber_uuid=uuid,
                                           partner=Partner.get_partner(self.partner)
                                           )
            else:
                self.logger.error(f"Cookie error{sid}, {csid}")
        else:
            self.logger.error(f"{new_url} without uuid")

    def password_form(self):
        input_password = WebDriverWait(self.driver, self.sleep).until(
            ec.presence_of_element_located((By.ID, UberService.get_value('UBER_LOGIN_3'))))
        clickandclear(input_password)
        input_password.send_keys(ParkSettings.get_value("UBER_PASSWORD", partner=self.partner))
        WebDriverWait(self.driver, self.sleep).until(
            ec.element_to_be_clickable((By.XPATH, UberService.get_value('UBER_LOGIN_2')))).click()

    def wait_otp_code(self, key):
        p = redis_instance.pubsub()
        p.subscribe(key)
        p.ping()
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
            otp = self.wait_otp_code('code')
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_1')).send_keys(otp[0])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_2')).send_keys(otp[1])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_3')).send_keys(otp[2])
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_4')).send_keys(otp[3])
            # self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V2_5')).click()
            break

    def wait_code_form(self, pk):
        try:
            WebDriverWait(self.driver, self.sleep).until(ec.presence_of_element_located((By.ID, pk)))
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
            otp = self.wait_otp_code('code')
            self.driver.find_element(By.ID, UberService.get_value('UBER_OTP_CODE_V1_1')).send_keys(otp)
            self.driver.find_element(By.CLASS_NAME, UberService.get_value('UBER_OTP_CODE_V1_2')).click()
            break

    def force_opt_form(self):
        try:
            WebDriverWait(self.driver, self.sleep).until(
                ec.presence_of_element_located((By.ID, UberService.get_value('UBER_FORCE_OPT_FORM'))))
            self.driver.find_element(By.ID, UberService.get_value('UBER_FORCE_OPT_FORM')).click()
        except TimeoutException:
            pass


def clickandclear(element):
    element.click()
    element.clear()
