import os
import time as tm
from contextlib import contextmanager
from datetime import datetime, timedelta
from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils import timezone
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from django.core.cache import cache
from selenium import webdriver

from app.models import RawGPS, Vehicle, VehicleGPS, Order, Driver, JobApplication, ParkStatus, ParkSettings, \
    UseOfCars, CarEfficiency, Payments, SummaryReport, DriverManager, Fleets_drivers_vehicles_rate, NinjaFleet, Park
from django.db.models import Sum, IntegerField, FloatField, Avg
from django.db.models.functions import Cast, Coalesce
from auto_bot.handlers.driver_manager.utils import calculate_reports, get_daily_report, get_efficiency
from auto_bot.main import bot
from scripts.conversion import convertion
from auto.celery import app
from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.uagps_sync import UaGpsSynchronizer
from selenium_ninja.uber_sync import UberSynchronizer
from selenium_ninja.uklon_sync import UklonSynchronizer, UklonRequest
from scripts.redis_conn import redis_instance

CHROME_DRIVER = None

MEMCACHE_LOCK_EXPIRE = 60 * 10
MEMCACHE_LOCK_AFTER_FINISHING = 10

logger = get_task_logger(__name__)
selenium_session = {}


@app.task()
def raw_gps_handler(pk):
    try:
        raw = RawGPS.objects.get(id=pk)
    except ObjectDoesNotExist:
        return f'{ObjectDoesNotExist}: id={pk}'
    data = raw.data.split(';')
    try:
        lat, lon = convertion(data[2]), convertion(data[4])
    except ValueError:
        lat, lon = 0, 0
    try:
        vehicle = Vehicle.objects.get(gps_imei=raw.imei)
    except ObjectDoesNotExist:
        return f'{ObjectDoesNotExist}: gps_imei={raw.imei}'
    try:
        date_time = timezone.datetime.strptime(data[0] + data[1], '%d%m%y%H%M%S')
        date_time = timezone.make_aware(date_time)
    except ValueError as err:
        return f'{ValueError} {err}'
    try:
        kwa = {
            'date_time': date_time,
            'vehicle': vehicle,
            'lat': float(lat),
            'lat_zone': data[3],
            'lon': float(lon),
            'lon_zone': data[5],
            'speed': float(data[6]),
            'course': float(data[7]),
            'height': float(data[8]),
            'raw_data': raw,
        }
        VehicleGPS.objects.create(**kwa)
    except ValueError as err:
        return f'{ValueError} {err}'


@app.task(bind=True)
def download_daily_report(self):
    for park in Park.objects.all():
        download_report_d.apply_async(args=[park.pk])


@app.task(bind=True)
def download_report_d(park_pk, day=None):
    if not day:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")
    # UberSynchronizer(CHROME_DRIVER.driver, 'Uber').try_to_execute('download_weekly_report', day)
    # driver, session = get_remote_selenium(park_pk)
    # UberSynchronizer(park_pk, 'Uber', driver).synchronize()
    # remove_session_driver_in_redis(driver, session, park_pk)
    UklonRequest(park_pk, 'Uklon').save_report(day)
    BoltRequest(park_pk, 'Bolt').save_report(day)
    save_report_to_ninja_payment(day)
    fleet_reports = Payments.objects.filter(report_from=day)
    for driver in Driver.objects.all():
        payments = [r for r in fleet_reports if r.driver_id == driver.get_driver_external_id(r.vendor_name)]
        if payments:
            if not SummaryReport.objects.filter(report_from=day, full_name=driver, partner=driver.partner):
                report = SummaryReport(report_from=day,
                                       full_name=driver,
                                       partner=driver.partner)
                fields = ("total_rides", "total_distance", "total_amount_cash",
                          "total_amount_on_card", "total_amount", "tips",
                          "bonuses", "fee", "total_amount_without_fee", "fares",
                          "cancels", "compensations", "refunds"
                          )

                for field in fields:
                    setattr(report, field, sum(getattr(payment, field, 0) or 0 for payment in payments))
                report.save()


