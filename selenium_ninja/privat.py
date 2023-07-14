import os
import re
import time

from selenium.common import TimeoutException
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_ninja.driver import SeleniumTools


class Privat24(SeleniumTools):
    def __init__(self, card=None, sum=None, driver=True, sleep=3, headless=False, base_url='https://next.privat24.ua/'):
        self.card = card
        self.sum = sum
        if driver:
            self.driver = self.build_driver(headless)
        self.base_url = base_url
        super().__init__('privat', sleep=sleep)

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