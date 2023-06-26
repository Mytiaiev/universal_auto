import time
import datetime
from _decimal import Decimal
from django.utils import timezone
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.models import UaGpsService, ParkSettings, Driver, Vehicle, StatusChange, RentInformation, UberTrips
from selenium_ninja.synchronizer import Synchronizer
from selenium_ninja.driver import SeleniumTools, clickandclear


class UaGpsSynchronizer(Synchronizer, SeleniumTools):
    def login(self):
        self.driver.get(UaGpsService.get_value('BASE_URL'))
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
        xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
        WebDriverWait(self.driver, self.sleep).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        unit = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_2'))))
        unit.click()
        try:
            WebDriverWait(self.driver, self.sleep).until(
                EC.element_to_be_clickable((
                    By.XPATH, f'{UaGpsService.get_value("UAGPSS_GENERATE_REPORT_3")} "{report_object}")]'))).click()
        except:
            return 0, datetime.timedelta()
        from_field = self.driver.find_element(By.ID, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_4'))
        clickandclear(from_field)
        from_field.send_keys(start_time.strftime("%d %B %Y %H:%M"))
        from_field.send_keys(Keys.ENTER)
        to_field = WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.ID, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_5'))))
        clickandclear(to_field)
        to_field.send_keys(end_time.strftime("%d %B %Y %H:%M"))
        to_field.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, self.sleep).until(
            EC.element_to_be_clickable((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_6')))).click()
        if self.sleep:
            time.sleep(self.sleep)
        road_distance = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_7')))).text
        rent_distance = float(road_distance.split(' ')[0])
        roadtimestr = WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located((By.XPATH, UaGpsService.get_value('UAGPSS_GENERATE_REPORT_8')))).text
        roadtime = [int(i) for i in roadtimestr.split(':')]
        rent_time = datetime.timedelta(hours=roadtime[0], minutes=roadtime[1], seconds=roadtime[2])
        time.sleep(1)
        return rent_distance, rent_time

    def get_rent_distance(self):
        xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
        self.get_target_element_of_page(UaGpsService.get_value('BASE_URL'), xpath,
                                        UaGpsService.get_value('UAGPS_LOGIN_1'))
        yesterday = timezone.localtime() - datetime.timedelta(days=1)
        start = timezone.datetime.combine(yesterday, datetime.datetime.min.time()).astimezone()
        end = timezone.datetime.combine(yesterday, datetime.datetime.max.time()).astimezone()
        for _driver in Driver.objects.all():
            if not RentInformation.objects.filter(driver=_driver,
                                                  created_at__date=timezone.localtime().date()):
                rent_distance = 0
                rent_time = datetime.timedelta()
                # car that have worked at that day
                split_driver = _driver.split()
                vehicle = Driver.objects.filter(name=split_driver[0], second_name=split_driver[1]).first()
                if vehicle:
                    rent_statuses = StatusChange.objects.filter(driver=_driver.id,
                                                                vehicle=vehicle,
                                                                start_time__gte=timezone.localtime(start),
                                                                end_time__lte=timezone.localtime(end))
                    if rent_statuses:
                        first_status = rent_statuses.first()
                        first_report = self.generate_report(timezone.localtime(start),
                                                            timezone.localtime(first_status.start_time),
                                                            vehicle.licence_plate)
                        rent_distance += first_report[0]
                        rent_time += first_report[1]

                        last_status = rent_statuses.last()
                        last_report = self.generate_report(timezone.localtime(last_status.end_time),
                                                           timezone.localtime(end),
                                                           vehicle.licence_plate)
                        rent_distance += last_report[0]
                        rent_time += last_report[1]
                        statuses = rent_statuses.filter(name__in=[Driver.ACTIVE, Driver.OFFLINE, Driver.RENT])
                        for status in statuses:
                            status_report = self.generate_report(timezone.localtime(status.start_time),
                                                                 timezone.localtime(status.end_time),
                                                                 vehicle.licence_plate)
                            rent_distance += status_report[0]
                            rent_time += status_report[1]
                    else:
                        report = self.generate_report(timezone.localtime(start),
                                                      timezone.localtime(end),
                                                      vehicle.licence_plate)
                        rent_distance += report[0]
                        rent_time += report[1]

                RentInformation.objects.create(driver_name=_driver,
                                               driver=_driver,
                                               rent_time=rent_time,
                                               rent_distance=rent_distance)

    def no_uber_rent_distance(self):
        drivers = Driver.objects.all()
        for driver in drivers:
            rent = RentInformation.objects.filter(driver_name=driver,
                                                  created_at__date=timezone.localtime().date()).first()
            driver_id = driver.get_driver_external_id('Uber')
            distance_in_trips = 0
            if driver_id and rent:
                xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
                self.get_target_element_of_page(UaGpsService.get_value('BASE_URL'), xpath,
                                                UaGpsService.get_value('UAGPS_LOGIN_1'))
                trips = UberTrips.objects.filter(driver_external_id=driver_id,
                                                 created_at__date=timezone.localtime().date())
                for trip in trips:
                    trip_distance = self.generate_report(timezone.localtime(trip.start_trip),
                                                         timezone.localtime(trip.end_trip),
                                                         trip.license_plate)
                    distance_in_trips += trip_distance[0]
                rent.rent_distance -= Decimal(distance_in_trips)
                rent.save()

    def no_route_trip(self, start, end, vehicle):
        xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
        self.get_target_element_of_page(UaGpsService.get_value('BASE_URL'), xpath,
                                        UaGpsService.get_value('UAGPS_LOGIN_1'))
        result = self.generate_report(start, end, vehicle)
        return result

    def total_per_day(self, driver, day):
        vehicle = Vehicle.objects.filter(driver=driver).first()
        if vehicle:
            xpath = UaGpsService.get_value('UAGPSS_GENERATE_REPORT_1')
            self.get_target_element_of_page(UaGpsService.get_value('BASE_URL'), xpath,
                                            UaGpsService.get_value('UAGPS_LOGIN_1'))
            distance = self.generate_report(self.start_report_interval(day),
                                            self.end_report_interval(day),
                                            vehicle.licence_plate)[0]
            return distance
