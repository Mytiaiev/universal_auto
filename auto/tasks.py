import os
import time
import pendulum
from contextlib import contextmanager
import datetime

from django.utils import timezone

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from app.models import RawGPS, Vehicle, VehicleGPS, Fleet,  Driver,  JobApplication, ParkStatus, ParkSettings, Bolt,\
    NewUklon, Uber, UaGps, get_report, download_and_save_daily_report

from scripts.conversion import convertion
from auto.celery import app
from auto.fleet_synchronizer import BoltSynchronizer, UklonSynchronizer, UberSynchronizer, UaGpsSynchronizer

BOLT_CHROME_DRIVER = None
UKLON_CHROME_DRIVER = None
UBER_CHROME_DRIVER = None
UAGPS_CHROME_DRIVER = None

UPDATE_DRIVER_DATA_FREQUENCY = 60 * 60 * 1
UPDATE_DRIVER_STATUS_FREQUENCY = 60 * 1.5
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
        date_time = date_time.replace(tzinfo=zoneinfo.ZoneInfo(settings.TIME_ZONE))
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


@app.task
def download_weekly_report(fleet_name, missing_weeks):
    weeks = missing_weeks.split(';')
    fleets = Fleet.objects.filter(name=fleet_name, deleted_at=None)
    for fleet in fleets:
        for week_number in weeks:
            fleet.download_weekly_report(week_number=week_number, driver=True, sleep=5, headless=True)


@app.task(bind=True, queue='non_priority')
def download_daily_report(self):
    # Yesterday
    try:
        day = pendulum.now().start_of('day').subtract(days=1)  # yesterday
        download_and_save_daily_report(driver=True, sleep=5, headless=True, day=day)
    except Exception as e:
        logger.info(e)


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

                bolt_status = BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('get_driver_status')
                logger.info(f'Bolt {bolt_status}')

                uklon_status = UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('get_driver_status')
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
                    last_hour = timezone.localtime() - timezone.timedelta(hours=1)
                    park_status = ParkStatus.objects.filter(driver=driver, created_at__gte=last_hour).first()
                    current_status = Driver.OFFLINE
                    if park_status:
                        current_status = park_status.status
                    if (driver.name, driver.second_name) in status_online:
                        current_status = Driver.ACTIVE
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
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def update_driver_data(self):
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:
                BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('synchronize')
                UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('synchronize')
                UberSynchronizer(UBER_CHROME_DRIVER.driver).try_to_execute('synchronize')
            else:
                logger.info('passed')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def download_weekly_report_force(self):
    try:
        BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
        UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
        UberSynchronizer(UBER_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def send_on_job_application_on_driver(self, job_id):
    try:
        candidate = JobApplication.objects.get(id=job_id)
        BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('add_driver', candidate)
        UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('add_driver', candidate)
        print('The job application has been sent')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def get_rent_information(self):
    try:
        UaGpsSynchronizer(UAGPS_CHROME_DRIVER.driver).try_to_execute('get_rent_distance')
        print('write rent report in uagps')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def get_report_for_tg(self):
    try:
        report = get_report(week=True, week_number=None, driver=True, sleep=5, headless=True)
        return report
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def withdraw_uklon(self):
    try:
        UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('withdraw_money')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def send_daily_into_group(self):
    try:
        total_values = {}
        today = pendulum.now().weekday()
        if today > 0:
            for i in range(today):
                day = pendulum.now().start_of('day').subtract(days=i + 1)
                report = get_report(week=False, day=day, week_number=None, driver=True, sleep=5, headless=True)[2]
                for key, value in report.items():
                    total_values[key] = total_values.get(key, 0) + value
        else:
            total_values = get_report(week=True, week_number=None, driver=True, sleep=5, headless=True)[2]
        sort_report = dict(sorted(total_values.items(), key=lambda item: item[1], reverse=True))
        message = [f'{k}: %.2f' % v for k, v in sort_report.items()]
        return message
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='non_priority')
def check_time_order(self):
    print("check orders on time")


@app.task(bind=True, queue='non_priority')
def get_distance_trip(self, order, query, start_trip_with_client, end, licence_plate):
    start_trip_with_client, end = start_trip_with_client.replace('T', ' '), end.replace('T', ' ')
    start = datetime.datetime.strptime(start_trip_with_client, '%Y-%m-%d %H:%M:%S.%f%z')
    format_end = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S.%f%z')
    delta = format_end - start
    try:
        result = UaGpsSynchronizer(UAGPS_CHROME_DRIVER.driver).try_to_execute('generate_report', start,
                                                                              format_end, licence_plate)
        minutes = delta.total_seconds() // 60
        return order, query, minutes, result[0]
    except Exception as e:
        logger.info(e)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    global BOLT_CHROME_DRIVER
    global UKLON_CHROME_DRIVER
    global UBER_CHROME_DRIVER
    global UAGPS_CHROME_DRIVER
    init_chrome_driver()
    sender.add_periodic_task(crontab(minute=f"*/{ParkSettings.get_value('CHECK_ORDER_TIME_MIN', 5)}"),
                             check_time_order.s(), queue='non_priority')
    sender.add_periodic_task(UPDATE_DRIVER_STATUS_FREQUENCY, update_driver_status.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=15, hour='*/2'), update_driver_data.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=5), download_weekly_report_force.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=6, day_of_week=1), get_report_for_tg.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=5), download_daily_report.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=5, hour=0, day_of_week=1), withdraw_uklon.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=0, hour=6), send_daily_into_group.s(), queue='non_priority')
    sender.add_periodic_task(crontab(minute=10, hour='*/1'), get_rent_information.s(), queue='non_priority')


def init_chrome_driver():
    global BOLT_CHROME_DRIVER
    global UKLON_CHROME_DRIVER
    global UBER_CHROME_DRIVER
    global UAGPS_CHROME_DRIVER
    BOLT_CHROME_DRIVER = Bolt(week_number=None, driver=True, sleep=5, headless=True, profile='Bolt_CeleryTasks')
    UKLON_CHROME_DRIVER = NewUklon(week_number=None, driver=True, sleep=5, headless=True, profile='Uklon_CeleryTasks')
    UBER_CHROME_DRIVER = Uber(week_number=None, driver=True, sleep=5, headless=True, profile='Uber_CeleryTasks')
    UAGPS_CHROME_DRIVER = UaGps(headless=True, profile='Uagps_CeleryTasks')
