from datetime import datetime, time
import logging
import base64
import shutil
import os
import re

from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
from selenium.common import TimeoutException


class SeleniumTools:
    def __init__(self, partner, profile, remote=True, driver=True, sleep=5, headless=True):
        self.partner = partner
        self.profile = profile
        self.remote = remote
        self.sleep = sleep
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        if driver:
            if self.remote:
                self.driver = self.build_remote_driver()
            else:
                self.driver = self.build_driver(headless)

    def report_file_name(self, pattern):
        filenames = os.listdir(os.curdir)
        for file in filenames:
            if re.search(pattern, file):
                return file

    def park_name(self):
        park = Park.objects.get(pk=self.partner)
        return park.name

    def payments_order_file_name(self, fleet, partner, day):
        return self.report_file_name(self.file_pattern(fleet, partner, day))

    @staticmethod
    def file_pattern(fleet, partner, day=None):
        return f'{fleet} {day.strftime("%Y%m%d")}-{partner}.csv'

    def remove_session(self):
        os.remove(self.park_name())

    def build_driver(self, headless=True):
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
            options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(options=options, port=9514)
        return driver

    def build_remote_driver(self):
        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("--enable-file-cookies")
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument(f'--user-data-dir=home/seluser/{self.profile}')
        options.add_argument(f'--profile-directory={self.profile}')

        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptInsecureCerts'] = True

        driver = webdriver.Remote(
            os.environ['SELENIUM_HUB_HOST'],
            desired_capabilities=capabilities,
            options=options
        )
        return driver

    @staticmethod
    def get_downloaded_files(driver):
        if not driver.current_url.startswith("chrome://downloads"):
            driver.get("chrome://downloads/")

        return driver.execute_script("""
        const downloadsManager = document.querySelector('downloads-manager');
        const shadowRoot = downloadsManager.shadowRoot;
        const items = shadowRoot.querySelector('#downloadsList').items;
        const completedItems = Array.from(items).filter(e => e.state === 'COMPLETE');
        return completedItems.map(e => e.filePath || e.file_path || e.fileUrl || e.file_url);
    """)

    def clear_downloads(self):
        if not self.driver.current_url.startswith("chrome://downloads"):
            self.driver.get("chrome://downloads/")

        download_manager = self.driver.find_element(By.TAG_NAME, 'downloads-manager')
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', download_manager)
        clear_button = WebDriverWait(shadow_root, self.sleep).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#toolbar #clear-all-button')))
        clear_button.click()

    def get_file_content(self, path):
        try:
            elem = self.driver.execute_script(
                "var input = window.document.createElement('INPUT'); "
                "input.setAttribute('type', 'file'); "
                "input.hidden = true; "
                "input.onchange = function (e) { e.stopPropagation() }; "
                "return window.document.documentElement.appendChild(input); ")
            elem._execute('sendKeysToElement', {'value': [path], 'text': path})
            result = self.driver.execute_async_script(
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
        fname = os.path.basename(files[0]) if save_as is None else save_as
        with open(os.path.join(os.getcwd(), fname), 'wb') as f:
            f.write(content)

    def get_last_downloaded_file(self, save_as=None):
        folder = os.path.join(os.getcwd(), "LastDownloads")
        files = [os.path.join(folder, f) for f in os.listdir(folder)]  # add path to each file
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        if files:
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


def clickandclear(element):
    element.click()
    element.clear()

