import os
from datetime import datetime, timedelta, time
import time as tm
import requests
from _decimal import Decimal
from celery import current_app
from celery.exceptions import MaxRetriesExceededError
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils import timezone
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from telegram import ParseMode
from telegram.error import BadRequest

from app.models import RawGPS, Vehicle, Order, Driver, JobApplication, \
    ParkSettings, \
    UseOfCars, CarEfficiency, Payments, SummaryReport, Manager, Partner, \
    DriverEfficiency, FleetOrder, \
    TransactionsConversantion, VehicleSpendings, DriverReshuffle
from django.db.models import Sum, IntegerField, FloatField, Q
from django.db.models.functions import Cast, Coalesce
from auto_bot.handlers.driver_manager.utils import get_daily_report, get_efficiency, generate_message_weekly, \
    get_driver_efficiency_report
from auto_bot.handlers.order.keyboards import inline_markup_accept, inline_search_kb, inline_client_spot, \
    inline_spot_keyboard, inline_reject_order, personal_order_end_kb, personal_driver_end_kb
from auto_bot.handlers.order.static_text import decline_order, order_info, client_order_info, search_driver_1, \
    search_driver_2, no_driver_in_radius, driver_arrived, complete_order_text, driver_complete_text, \
    client_order_text, order_customer_text, search_driver, personal_time_route_end, personal_order_info, \
    pd_order_not_accepted, driver_text_personal_end, client_text_personal_end
from auto_bot.handlers.order.utils import text_to_client, check_reshuffle
from auto_bot.main import bot
from scripts.conversion import convertion, haversine, get_location_from_db, get_route_price
from auto.celery import app
from scripts.google_calendar import GoogleCalendar
from scripts.redis_conn import redis_instance
from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.uagps_sync import UaGpsSynchronizer
from selenium_ninja.uber_sync import UberRequest
from selenium_ninja.uklon_sync import UklonRequest
from scripts.nbu_conversion import convert_to_currency


logger = get_task_logger(__name__)


@app.task(queue='bot_tasks')
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
        date_time = timezone.datetime.strptime(data[0] + data[1], '%d%m%y%H%M%S')
        date_time = timezone.make_aware(date_time, timezone.get_current_timezone())
    except ValueError as err:
        return f'Error converting date and time: {err}'
    updated = Vehicle.objects.filter(gps_imei=raw.imei).update(lat=lat, lon=lon, coord_time=date_time)
    if not updated:
        return f'No vehicle found with gps_imei={raw.imei}'


@app.task(bind=True, queue='bot_tasks')
def health_check(self):
    logger.warning("Celery OK")


@app.task(bind=True, queue='beat_tasks')
def auto_send_task_bot(self):
    webhook_url = f'{os.environ["WEBHOOK_URL"]}/webhook/'
    message_data = {"update_id": 523456789,
                    "message": {"message_id": 6993, "chat": {"id": 515224934, "type": "private"},
                                "text": "/test_celery",
                                "from": {"id": 515224934, "first_name": "Родіон", "is_bot": False},
                                "date": int(tm.time()),
                                "entities": [{"offset": 0, "length": 12, "type": "bot_command"}]}}
    requests.post(webhook_url, json=message_data)


@app.task(bind=True, queue='beat_tasks')
def get_uber_session(self, partner_pk):
    chrome = SeleniumTools(partner_pk)
    chrome.uber_login(session=True)
    chrome.quit()


@app.task(bind=True, queue='beat_tasks')
def get_orders_from_fleets(self, partner_pk, day=None):

    if day is None:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")
    drivers = Driver.objects.filter(partner=partner_pk)
    for driver in drivers:
        BoltRequest(partner_pk).get_fleet_orders(day, driver.pk)
        UklonRequest(partner_pk).get_fleet_orders(day, driver.pk)
    if not FleetOrder.objects.filter(fleet="Uber", accepted_time__date=day):
        uber_driver = SeleniumTools(partner_pk)
        uber_driver.download_payments_order("Uber", day)
        uber_driver.save_trips_report("Uber", day)
        uber_driver.quit()