@app.task(bind=True)
def get_car_efficiency(self, day=None):
    if not day:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")
    for vehicle in Vehicle.objects.filter(driver__isnull=False):
        efficiency = CarEfficiency.objects.filter(report_from=day,
                                                  licence_plate=vehicle.licence_plate)
        if not efficiency:
            total_kasa = 0
            drivers = None
            total_km, vehicle = UaGpsSynchronizer().total_per_day(vehicle.licence_plate, day)
            if total_km:
                drivers = Driver.objects.filter(vehicle=vehicle).first()
                # for driver in drivers:
                report = SummaryReport.objects.filter(report_from=day,
                                                      full_name=drivers).first()
                if report:
                    total_kasa += report.total_amount_without_fee
                result = Decimal(total_kasa)/Decimal(total_km)
            else:
                result = 0
            CarEfficiency.objects.create(report_from=day,
                                         licence_plate=vehicle.licence_plate,
                                         driver=drivers,
                                         total_kasa=total_kasa,
                                         mileage=total_km or 0,
                                         efficiency=result)

@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = tm.monotonic() + MEMCACHE_LOCK_EXPIRE - 3
    status = cache.add(lock_id, oid, MEMCACHE_LOCK_EXPIRE)
    try:
        yield status
    finally:
        if tm.monotonic() < timeout_at and status:
            cache.set(lock_id, oid, MEMCACHE_LOCK_AFTER_FINISHING)


