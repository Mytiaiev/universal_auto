import os
import time
import pendulum
from contextlib import contextmanager
import datetime

import pytz
from _decimal import Decimal
from django.db import IntegrityError
from django.utils import timezone
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from app.models import RawGPS, Vehicle, VehicleGPS, Fleet, Order, Driver, JobApplication, ParkStatus, ParkSettings, \
    NinjaPaymentsOrder, UseOfCars, Fleets_drivers_vehicles_rate, NinjaFleet, CarEfficiency
from django.db.models import Sum, IntegerField, FloatField, Avg
from django.db.models.functions import Cast, Coalesce

from scripts.conversion import convertion
from auto.celery import app
from selenium_ninja.bolt_sync import BoltSynchronizer
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.uagps_sync import UaGpsSynchronizer
from selenium_ninja.uber_sync import UberSynchronizer
from selenium_ninja.uklon_sync import UklonSynchronizer

CHROME_DRIVER = None

MEMCASH_LOCK_EXPIRE = 60 * 10
MEMCASH_LOCK_AFTER_FINISHING = 10

logger = get_task_logger(__name__)


@app.task(queue='non_priority')
def raw_gps_handler(id):
    try:
        raw = RawGPS.objects.get(id=id)
    except RawGPS.DoesNotExist:
        return f'{RawGPS.DoesNotExist}: id={id}'
    data = raw.data.split(';')
    try:
        lat, lon = convertion(data[2]), convertion(data[4])
    except ValueError:
        lat, lon = 0, 0
    try:
        vehicle = Vehicle.objects.get(gps_imei=raw.imei)
    except Vehicle.DoesNotExist:
        return f'{Vehicle.DoesNotExist}: gps_imei={raw.imei}'
    try:
        date_time = datetime.datetime.strptime(data[0] + data[1], '%d%m%y%H%M%S')
        date_time = pytz.timezone(settings.TIME_ZONE).localize(date_time)
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
    except ValueError as err:
        return f'{ValueError} {err}'
    obj = VehicleGPS.objects.create(**kwa)
    return True


@app.task(bind=True, queue='non_priority')
def download_weekly_report(self):
    report = download_reports()
    return report


@app.task(bind=True, queue='non_priority')
def download_daily_report(self):
    # Yesterday
    try:
        day = pendulum.now().start_of('day').subtract(days=1)
        format_day = day.format("DD.MM.YYYY")
        download_reports(day=format_day, interval=1)
    except Exception as e:
        logger.error(e)