@app.task(bind=True, queue='beat_tasks')
def download_daily_report(self, partner_pk, day=None):
    if day is None:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")
    BoltRequest(partner_pk).save_report(day)
    UklonRequest(partner_pk).save_report(day)
    UberRequest(partner_pk).save_report(day)
    save_report_to_ninja_payment(day, partner_pk)
    fleet_reports = Payments.objects.filter(report_from=day, partner=partner_pk)
    for driver in Driver.objects.filter(partner=partner_pk):
        payments = [r for r in fleet_reports if r.driver_id == driver.get_driver_external_id(r.vendor_name)]
        if payments:
            if not SummaryReport.objects.filter(report_from=day, full_name=driver, partner=partner_pk):
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


@app.task(bind=True, queue='beat_tasks')
def get_car_efficiency(self, partner_pk, day=None):
    if not day:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")

    for vehicle in Vehicle.objects.filter(driver__isnull=False, partner=partner_pk):
        efficiency = CarEfficiency.objects.filter(report_from=day,
                                                  partner=partner_pk,
                                                  licence_plate=vehicle.licence_plate)
        if not efficiency:
            total_kasa = 0
            total_km = UaGpsSynchronizer(partner_pk).total_per_day(vehicle.gps_id, day)

            total_spendings = VehicleSpendings.objects.filter(
                vehicle=vehicle, created_at__date=day).aggregate(Sum('amount'))['amount__sum'] or 0
            result = - Decimal(total_spendings)
            if total_km:
                for driver in Driver.objects.filter(vehicle=vehicle):
                    report = SummaryReport.objects.filter(report_from=day,
                                                          full_name=driver).first()
                    if report:
                        total_kasa += report.total_amount_without_fee

                result = max(
                    Decimal(total_kasa) - Decimal(total_spendings), Decimal(0)) / Decimal(total_km) if total_km else 0
            CarEfficiency.objects.create(report_from=day,
                                         licence_plate=vehicle.licence_plate,
                                         total_kasa=total_kasa,
                                         total_spendings=total_spendings,
                                         mileage=total_km,
                                         efficiency=result,
                                         partner=Partner.get_partner(partner_pk))


@app.task(bind=True, queue='beat_tasks')
def get_driver_efficiency(self, partner_pk, day=None):
    if not day:
        day = timezone.localtime() - timedelta(days=1)
    else:
        day = datetime.strptime(day, "%Y-%m-%d")
    for driver in Driver.objects.filter(partner=partner_pk):
        efficiency = DriverEfficiency.objects.filter(report_from=day,
                                                     partner=partner_pk,
                                                     driver=driver)
        vehicle, reshuffle = check_reshuffle(driver, day)
        if not efficiency and vehicle:
            accept = 0
            avg_price = 0
            total_km = 0
            if reshuffle:
                total_km = UaGpsSynchronizer(partner_pk).total_per_day(vehicle.gps_id,
                                                                       day, driver, reshuffle)
            elif vehicle:
                total_km = UaGpsSynchronizer(partner_pk).total_per_day(vehicle.gps_id, day)
            report = SummaryReport.objects.filter(report_from=day, full_name=driver).first()
            total_kasa = report.total_amount_without_fee if report else 0
            result = Decimal(total_kasa)/Decimal(total_km) if total_km else 0
            orders = FleetOrder.objects.filter(driver=driver, accepted_time__date=day)
            total_orders = orders.count()
            if total_orders:
                canceled = orders.filter(state=FleetOrder.DRIVER_CANCEL).count()
                accept = int((total_orders-canceled)/total_orders * 100) if canceled else 100
                avg_price = Decimal(total_kasa) / Decimal(total_orders)
            hours_online = timedelta()
            using_info = UseOfCars.objects.filter(created_at__date=day, user_vehicle=driver)
            start = timezone.datetime.combine(day, datetime.min.time()).astimezone()
            end = timezone.datetime.combine(day, datetime.max.time()).astimezone()
            yesterday = day - timedelta(days=1)
            for report in using_info:
                if report.end_at:
                    if report.end_at.date() == day:
                        hours_online += report.end_at - report.created_at
                else:
                    hours_online += end - report.created_at

            last_using = UseOfCars.objects.filter(created_at__date=yesterday,
                                                  user_vehicle=driver,
                                                  end_at__date=day).first()
            if last_using:
                hours_online += last_using.end_at - start

            DriverEfficiency.objects.create(report_from=day,
                                            driver=driver,
                                            total_kasa=total_kasa,
                                            total_orders=total_orders,
                                            accept_percent=accept,
                                            average_price=avg_price,
                                            mileage=total_km or 0,
                                            online_time=hours_online,
                                            efficiency=result,
                                            partner=Partner.get_partner(partner_pk))