@app.task(bind=True)
def update_driver_status(self):
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:
                for park in Park.objects.all():
                    bolt_status = BoltRequest(park.pk, 'Bolt').get_drivers_status()
                    logger.info(f'Bolt {bolt_status}')

                    uklon_status = UklonRequest(park.pk, 'Uklon').get_driver_status()
                    logger.info(f'Uklon {uklon_status}')

                status_online = set()
                status_with_client = set()
                if bolt_status is not None:
                    status_online = status_online.union(set(bolt_status['wait']))
                    status_with_client = status_with_client.union(set(bolt_status['with_client']))
                if uklon_status is not None:
                    status_online = status_online.union(set(uklon_status['wait']))
                    status_with_client = status_with_client.union(set(uklon_status['width_client']))
                drivers = Driver.objects.filter(deleted_at=None)
                for driver in drivers:
                    last_status = timezone.localtime() - timedelta(minutes=2)
                    park_status = ParkStatus.objects.filter(driver=driver, created_at__gte=last_status).first()
                    work_ninja = UseOfCars.objects.filter(user_vehicle=driver,
                                                          created_at__date=timezone.now().date(), end_at=None)
                    if work_ninja or (driver.name, driver.second_name) in status_online:
                        current_status = Driver.ACTIVE
                    else:
                        current_status = Driver.OFFLINE
                    if park_status and park_status.status != Driver.ACTIVE:
                        current_status = park_status.status
                    if (driver.name, driver.second_name) in status_with_client:
                        current_status = Driver.WITH_CLIENT
                    # if (driver.name, driver.second_name) in status['wait']:
                    #     current_status = Driver.ACTIVE
                    driver.driver_status = current_status
                    driver.save()
                    if current_status != Driver.OFFLINE:
                        logger.info(f'{driver}: {current_status}')

            else:
                logger.info('passed')

    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def update_driver_data(self, park_pk, manager_id=None):
    day = timezone.localtime() - timedelta(days=1)
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:
                BoltRequest(park_pk, 'Bolt').synchronize()
                UklonRequest(park_pk, 'Uklon').synchronize()
                UaGpsSynchronizer().get_vehicle_id()
                uber_driver = UberSynchronizer(park_pk, 'Uber', selenium_session[park_pk])
                if manager_id is None:
                    uber_driver.synchronize()
                    # uber_driver.try_to_execute('download_trips', 'Trips', day)
                    # uber_driver.try_to_execute('download_weekly_report', day)
            else:
                logger.info('passed')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def send_on_job_application_on_driver(self, job_id):
    try:
        candidate = JobApplication.objects.get(id=job_id)
        UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('add_driver', candidate)
        BoltRequest().add_driver(candidate)
        logger.info('The job application has been sent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def detaching_the_driver_from_the_car(self, licence_plate):
    try:
        UklonSynchronizer(CHROME_DRIVER.driver).try_to_execute('detaching_the_driver_from_the_car', licence_plate)
        logger.info(f'Car {licence_plate} was detached')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def get_rent_information(self):
    try:
        session = UaGpsSynchronizer()
        session.get_rent_distance()
        logger.info('write rent report in uagps')
        session.no_uber_rent_distance()
        logger.info('uber removed in rent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def fleets_cash_trips(self, pk, enable):
    try:
        UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('disable_cash', pk, enable)
        logger.info('disable_uklon_cash')
        BoltRequest().cash_restriction(pk, enable)
        logger.info('disable_bolt_cash')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def withdraw_uklon(self):
    try:
        UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('withdraw_money')
    except Exception as e:
        logger.error(e)


@app.task(bind=True)
def manager_paid_weekly(self):
    return logger.info('send message to manager')


@app.task(bind=True)
def send_weekly_report(self):
    end = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday() + 1)
    start = end - timedelta(days=6)
    message = ''
    balance = 0
    for manager in DriverManager.objects.all():
        drivers = Driver.objects.filter(manager=manager)
        if drivers:
            for driver in drivers:
                driver_message = ''
                result = calculate_reports(start, end, driver)
                if result:
                    balance += result[0]
                    driver_message += f"{driver} каса: {result[1]}\n"
                    driver_message += f'Зарплата за тиждень: {result[1]}*{driver.rate}- Готівка {result[2]} = {result[3]}\n'
                    if driver.chat_id:
                        bot.send_message(chat_id=driver.chat_id, text=driver_message)
                    message += driver_message
                    message += "*" * 39 + '\n'
            manager_message = f'Ваш тижневий баланс:%.2f\n' % balance
            manager_message += message
            bot.send_message(chat_id=manager.chat_id, text=manager_message)


@app.task(bind=True)
def send_daily_report(self):
    message = ''
    for manager in DriverManager.objects.filter(chat_id__isnull=False):
        result = get_daily_report(manager_id=manager.chat_id)
        if result:
            for num, key in enumerate(result[0], 1):
                if result[0][key]:
                    num = "\U0001f3c6" if num == 1 else num
                    message += "{}.{}\n Всього: {:.2f} Учора: (+{:.2f})\n".format(
                        num, key, result[0][key], result[1].get(key, 0))
            bot.send_message(chat_id=ParkSettings.get_value('DRIVERS_CHAT'), text=message)


@app.task(bind=True)
def send_efficiency_report(self):
    message = ''
    for manager in DriverManager.objects.filter(chat_id__isnull=False):
        result = get_efficiency(manager_id=manager.chat_id)
        if result:
            for k, v in result.items():
                message += f"{k}\n" + "".join(v)
            bot.send_message(chat_id=ParkSettings.get_value('DRIVERS_CHAT'), text=message)


@app.task(bind=True)
def check_time_order(self, order_id):
    return order_id


@app.task(bind=True)
def send_time_order(self):
    return logger.info('sending_time_orders')


@app.task(bind=True)
def check_order(self, order_id):
    return order_id


@app.task(bind=True)
def get_distance_trip(self, order, query, start_trip_with_client, end, gps_id):
    start = datetime.fromtimestamp(start_trip_with_client)
    format_end = datetime.fromtimestamp(end)
    delta = format_end - start
    try:
        result = UaGpsSynchronizer().generate_report(start_trip_with_client, end, gps_id)
        minutes = delta.total_seconds() // 60
        return order, query, minutes, result[0]
    except Exception as e:
        logger.info(e)


@app.task(bind=True)
def save_report_to_ninja_payment(self, day, partner='Ninja'):
    reports = Payments.objects.filter(report_from=day, vendor_name=partner)
    if reports:
        return reports
    # Pulling notes for the rest of the week and grouping behind the chat_id field
    for driver in Driver.objects.exclude(chat_id=''):
        records = Order.objects.filter(driver__chat_id=driver.chat_id,
                                       status_order=Order.COMPLETED,
                                       created_at__date=day)
        total_rides = records.count()
        result = records.aggregate(
            total=Sum(Coalesce(Cast('distance_gps', FloatField()),
                               Cast('distance_google', FloatField()),
                               output_field=FloatField())))
        total_distance = result['total'] if result['total'] is not None else 0.0
        total_amount_cash = records.filter(payment_method='Готівка').aggregate(
            total=Coalesce(Sum(Cast('sum', output_field=IntegerField())), 0))['total']
        total_amount_card = records.filter(payment_method='Картка').aggregate(
            total=Coalesce(Sum(Cast('sum', output_field=IntegerField())), 0))['total']
        total_amount = total_amount_cash + total_amount_card
        report = Payments(
            report_from=day,
            full_name=str(driver),
            driver_id=driver.chat_id,
            total_rides=total_rides,
            total_distance=total_distance,
            total_amount_cash=total_amount_cash,
            total_amount_on_card=total_amount_card,
            total_amount_without_fee=total_amount)
        try:
            report.save()
        except IntegrityError:
            pass


@app.task(bind=True)
def upload_db(self, day):
    UberSynchronizer(CHROME_DRIVER.driver, 'Uber').try_to_execute('download_trips', 'Trips', day)
    UberSynchronizer(CHROME_DRIVER.driver, 'Uber').try_to_execute('download_weekly_report', day)
    UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('download_weekly_report', day)
    BoltRequest().save_report(day)
    save_report_to_ninja_payment(day)
    fleet_reports = Payments.objects.filter(report_from=day)
    for driver in Driver.objects.all():
        payments = [r for r in fleet_reports if r.driver_id == driver.get_driver_external_id(r.vendor_name)]
        if payments:
            if not SummaryReport.objects.filter(report_from=day, full_name=driver, partner=driver.partner):
                report = SummaryReport(report_from=day,
                                       full_name=driver,
                                       partner=driver.partner)
                fields = ("total_rides", "total_distance", "total_amount_cash",
                          "total_amount_on_card", "total_amount", "tips",
                          "bonuses", "fee", "total_amount_without_fee", "fares",
                          "cancels", "compensations", "refunds"
                          )

                for field in fields:
                    setattr(report, field, sum(getattr(payment, field, 0) or 0 for payment in payments))
                report.save()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    init_chrome_driver()
    sender.add_periodic_task(crontab(minute=f"*/{ParkSettings.get_value('CHECK_ORDER_TIME_MIN', 5)}"),
                             send_time_order.s())
    sender.add_periodic_task(crontab(minute='*/1'), update_driver_status.s(),)
    for park in Park.objects.all():
        sender.add_periodic_task(crontab(minute='*/3'), update_driver_data.s(park.pk))
    # sender.add_periodic_task(crontab(minute=0, hour=5), download_daily_report.s())
    # sender.add_periodic_task(crontab(minute=5, hour=0, day_of_week=1), withdraw_uklon.s())
    # sender.add_periodic_task(crontab(minute=30, hour=5), download_uber_trips.s())
    # sender.add_periodic_task(crontab(minute=10, hour=5), get_rent_information.s())
    # sender.add_periodic_task(crontab(minute=0, hour=6), send_efficiency_report.s())
    # sender.add_periodic_task(crontab(minute=30, hour=3), get_car_efficiency.s())
    # sender.add_periodic_task(crontab(minute=1, hour=6), send_daily_report.s())
    # sender.add_periodic_task(crontab(minute=0, hour=6, day_of_week=1), send_weekly_report.s())
    # sender.add_periodic_task(crontab(minute=55, hour=8, day_of_week=1), manager_paid_weekly.s())


def init_chrome_driver():
    global selenium_session
    for park in Park.objects.all():
        driver = webdriver.Remote(command_executor=os.environ['SELENIUM_HUB_HOST'],
                                  desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        selenium_session[park.pk] = driver