@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = time.monotonic() + MEMCASH_LOCK_EXPIRE - 3
    status = cache.add(lock_id, oid, MEMCASH_LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.set(lock_id, oid, MEMCASH_LOCK_AFTER_FINISHING)


@app.task(bind=True, queue='non_priority')
def update_driver_status(self):
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:

                bolt_status = BoltSynchronizer(CHROME_DRIVER.driver, 'Bolt').try_to_execute('get_driver_status')
                logger.info(f'Bolt {bolt_status}')

                uklon_status = UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('get_driver_status')
                logger.info(f'Uklon {uklon_status}')

                # uber_status = UberSynchronizer(UBER_CHROME_DRIVER.driver).try_to_execute('get_driver_status')
                # logger.info(f'Uber {uber_status}')

                status_online = set()
                status_width_client = set()
                if bolt_status is not None:
                    status_online = status_online.union(set(bolt_status['wait']))
                    status_width_client = status_width_client.union(set(bolt_status['width_client']))
                if uklon_status is not None:
                    status_online = status_online.union(set(uklon_status['wait']))
                    status_width_client = status_width_client.union(set(uklon_status['width_client']))
                # if uber_status is not None:
                #     status_online = status_online.union(set(uber_status['online']))
                #     status_width_client = status_width_client.union(set(uber_status['width_client']))
                drivers = Driver.objects.filter(deleted_at=None)
                for driver in drivers:
                    last_status = timezone.localtime() - timezone.timedelta(minutes=2)
                    park_status = ParkStatus.objects.filter(driver=driver, created_at__gte=last_status).first()
                    work_ninja = UseOfCars.objects.filter(user_vehicle=driver,
                                                          created_at__date=timezone.now().date(), end_at=None)
                    if work_ninja or (driver.name, driver.second_name) in status_online:
                        current_status = Driver.ACTIVE
                    else:
                        current_status = Driver.OFFLINE
                    if park_status and park_status.status != Driver.ACTIVE:
                        current_status = park_status.status
                    if (driver.name, driver.second_name) in status_width_client:
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


@app.task(bind=True, queue='non_priority')
def update_driver_data(self):
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:
                BoltSynchronizer(CHROME_DRIVER.driver, 'Bolt').try_to_execute('synchronize')
                UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('synchronize')
                UberSynchronizer(CHROME_DRIVER.driver, 'Uber').try_to_execute('synchronize')
            else:
                logger.info('passed')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def send_on_job_application_on_driver(self, job_id):
    try:
        candidate = JobApplication.objects.get(id=job_id)
        UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('add_driver', candidate)
        BoltSynchronizer(CHROME_DRIVER.driver, 'Bolt').try_to_execute('add_driver', candidate)
        logger.info('The job application has been sent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def detaching_the_driver_from_the_car(self, licence_plate):
    try:
        UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('detaching_the_driver_from_the_car', licence_plate)
        logger.info(f'Car {licence_plate} was detached')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def get_rent_information(self):
    try:
        UaGpsSynchronizer(CHROME_DRIVER.driver).try_to_execute('get_rent_distance')
        logger.info('write rent report in uagps')
        UaGpsSynchronizer(CHROME_DRIVER.driver).try_to_execute('no_uber_rent_distance')
        logger.info('uber removed in rent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def withdraw_uklon(self):
    try:
        UklonSynchronizer(CHROME_DRIVER.driver, 'Uklon').try_to_execute('withdraw_money')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def download_uber_trips(self):
    try:
        day = pendulum.now().start_of('day').subtract(days=1)
        format_day = day.format("DD.MM.YYYY")
        UberSynchronizer(CHROME_DRIVER.driver, 'Uber').try_to_execute('download_trips', 'Trips', day=format_day)
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def send_daily_into_group(self):
    try:
        total_values = {}
        day_values = {}
        report_values = {}
        effective_driver = {}
        effective_report = {}
        today = pendulum.now().weekday()
        if today > 0:
            for i in range(today):
                day = pendulum.now().start_of('day').subtract(days=i + 1)
                format_day = day.format("DD.MM.YYYY")
                report = download_reports(day=format_day, interval=i*2 + 1)[2]
                for key, value in report.items():
                    if not i:
                        day_values[key] = day_values.get(key, 0) + value
                    total_values[key] = total_values.get(key, 0) + value
        else:
            day = pendulum.now().start_of('day').subtract(days=1)
            format_day = day.format("DD.MM.YYYY")
            day_values = download_reports(day=format_day, interval=1)[2]
            total_values = download_reports()[2]
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        for key in sort_report:
            report_values[key] = "Всього: {:.2f} Учора: (+{:.2f})".format(sort_report[key], day_values.get(key, 0))
        for driver in Driver.objects.filter(vehicle__isnull=False):
            effect = calculate_efficiency(driver)
            effective_driver[driver.full_name()] = {'Середня ефективність(грн/км)': effect[0],
                                                    'Ефективність(грн/км)': effect[1],
                                                    'КМ за тиждень': effect[2],
                                                    'КМ учора': effect[3]}
        sorted_effective_driver = dict(sorted(effective_driver.items(),
                                       key=lambda x: x[1]['Середня ефективність(грн/км)'],
                                       reverse=True))
        message = [f'{k}:\n{v}' for k, v in report_values.items()]
        for k, v in sorted_effective_driver.items():
            effective_report[k] = [f"{vk}: {vv}\n" for vk, vv in v.items()]
        effect_message = [f'{k}:\n' + ''.join(v) for k, v in effective_report.items()]
        return message, effect_message
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='non_priority')
def check_time_order(self, order_id):
    return order_id


@app.task(bind=True, queue='non_priority')
def send_time_order(self):
    return logger.info('sending_time_orders')


@app.task(bind=True, queue='non_priority')
def check_order(self, order_id):
    return order_id


@app.task(bind=True, queue='non_priority')
def get_distance_trip(self, order, query, start_trip_with_client, end, licence_plate):
    start = datetime.datetime.strptime(str(start_trip_with_client), '%Y-%m-%d %H:%M:%S.%f%z')
    format_end = datetime.datetime.strptime(str(end), '%Y-%m-%d %H:%M:%S.%f%z')
    delta = format_end - start
    try:
        result = UaGpsSynchronizer(CHROME_DRIVER.driver).try_to_execute('generate_report', start,
                                                                        format_end, licence_plate)
        minutes = delta.total_seconds() // 60
        return order, query, minutes, result[0]
    except Exception as e:
        logger.info(e)


@app.task(queue='non_priority')
def save_report_to_ninja_payment(day=None):
    if day:
        day = pendulum.now().start_of('day').subtract(days=1)
        start_date = day.start_of("day")
        end_date = day.end_of("day")
    else:
        week = pendulum.now().start_of('week').subtract(days=3)
        start_date = week.start_of('week')
        end_date = week.end_of('week')

    start_date, end_date = str(start_date).replace('T', ' '), str(end_date).replace('T', ' ')
    # Pulling notes for the rest of the week and grouping behind the chat_id field
    for driver in Driver.objects.exclude(chat_id=''):
        records = Order.objects.filter(driver__chat_id=driver.chat_id,
                                       status_order=Order.COMPLETED,
                                       created_at__date__range=(start_date.split()[0], end_date.split()[0]))
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
        report = NinjaPaymentsOrder(
            report_from=start_date,
            report_to=end_date,
            full_name=str(driver),
            chat_id=driver.chat_id,
            total_rides=total_rides,
            total_distance=total_distance,
            total_amount_cash=total_amount_cash,
            total_amount_on_card=total_amount_card,
            total_amount=total_amount)
        try:
            report.save()
        except IntegrityError:
            pass

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    global CHROME_DRIVER
    init_chrome_driver()
    sender.add_periodic_task(crontab(minute=f"*/{ParkSettings.get_value('CHECK_ORDER_TIME_MIN', 5)}"),
                             send_time_order.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute='*/1'), update_driver_status.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour="*/2"), update_driver_data.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=6, day_of_week=1), download_weekly_report.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=5), download_daily_report.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=5, hour=0, day_of_week=1), withdraw_uklon.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=6), send_daily_into_group.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=4, day_of_week=1), save_report_to_ninja_payment.s(),
                             queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=3), save_report_to_ninja_payment.s(day=True), queue='non_priority')
    sender.add_periodic_task(crontab(minute=30, hour=5), download_uber_trips.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=10, hour=6), get_rent_information.s(), queue='non_priority')