@app.task(bind=True, queue='beat_tasks')
def update_driver_status(self, partner_pk):
    try:
        bolt_status = BoltRequest(partner_pk).get_drivers_status()
        logger.info(f'Bolt {bolt_status}')

        uklon_status = UklonRequest(partner_pk).get_driver_status()
        logger.info(f'Uklon {uklon_status}')

        uber_status = UberRequest(partner_pk).get_drivers_status()
        logger.info(f'Uber {uber_status}')

        status_online = set()
        status_with_client = set()
        if bolt_status is not None:
            status_online = status_online.union(set(bolt_status['wait']))
            status_with_client = status_with_client.union(set(bolt_status['with_client']))
        if uklon_status is not None:
            status_online = status_online.union(set(uklon_status['wait']))
            status_with_client = status_with_client.union(set(uklon_status['width_client']))
        if uber_status is not None:
            status_online = status_online.union(set(uber_status['wait']))
            status_with_client = status_with_client.union(set(uber_status['with_client']))
        drivers = Driver.objects.filter(deleted_at=None, partner=partner_pk)
        for driver in drivers:
            active_order = Order.objects.filter(driver=driver, status_order=Order.IN_PROGRESS)
            work_ninja = UseOfCars.objects.filter(user_vehicle=driver, partner=partner_pk,
                                                  created_at__date=timezone.localtime().date(), end_at=None).first()
            if active_order or (driver.name, driver.second_name) in status_with_client:
                current_status = Driver.WITH_CLIENT
            elif (driver.name, driver.second_name) in status_online:
                current_status = Driver.ACTIVE
            else:
                current_status = Driver.OFFLINE
            driver.driver_status = current_status
            driver.save()
            if current_status != Driver.OFFLINE:
                vehicle = check_reshuffle(driver)[0]
                if not work_ninja and vehicle and driver.chat_id:
                    UseOfCars.objects.create(user_vehicle=driver,
                                             partner=Partner.get_partner(partner_pk),
                                             licence_plate=vehicle.licence_plate,
                                             chat_id=driver.chat_id)
                logger.warning(f'{driver}: {current_status}')
            else:
                if work_ninja:
                    work_ninja.end_at = timezone.localtime()
                    work_ninja.save()
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='bot_tasks')
def update_driver_data(self, partner_pk, manager_id=None):
    try:
        settings = ParkSettings.objects.filter(
            Q(key="BOLT_PASSWORD") |
            Q(key="UKLON_PASSWORD") |
            Q(key="UBER_PASSWORD") |
            Q(key="UAGPS_TOKEN"),
            partner=partner_pk
        )
        synchronize_classes = {
            "BOLT_PASSWORD": BoltRequest,
            "UKLON_PASSWORD": UklonRequest,
            "UBER_PASSWORD": UberRequest,
            "UAGPS_TOKEN": UaGpsSynchronizer,
        }
        for setting in settings:
            synchronization_class = synchronize_classes.get(setting.key)
            if synchronization_class:
                synchronization_class(partner_pk).synchronize()
    except Exception as e:
        logger.error(e)
    return manager_id


@app.task(bind=True, queue='bot_tasks')
def send_on_job_application_on_driver(self, job_id):
    try:
        candidate = JobApplication.objects.get(id=job_id)
        SeleniumTools().add_driver(candidate)
        BoltRequest().add_driver(candidate)
        logger.info('The job application has been sent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='bot_tasks')
def detaching_the_driver_from_the_car(self, partner_pk, licence_plate):
    try:
        UklonRequest(partner_pk).detaching_the_driver_from_the_car(licence_plate)
        logger.info(f'Car {licence_plate} was detached')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def get_rent_information(self, partner_pk, delta=1):
    try:
        UaGpsSynchronizer(partner_pk).save_daily_rent(delta)
        logger.info('write rent report')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='bot_tasks')
def fleets_cash_trips(self, partner_pk, pk, enable):
    try:
        UklonRequest(partner_pk).disable_cash(pk, enable)
        logger.info('disable_uklon_cash')
        BoltRequest(partner_pk).cash_restriction(pk, enable)
        logger.info('disable_bolt_cash')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def withdraw_uklon(self, partner_pk):
    try:
        UklonRequest(partner_pk).withdraw_money()
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def manager_paid_weekly(self, partner_pk):
    logger.info('send message to manager')
    return partner_pk


@app.task(bind=True, queue='beat_tasks')
def send_weekly_report(self, partner_pk):
    return generate_message_weekly(partner_pk)


