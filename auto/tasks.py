import time
from contextlib import contextmanager
from datetime import datetime
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from selenium.common import InvalidSessionIdException

from app.models import *
from auto.celery import app
from auto.fleet_synchronizer import BoltSynchronizer, UklonSynchronizer, UberSynchronizer

BOLT_CHROME_DRIVER = None
UKLON_CHROME_DRIVER = None
UBER_CHROME_DRIVER = None

UPDATE_DRIVER_DATA_FREQUENCY = 60*60*1
UPDATE_DRIVER_STATUS_FREQUENCY = 60*2
MEMCASH_LOCK_EXPIRE = 60 * 10
MEMCASH_LOCK_AFTER_FINISHING = 10

logger = get_task_logger(__name__)


@app.task(priority=7)
def raw_gps_handler(id):
    try:
        raw = RawGPS.objects.get(id=id)
    except RawGPS.DoesNotExist:
        return f'{RawGPS.DoesNotExist}: id={id}'
    data = raw.data.split(';')
    try:
        vehicle = Vehicle.objects.get(gps_imei=raw.imei)
    except Vehicle.DoesNotExist:
        return f'{Vehicle.DoesNotExist}: gps_imei={raw.imei}'
    try:
        date_time = datetime.strptime(data[0] + data[1], '%d%m%y%H%M%S')
        date_time = date_time.replace(tzinfo=zoneinfo.ZoneInfo(settings.TIME_ZONE))
    except ValueError as err:
        return f'{ValueError} {err}'
    try:
        kwa = {
            'date_time': date_time,
            'vehicle': vehicle,
            'lat': float(data[2]),
            'lat_zone': data[3],
            'lon': float(data[4]),
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


@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = time.monotonic() + MEMCASH_LOCK_EXPIRE - 3
    status = cache.add(lock_id, oid, MEMCASH_LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.set(lock_id, oid, MEMCASH_LOCK_AFTER_FINISHING)


@app.task(bind=True)
def update_driver_status(self):
    try:
        with memcache_lock(self.name, self.app.oid) as acquired:
            if acquired:

                bolt_status = BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('get_driver_status')
                logger.info(f'Bolt {bolt_status}')

                uklon_status = UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('get_driver_status')
                logger.info(f'Uklon {uklon_status}')

                status_online = set()
                status_width_client = set()
                if bolt_status is not None:
                    status_online = status_online.union(set(bolt_status['online']))
                    status_width_client = status_width_client.union(set(bolt_status['width_client']))
                if uklon_status is not None:
                    status_online = status_online.union(set(uklon_status['online']))
                    status_width_client = status_width_client.union(set(uklon_status['width_client']))
                drivers = Driver.objects.filter(deleted_at=None)
                for driver in drivers:
                    current_status = Driver.OFFLINE
                    if ((driver.name, driver.second_name) in status_online
                            or driver.driver_status == Driver.ACTIVE):
                        current_status = Driver.ACTIVE
                    if ((driver.name, driver.second_name) in status_width_client
                            or driver.driver_status == Driver.WITH_CLIENT):
                        current_status = Driver.WITH_CLIENT
                    # if (driver.name, driver.second_name) in status['wait']:
                    #     current_status = Driver.ACTIVE
                    driver.driver_status = current_status
                    if current_status != Driver.OFFLINE:
                        logger.info(f'{driver}: {current_status}')
                    try:
                        driver.save(update_fields=['driver_status'])
                    except Exception:
                        pass

            else:
                logger.info('passed')

    except Exception as e:
        logger.info(e)


@app.task(bind=True)
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


@app.task(bind=True, priority=6)
def download_weekly_report_force(self):
    try:
        BoltSynchronizer(BOLT_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
        UklonSynchronizer(UKLON_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
        UberSynchronizer(UBER_CHROME_DRIVER.driver).try_to_execute('download_weekly_report')
    except Exception as e:
        logger.info(e)



@app.task(bind=True, priority=8)
def send_on_job_application_on_driver_to_Bolt(self, id):
    try:
        b = Bolt(driver=True, sleep=3, headless=True)
        b.login()
        candidate = JobApplication.objects.get(id=id)
        b.add_driver(candidate)
        print('The job application has been sent to Bolt')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, priority=9)
def send_on_job_application_on_driver_to_Uber(self, phone_number, email, name, second_name):
    try:
        ub = Uber(driver=True, sleep=5, headless=True)
        ub.login_v3()
        ub.add_driver(phone_number, email, name, second_name)
        ub.quit()
        print('The job application has been sent to Uber')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, priority=10)
def send_on_job_application_on_driver_to_NewUklon(self, id):
    try:
        uklon = NewUklon(driver=True, sleep=5, headless=True)
        candidate = JobApplication.objects.get(id=id)
        uklon.add_driver(candidate)
        uklon.quit()
        print('The job application has been sent to Uklon')
    except Exception as e:
        logger.info(e)


@app.task(bind=True, priority=11)
def get_rent_information(self):
    try:
        gps = UaGps(driver=True, sleep=5, headless=True)
        gps.login()
        gps.get_rent_distance()
        gps.quit()
        print('write rent report in uagps')
    except Exception as e:
        logger.info(e)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    global BOLT_CHROME_DRIVER
    global UKLON_CHROME_DRIVER
    global UBER_CHROME_DRIVER
    init_chrome_driver()
    sender.add_periodic_task(UPDATE_DRIVER_STATUS_FREQUENCY, update_driver_status.s())
    sender.add_periodic_task(UPDATE_DRIVER_DATA_FREQUENCY, update_driver_data.s())
    sender.add_periodic_task(UPDATE_DRIVER_DATA_FREQUENCY, get_rent_information.s())
    sender.add_periodic_task(crontab(minute=0, hour=5), download_weekly_report_force.s())
    # sender.add_periodic_task(60*60*3, download_weekly_report_force.s())


def init_chrome_driver():
    global BOLT_CHROME_DRIVER
    global UKLON_CHROME_DRIVER
    global UBER_CHROME_DRIVER
    BOLT_CHROME_DRIVER = Bolt(week_number=None, driver=True, sleep=3, headless=True, profile='Bolt_CeleryTasks')
    UKLON_CHROME_DRIVER = NewUklon(week_number=None, driver=True, sleep=3, headless=True, profile='Uklon_CeleryTasks')
    UBER_CHROME_DRIVER = Uber(week_number=None, driver=True, sleep=3, headless=True, profile='Uber_CeleryTasks')