def init_chrome_driver():
    global CHROME_DRIVER
    CHROME_DRIVER = SeleniumTools(session='Ninja', week_number=None, driver=True, remote=False,
                                  sleep=5, headless=True, profile='Tasks')


def download_reports(day=None, interval=None):
    our_fleet = NinjaFleet()
    all_drivers_report = []
    owner = {"Fleet Owner": 0}
    reports = {}
    totals = {}
    salary = {}
    try:
        all_drivers_report += BoltSynchronizer(
            CHROME_DRIVER.driver, 'Bolt').try_to_execute('download_weekly_report', day=day, interval=interval)
        all_drivers_report += UklonSynchronizer(
            CHROME_DRIVER.driver, 'Uklon').try_to_execute('download_weekly_report', day=day)
        all_drivers_report += UberSynchronizer(
            CHROME_DRIVER.driver, 'Uber').try_to_execute('download_weekly_report', day=day)
        all_drivers_report += our_fleet.download_report(day=day)
        for rate in Fleets_drivers_vehicles_rate.objects.all():
            r = list((r for r in all_drivers_report if r.driver_id() == rate.driver_external_id))
            if r:
                r = r[0]
                name = rate.driver.full_name()
                reports[name] = reports.get(name, '') + r.report_text(name, float(rate.driver.rate)) + '\n'
                totals[name] = totals.get(name, 0) + r.kassa()
                salary[name] = salary.get(name, 0) + r.total_drivers_amount(float(rate.driver.rate))

        totals = {k: v for k, v in totals.items() if v != 0.0}
        plan = dict(totals)
        totals = {k: f'Загальна каса {k}: %.2f\n' % v for k, v in totals.items()}
        totals = {k: v + reports[k] for k, v in totals.items()}
        for k, v in totals.items():
            for driver in Driver.objects.all():
                if driver.full_name() == k and driver.schema == 'RENT':
                    totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]} - Оренда ({'%.2f' % -driver.rental}) = {'%.2f' % (salary[k] - driver.rental)}\n" + "-" * 39
                    owner["Fleet Owner"] += driver.rental
                elif driver.full_name() == k and driver.schema == 'HALF':
                    if plan[k] < driver.plan:
                        owner["Fleet Owner"] += driver.rental
                        incomplete = (driver.plan - plan[k]) * float(1 - driver.rate)
                        totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]} - План ({'%.2f' % -incomplete}) = {'%.2f' % (salary[k] - incomplete)}\n" + "-" * 39
                    else:
                        owner["Fleet Owner"] += plan[k] * float(1 - driver.rate)
                        totals[k] = v + f"Зарплата за тиждень: {'%.2f' % salary[k]}\n" + "-" * 39
                else:
                    pass
        return owner, totals, plan
    except Exception as e:
        logger.info(e)