@app.task(bind=True, queue='beat_tasks')
def send_daily_report(self, partner_pk):
    message = ''
    dict_msg = {}
    for manager in Manager.objects.filter(chat_id__isnull=False, partner=partner_pk):
        result = get_daily_report(manager_id=manager.chat_id)
        if result:
            for num, key in enumerate(result[0], 1):
                if result[0][key]:
                    num = "\U0001f3c6" if num == 1 else f"{num}."
                    message += "{}{}\nКаса: {:.2f} (+{:.2f})\n Оренда: {:.2f}км (+{:.2f})\n".format(
                        num, key, result[0][key], result[1].get(key, 0), result[2].get(key, 0), result[3].get(key, 0))
            dict_msg[partner_pk] = message
    return dict_msg


@app.task(bind=True, queue='beat_tasks')
def send_efficiency_report(self, partner_pk):
    message = ''
    dict_msg = {}
    for manager in Manager.objects.filter(chat_id__isnull=False, partner=partner_pk):
        result = get_efficiency(manager_id=manager.chat_id)
        if result:
            for k, v in result.items():
                message += f"{k}\n" + "".join(v)
            dict_msg[partner_pk] = message
    return dict_msg


@app.task(bind=True, queue='beat_tasks')
def send_driver_efficiency(self, partner_pk):
    message = ''
    dict_msg = {}
    for manager in Manager.objects.filter(chat_id__isnull=False, partner=partner_pk):
        result = get_driver_efficiency_report(manager_id=manager.chat_id)
        if result:
            for k, v in result.items():
                message += f"{k}\n" + "".join(v) + "\n"
            dict_msg[partner_pk] = message
    return dict_msg


@app.task(bind=True, queue='bot_tasks')
def check_time_order(self, order_id):
    try:
        instance = Order.objects.get(pk=order_id)
    except ObjectDoesNotExist:
        return
    text = order_info(instance, time=True) if instance.type_order == Order.STANDARD_TYPE \
        else personal_order_info(instance)
    group_msg = bot.send_message(chat_id=ParkSettings.get_value('ORDER_CHAT'),
                                 text=text,
                                 reply_markup=inline_markup_accept(instance.pk),
                                 parse_mode=ParseMode.HTML)
    redis_instance().hset('group_msg', order_id, group_msg.message_id)
    instance.checked = True
    instance.save()