def get_car_efficiency(driver, interval, day=None):
    efficiency = CarEfficiency.objects.filter(start_report=day.start_of('day'),
                                              end_report=day.end_of('day'),
                                              driver=driver)
    if not efficiency:
        try:
            format_day = day.format("DD.MM.YYYY")
            total_km = UaGpsSynchronizer(CHROME_DRIVER.driver).try_to_execute('total_per_day', driver, format_day)
            total_kasa = download_reports(day=format_day, interval=interval)[2]
            if total_km and total_kasa.get(driver.full_name()):
                result = Decimal(total_kasa[driver.full_name()])/Decimal(total_km)
                CarEfficiency.objects.create(start_report=day.start_of('day'),
                                             end_report=day.end_of('day'),
                                             driver=driver,
                                             mileage=total_km,
                                             efficiency=result)
            else:
                CarEfficiency.objects.create(start_report=day.start_of('day'),
                                             end_report=day.end_of('day'),
                                             driver=driver,
                                             mileage=total_km or 0,
                                             efficiency=0)
        except Exception as e:
            logger.info(e)


def calculate_efficiency(driver):
    today = pendulum.now().weekday()
    if not today:
        today = 7
    for i in range(today):
        day = pendulum.now().start_of('day').subtract(days=i + 1)
        interval = i * 2 + 1
        get_car_efficiency(driver, interval, day)
    start_period = pendulum.now().start_of('day').subtract(days=today)
    end_period = pendulum.now().start_of('day').subtract(days=1)
    all_objects = CarEfficiency.objects.filter(start_report__range=[start_period, end_period],
                                               driver=driver)
    efficiency_objects = all_objects.exclude(efficiency=0)
    yesterday_efficiency = CarEfficiency.objects.filter(start_report=end_period,
                                                        driver=driver).first()
    efficiency = float(yesterday_efficiency.efficiency) if yesterday_efficiency else 1
    distance = float(yesterday_efficiency.mileage) if yesterday_efficiency else 1
    average_efficiency = efficiency_objects.aggregate(avg_efficiency=Avg('efficiency'))['avg_efficiency']
    total_distance = efficiency_objects.aggregate(total_distance=Sum('mileage'))['total_distance']
    formatted_efficiency = float('{:.2f}'.format(average_efficiency)) if average_efficiency is not None else 0.00
    formatted_distance = float('{:.2f}'.format(total_distance)) if total_distance is not None else 0.00
    return formatted_efficiency, efficiency, formatted_distance, distance