@app.task(bind=True, queue='beat_tasks')
def check_personal_orders(self):
    for order in Order.objects.filter(status_order=Order.IN_PROGRESS, type_order=Order.PERSONAL_TYPE):
        finish_time = timezone.localtime(order.order_time) + timedelta(hours=order.payment_hours)
        distance = int(order.payment_hours) * int(ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR'))
        notify_min = int(ParkSettings.get_value('PERSONAL_CLIENT_NOTIFY_MIN'))
        notify_km = int(ParkSettings.get_value('PERSONAL_CLIENT_NOTIFY_KM'))
        vehicle = check_reshuffle(order.driver)[0]
        gps = UaGpsSynchronizer(order.driver.partner)
        route = gps.generate_report(gps.get_timestamp(order.order_time),
                                    gps.get_timestamp(finish_time), vehicle.gps_id)[0]
        pc_message = redis_instance().hget(str(order.chat_id_client), "client_msg")
        pd_message = redis_instance().hget(str(order.driver.chat_id), "driver_msg")
        if timezone.localtime() > finish_time or distance < route:
            if redis_instance().hget(str(order.chat_id_client), "finish") == order.id:
                bot.edit_message_text(chat_id=order.driver.chat_id,
                                      message_id=pd_message, text=driver_complete_text(order.sum))
                order.status_order = Order.COMPLETED
                order.partner = order.driver.partner
                order.save()
            else:
                client_msg = text_to_client(order, text=client_text_personal_end,
                                            button=personal_order_end_kb(order.id), delete_id=pc_message)
                driver_msg = bot.edit_message_text(chat_id=order.driver.chat_id,
                                                   message_id=pd_message,
                                                   text=driver_text_personal_end,
                                                   reply_markup=personal_driver_end_kb(order.id))
                redis_instance().hset(str(order.driver.chat_id), "driver_msg", driver_msg.message_id)
                redis_instance().hset(str(order.chat_id_client), "client_msg", client_msg)
        elif timezone.localtime() + timedelta(minutes=notify_min) > finish_time or distance < route - notify_km:
            pre_finish_text = personal_time_route_end(finish_time, distance-route)
            pc_message = bot.send_message(chat_id=order.chat_id_client,
                                          text=pre_finish_text,
                                          reply_markup=personal_order_end_kb(order.id, pre_finish=True))
            pd_message = bot.send_message(chat_id=order.driver.chat_id,
                                          text=pre_finish_text)
            redis_instance().hset(str(order.driver.chat_id), "driver_msg", pd_message.message_id)
            redis_instance().hset(str(order.chat_id_client), "client_msg", pc_message.message_id)


@app.task(bind=True, queue='beat_tasks')
def add_money_to_vehicle(self, partner_pk):
    yesterday = timezone.localtime() - timedelta(days=1)
    car_efficiency_records = CarEfficiency.objects.filter(report_from=yesterday.date(), partner=partner_pk)
    sum_by_plate = car_efficiency_records.values('licence_plate').annotate(total_sum=Sum('total_kasa'))
    for result in sum_by_plate:
        vehicle = Vehicle.objects.filter(licence_plate=result['licence_plate'], partner=partner_pk).first()
        if vehicle:
            currency = vehicle.сurrency_back
            total_kasa = result['total_sum']
            if currency != Vehicle.Currency.UAH:
                result, rate = convert_to_currency(float(total_kasa), currency)
                car_earnings = result * vehicle.investor_percentage
            else:
                car_earnings = total_kasa * vehicle.investor_percentage
                rate = 0.00
            vehicle.car_earnings += car_earnings
            vehicle.save()

            TransactionsConversantion.objects.create(
                vehicle=vehicle,
                sum_before_transaction=total_kasa / 2,
                сurrency=currency,
                currency_rate=rate,
                sum_after_transaction=car_earnings)


@app.task(bind=True, queue='beat_tasks')
def order_not_accepted(self):
    instances = Order.objects.filter(status_order=Order.ON_TIME, driver__isnull=True)
    for order in instances:
        if order.order_time < (timezone.localtime() + timedelta(
                minutes=int(ParkSettings.get_value('SEND_TIME_ORDER_MIN')))):
            group_msg = redis_instance().hget('group_msg', order.id)
            if order.type_order == Order.STANDARD_TYPE:
                bot.delete_message(chat_id=ParkSettings.get_value("ORDER_CHAT"), message_id=group_msg)
                redis_instance().hdel('group_msg', order.id)
                search_driver_for_order.delay(order.id)
            else:
                for manager in Manager.objects.exclude(chat_id__isnull=True):
                    if not redis_instance().hexists(str(manager.chat_id), f'personal {order.id}'):
                        redis_instance().hset(str(manager.chat_id), f'personal {order.id}', order.id)
                        bot.send_message(chat_id=manager.chat_id, text=pd_order_not_accepted)
                        bot.forward_message(chat_id=manager.chat_id,
                                            from_chat_id=ParkSettings.get_value("ORDER_CHAT"),
                                            message_id=group_msg)


@app.task(bind=True, queue='beat_tasks')
def send_time_order(self):
    accepted_orders = Order.objects.filter(status_order=Order.ON_TIME, driver__isnull=False)
    for order in accepted_orders:
        if timezone.localtime() < order.order_time < (timezone.localtime() + timedelta(minutes=int(
                ParkSettings.get_value('SEND_TIME_ORDER_MIN', 10)))):
            if order.type_order == Order.STANDARD_TYPE:
                text = order_info(order, time=True)
                reply_markup = inline_spot_keyboard(order.latitude, order.longitude, order.id)
            else:
                text = personal_order_info(order)
                reply_markup = inline_spot_keyboard(order.latitude, order.longitude)
            driver_msg = bot.send_message(chat_id=order.driver.chat_id, text=text,
                                          reply_markup=reply_markup,
                                          parse_mode=ParseMode.HTML)
            driver = order.driver
            redis_instance().hset(str(order.driver.chat_id), 'driver_msg', driver_msg.message_id)
            order.status_order, order.accepted_time = Order.IN_PROGRESS, timezone.localtime()
            order.save()
            if order.chat_id_client:
                vehicle = check_reshuffle(driver)[0]
                lat, long = get_location_from_db(vehicle.licence_plate)
                bot.send_message(chat_id=order.chat_id_client, text=order_customer_text)
                message = bot.sendLocation(order.chat_id_client, latitude=lat, longitude=long, live_period=1800)
                send_map_to_client.delay(order.id, vehicle.licence_plate, message.message_id, message.chat_id)


@app.task(bind=True, max_retries=3, queue='bot_tasks')
def order_create_task(self, order_data):
    try:
        distance_price = get_route_price(order_data['latitude'], order_data['longitude'],
                                         order_data['to_latitude'], order_data['to_longitude'],
                                         ParkSettings.get_value('GOOGLE_API_KEY'))

        order_data['sum'] = distance_price[0]
        order_data['distance_google'] = round(distance_price[1], 2)
        Order.objects.create(**order_data)
    except Exception as e:
        if self.request.retries <= self.max_retries:
            self.retry(exc=e, countdown=5)
        else:
            bot.send_message(chat_id=515224934, text=str(e))
            raise MaxRetriesExceededError("Max retries exceeded for task.")


@app.task(bind=True, max_retries=3, queue='bot_tasks')
def search_driver_for_order(self, order_pk):

    try:
        order = Order.objects.get(id=order_pk)
        if order.status_order == Order.CANCELED:
            return
        if order.status_order == Order.ON_TIME:
            order.status_order = Order.WAITING
            order.order_time = None
            order.save()
            if order.chat_id_client:
                bot.send_message(chat_id=order.chat_id_client,
                                 text=no_driver_in_radius,
                                 reply_markup=inline_search_kb())
            return
        client_msg = redis_instance().hget(str(order.chat_id_client), 'client_msg')
        if self.request.retries == self.max_retries:
            if order.chat_id_client:
                bot.edit_message_text(chat_id=order.chat_id_client,
                                      text=no_driver_in_radius,
                                      reply_markup=inline_search_kb(),
                                      message_id=client_msg)
            return
        if self.request.retries == 0:
            bot.edit_message_text(chat_id=order.chat_id_client, text=client_order_info(order), message_id=client_msg)
            last_msg = text_to_client(order, search_driver, button=inline_reject_order(order.pk))
            redis_instance().hset(order.chat_id_client, 'client_msg', last_msg)
        elif self.request.retries == 1:
            text_to_client(order, search_driver_1, message_id=client_msg,
                           button=inline_reject_order(order.pk))
        else:
            text_to_client(order, search_driver_2, message_id=client_msg,
                           button=inline_reject_order(order.pk))
        drivers = Driver.objects.filter(chat_id__isnull=False, vehicle__isnull=False)
        for driver in drivers:
            if driver.driver_status == Driver.ACTIVE:
                vehicle = check_reshuffle(driver)[0]
                driver_lat, driver_long = get_location_from_db(vehicle.licence_plate)
                distance = haversine(float(driver_lat), float(driver_long),
                                     float(order.latitude), float(order.longitude))
                radius = int(ParkSettings.get_value('FREE_CAR_SENDING_DISTANCE')) + \
                         order.car_delivery_price / int(ParkSettings.get_value('TARIFF_CAR_DISPATCH'))
                if distance <= radius:
                    accept_message = bot.send_message(chat_id=driver.chat_id,
                                                      text=order_info(order),
                                                      reply_markup=inline_markup_accept(order.pk))
                    end_time = tm.time() + int(ParkSettings.get_value("MESSAGE_APPEAR"))
                    while tm.time() < end_time:
                        Driver.objects.filter(id=driver.id).update(driver_status=Driver.GET_ORDER)
                        upd_driver = Driver.objects.get(id=driver.id)
                        instance = Order.objects.get(id=order.id)
                        if instance.status_order == Order.CANCELED:
                            bot.delete_message(chat_id=driver.chat_id,
                                               message_id=accept_message.message_id)
                            return
                        if instance.driver == upd_driver:
                            return
                    bot.delete_message(chat_id=driver.chat_id,
                                       message_id=accept_message.message_id)
                    bot.send_message(chat_id=driver.chat_id,
                                     text=decline_order)
            else:
                continue
        self.retry(args=[order_pk], countdown=30)
    except ObjectDoesNotExist as e:
        logger.error(e)


@app.task(bind=True, max_retries=90, queue='bot_tasks')
def send_map_to_client(self, order_pk, licence, message, chat):
    order = Order.objects.get(id=order_pk)
    if order.chat_id_client:
        try:
            latitude, longitude = get_location_from_db(licence)
            distance = haversine(float(latitude), float(longitude), float(order.latitude), float(order.longitude))
            if order.status_order in (Order.CANCELED, Order.WAITING):
                bot.stopMessageLiveLocation(chat, message)
                return
            elif distance < float(ParkSettings.get_value('SEND_DISPATCH_MESSAGE')):
                bot.stopMessageLiveLocation(chat, message)
                client_msg = redis_instance().hget(str(order.chat_id_client), 'client_msg')
                driver_msg = redis_instance().hget(str(order.driver.chat_id), 'driver_msg')
                text_to_client(order, driver_arrived, delete_id=client_msg)
                redis_instance().hset(str(order.driver.chat_id), 'start_route', int(timezone.localtime().timestamp()))
                reply_markup = inline_client_spot(order_pk, message) if \
                    order.type_order == Order.STANDARD_TYPE else None
                bot.edit_message_reply_markup(chat_id=order.driver.chat_id,
                                              message_id=driver_msg,
                                              reply_markup=reply_markup)
            else:
                bot.editMessageLiveLocation(chat, message, latitude=latitude, longitude=longitude)
                self.retry(args=[order_pk, licence, message, chat], countdown=20)
        except BadRequest as e:
            if "Message can't be edited" in str(e) or order.status_order in (Order.CANCELED, Order.WAITING):
                pass
            else:
                raise self.retry(args=[order_pk, licence, message, chat], countdown=30) from e
        except StopIteration:
            pass
        except Exception as e:
            logger.error(msg=str(e))
            self.retry(args=[order_pk, licence, message, chat], countdown=30)
        if self.request.retries >= self.max_retries:
            bot.stopMessageLiveLocation(chat, message)
        return message


@app.task(bind=True, queue='bot_tasks')
def get_distance_trip(self, order, query, start_trip_with_client, end, gps_id):
    start = datetime.fromtimestamp(start_trip_with_client)
    format_end = datetime.fromtimestamp(end)
    delta = format_end - start
    try:
        instance = Order.objects.filter(pk=order).first()
        result = UaGpsSynchronizer(instance.driver.partner).generate_report(start_trip_with_client, end, gps_id)
        minutes = delta.total_seconds() // 60
        instance.distance_gps = result[0]
        price_per_minute = (int(ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR')) *
                            int(ParkSettings.get_value('COST_PER_KM'))) / 60
        price_per_minute = price_per_minute * minutes
        price_per_distance = round(int(ParkSettings.get_value('COST_PER_KM')) * result[0])
        if price_per_distance > price_per_minute:
            instance.sum = int(price_per_distance) + int(instance.car_delivery_price)
        else:
            instance.sum = int(price_per_minute) + int(instance.car_delivery_price)
        instance.save()
        text_to_client(order=instance, text=f'Сума до cплати: {instance.sum} грн\n {complete_order_text}')
        message = driver_complete_text(instance.sum)
        bot.edit_message_text(chat_id=instance.driver.chat_id, message_id=query, text=message)
    except Exception as e:
        logger.info(e)


@app.task(bind=True, queue='beat_tasks')
def get_driver_reshuffles(self):
    day = timezone.localtime() - timedelta(days=1)
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = timezone.make_aware(datetime.combine(day, time.max))
    events = GoogleCalendar().get_list_events(ParkSettings.get_value("GOOGLE_ID_ORDER_CALENDAR"), start, end)
    for event in events['items']:
        calendar_event_id = event['id']
        event_summary = event['summary'].split(',')
        if len(event_summary) == 2:
            licence_plate, driver = event_summary
            name, second_name = driver.split()
            driver_start = Driver.objects.filter(name=name, second_name=second_name).first()
            driver_finish = None
            vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
            swap_time = timezone.make_aware(datetime.strptime(event['start']['date'], "%Y-%m-%d"))
        else:
            swap_time = datetime.strptime(event['start']['dateTime'], "%Y-%m-%dT%H:%M:%S%z").astimezone()
            licence_plate, first_driver, second_driver = event_summary
            name, second_name = first_driver.split()
            other_name, other_second_name = second_driver.split()
            driver_start = Driver.objects.filter(Q(name=name, second_name=second_name) |
                                                 Q(name=second_name, second_name=name)).first()
            driver_finish = Driver.objects.filter(Q(name=other_name, second_name=other_second_name) |
                                                  Q(name=other_second_name, second_name=other_name)).first()
            vehicle = Vehicle.objects.filter(licence_plate=licence_plate).first()
        obj_data = {
            "calendar_event_id": calendar_event_id,
            "swap_vehicle": vehicle,
            "driver_start": driver_start,
            "driver_finish": driver_finish,
            "swap_time": swap_time
        }
        reshuffle = DriverReshuffle.objects.filter(calendar_event_id=calendar_event_id)
        reshuffle.update(**obj_data) if reshuffle else DriverReshuffle.objects.create(**obj_data)


def save_report_to_ninja_payment(day, partner_pk, fleet_name='Ninja'):
    reports = Payments.objects.filter(report_from=day, vendor_name=fleet_name, partner=partner_pk)
    if reports:
        return reports
    # Pulling notes for the rest of the week and grouping behind the chat_id field
    for driver in Driver.objects.exclude(chat_id=''):
        records = Order.objects.filter(driver__chat_id=driver.chat_id,
                                       status_order=Order.COMPLETED,
                                       created_at__date=day,
                                       partner=partner_pk)
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
            total_amount_without_fee=total_amount,
            partner=Partner.get_partner(partner_pk))
        try:
            report.save()
        except IntegrityError:
            pass


@app.on_after_finalize.connect
def run_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(minute="*/2"), send_time_order.s())
    sender.add_periodic_task(crontab(minute='*/15'), auto_send_task_bot.s())
    sender.add_periodic_task(crontab(minute="*/2"), order_not_accepted.s())
    sender.add_periodic_task(crontab(minute="*/4"), check_personal_orders.s())
    for partner in Partner.objects.exclude(user__is_superuser=True):
        setup_periodic_tasks(partner, sender)


def setup_periodic_tasks(partner, sender=None):
    if sender is None:
        sender = current_app
    partner_id = partner.pk
    sender.add_periodic_task(20, update_driver_status.s(partner_id))
    sender.add_periodic_task(crontab(minute="0", hour="4"), download_daily_report.s(partner_id))
    # sender.add_periodic_task(crontab(minute="0", hour='*/2'), withdraw_uklon.s(partner_id))
    sender.add_periodic_task(crontab(minute="40", hour='4'), get_rent_information.s(partner_id))
    sender.add_periodic_task(crontab(minute="30", hour='1'), get_driver_reshuffles.s(partner_id))
    sender.add_periodic_task(crontab(minute="15", hour='4'), get_orders_from_fleets.s(partner_id))
    sender.add_periodic_task(crontab(minute="2", hour="9"), send_driver_efficiency.s(partner_id))
    sender.add_periodic_task(crontab(minute="0", hour="9"), send_efficiency_report.s(partner_id))
    sender.add_periodic_task(crontab(minute="30", hour="7"), get_car_efficiency.s(partner_id))
    sender.add_periodic_task(crontab(minute="0", hour="5"), add_money_to_vehicle.s(partner_id))
    sender.add_periodic_task(crontab(minute="20", hour="4"), get_driver_efficiency.s(partner_id))
    sender.add_periodic_task(crontab(minute="1", hour="9"), send_daily_report.s(partner_id))
    sender.add_periodic_task(crontab(minute="55", hour="8", day_of_week="1"),
                             send_weekly_report.s(partner_id))
    sender.add_periodic_task(crontab(minute="55", hour="11", day_of_week="1"),
                             manager_paid_weekly.s(partner_id))
    sender.add_periodic_task(crontab(minute="55", hour="9", day_of_week="1"),
                             get_uber_session.s(partner_id))


def remove_periodic_tasks(partner, sender=None):
    if sender is None:
        sender = current_app
    partner_id = partner.pk
    sender.remove_periodic_task(f"update_driver_status.s({partner_id})")
    sender.remove_periodic_task(f"update_driver_data.s({partner_id})")
    sender.remove_periodic_task(f"download_daily_report.s({partner_id})")
    sender.remove_periodic_task(f"withdraw_uklon.s({partner_id})")
    sender.remove_periodic_task(f"get_rent_information.s({partner_id})")
    sender.remove_periodic_task(f"send_efficiency_report.s({partner_id})")
    sender.remove_periodic_task(f"get_car_efficiency.s({partner_id})")
    sender.remove_periodic_task(f"send_daily_report.s({partner_id})")
    sender.remove_periodic_task(f"send_weekly_report.s({partner_id})")
    sender.remove_periodic_task(f"manager_paid_weekly.s({partner_id})")
    sender.remove_periodic_task(f"get_uber_session.s({partner_id})")
