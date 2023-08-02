from datetime import datetime, timedelta
import time
from _decimal import Decimal
from celery import current_app
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils import timezone
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from telegram import ParseMode
from telegram.error import BadRequest, Unauthorized

from app.models import RawGPS, Vehicle, VehicleGPS, Order, Driver, JobApplication, ParkStatus, ParkSettings, \
    UseOfCars, CarEfficiency, Payments, SummaryReport, DriverManager, Partner
from django.db.models import Sum, IntegerField, FloatField
from django.db.models.functions import Cast, Coalesce
from auto_bot.handlers.driver_manager.utils import get_daily_report, get_efficiency, generate_message_weekly
from auto_bot.handlers.main.keyboards import spam_driver_kb
from auto_bot.handlers.order.keyboards import inline_markup_accept, inline_search_kb, inline_client_spot, \
    inline_time_order_kb
from auto_bot.handlers.order.static_text import decline_order, order_info, client_order_info, search_driver_1, \
    search_driver_2, no_driver_in_radius, driver_arrived, complete_order_text, driver_complete_text
from auto_bot.handlers.order.utils import text_to_client
from auto_bot.handlers.status.static_text import please_start_text, unblock_text
from auto_bot.main import bot
from scripts.conversion import convertion, haversine, get_location_from_db, geocode, get_route_price
from auto.celery import app
from scripts.redis_conn import redis_instance
from selenium_ninja.bolt_sync import BoltRequest
from selenium_ninja.driver import SeleniumTools
from selenium_ninja.uagps_sync import UaGpsSynchronizer
from selenium_ninja.uber_sync import UberRequest
from selenium_ninja.uklon_sync import UklonRequest


logger = get_task_logger(__name__)


@app.task(queue='gps_tasks')
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


@app.task(bind=True, queue='beat_tasks')
def get_uber_session(self, partner_pk):
    SeleniumTools(partner_pk).uber_login()


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
                                                  created_at__date=timezone.localtime().date(), end_at=None)
            if active_order or (driver.name, driver.second_name) in status_with_client:
                current_status = Driver.WITH_CLIENT
            elif (driver.name, driver.second_name) in status_online:
                current_status = Driver.ACTIVE
            else:
                current_status = Driver.ACTIVE if work_ninja else Driver.OFFLINE
            driver.driver_status = current_status
            driver.save()
            if current_status != Driver.OFFLINE:
                if not work_ninja:
                    try:
                        bot.send_message(chat_id=driver.chat_id, text=please_start_text,
                                         reply_markup=spam_driver_kb())
                    except Unauthorized:
                        if not redis_instance.exists(f"{driver}_block"):
                            bot.send_message(chat_id=ParkSettings.get_value("DRIVERS_CHAT", partner=partner_pk),
                                             text=f"{driver} {unblock_text}")
                            redis_instance.set(f"{driver}_block", 'blocked', ex=3600)
                    except Exception as e:
                        logger.info(e)
                logger.info(f'{driver}: {current_status}')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def update_driver_data(self, partner_pk, manager_id=None):
    try:
        BoltRequest(partner_pk).synchronize()
        UklonRequest(partner_pk).synchronize()
        UberRequest(partner_pk).synchronize()
        UaGpsSynchronizer().get_vehicle_id()
    except Exception as e:
        logger.error(e)
    return manager_id


@app.task(bind=True, queue='beat_tasks')
def send_on_job_application_on_driver(self, job_id):
    try:
        candidate = JobApplication.objects.get(id=job_id)
        SeleniumTools().add_driver(candidate)
        BoltRequest().add_driver(candidate)
        logger.info('The job application has been sent')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def detaching_the_driver_from_the_car(self, partner_pk, licence_plate):
    try:
        UklonRequest(partner_pk).detaching_the_driver_from_the_car(licence_plate)
        logger.info(f'Car {licence_plate} was detached')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
def get_rent_information(self, partner_pk):
    try:
        UaGpsSynchronizer().get_rent_distance(partner_pk)
        logger.info('write rent report in uagps')
    except Exception as e:
        logger.error(e)


@app.task(bind=True, queue='beat_tasks')
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
    for manager in DriverManager.objects.filter(chat_id__isnull=False, partner=partner_pk):
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
    for manager in DriverManager.objects.filter(chat_id__isnull=False, partner=partner_pk):
        result = get_efficiency(manager_id=manager.chat_id)
        if result:
            for k, v in result.items():
                message += f"{k}\n" + "".join(v)
            dict_msg[partner_pk] = message
    return dict_msg


@app.task(bind=True, queue='beat_tasks')
def check_time_order(self, order_id):
    try:
        instance = Order.objects.get(pk=order_id)
    except ObjectDoesNotExist:
        return
    order_time = timezone.localtime(instance.order_time)
    message = order_info(instance.pk,
                         instance.from_address,
                         instance.to_the_address,
                         instance.payment_method,
                         instance.phone_number,
                         instance.sum,
                         instance.distance_google,
                         time=order_time.strftime("%Y-%m-%d %H:%M"))

    group_msg = bot.send_message(chat_id=ParkSettings.get_value('ORDER_CHAT'),
                                 text=message,
                                 reply_markup=inline_markup_accept(instance.pk),
                                 parse_mode=ParseMode.HTML)
    instance.driver_message_id, instance.checked = group_msg.message_id, True
    instance.save()


@app.task(bind=True, queue='beat_tasks')
def send_time_order(self):
    logger.info('sending_time_orders')
    accepted_orders = Order.objects.filter(status_order=Order.ON_TIME, driver__isnull=False)
    for order in accepted_orders:
        if timezone.localtime() < order.order_time < (timezone.localtime() + timedelta(minutes=int(
                ParkSettings.get_value('SEND_TIME_ORDER_MIN', 10)))):
            markup = inline_time_order_kb(order.id)
            text = order_info(order.pk, order.from_address, order.to_the_address,
                              order.payment_method, order.phone_number, order.sum,
                              order.distance_google,
                              time=timezone.localtime(order.order_time).time())

            bot.send_message(chat_id=order.driver.chat_id, text=text,
                             reply_markup=markup, parse_mode=ParseMode.HTML)


@app.task(bind=True, max_retries=3, queue='beat_tasks')
def order_create_task(self, context, phone, chat_id, payment, message_id):
    try:
        if 'from_address' not in context:
            context['from_address'] = context['location_address']
        else:
            from_place = context['addresses_first'].get(context['from_address'])
            context['latitude'], context['longitude'] = geocode(from_place, ParkSettings.get_value('GOOGLE_API_KEY'))

        destination_place = context['addresses_second'].get(context['to_the_address'])
        destination_lat, destination_long = geocode(destination_place, ParkSettings.get_value('GOOGLE_API_KEY'))

        distance_price = get_route_price(context['latitude'], context['longitude'],
                                         destination_lat, destination_long,
                                         ParkSettings.get_value('GOOGLE_API_KEY'))

        order_data = {
            'from_address': context['from_address'],
            'latitude': context['latitude'],
            'longitude': context['longitude'],
            'to_the_address': context['to_the_address'],
            'to_latitude': destination_lat,
            'to_longitude': destination_long,
            'phone_number': phone,
            'chat_id_client': chat_id,
            'payment_method': payment,
            'client_message_id': message_id,
            'sum': distance_price[0],
            'distance_google': round(distance_price[1], 2)
        }

        if 'time_order' in context:
            order_data['status_order'] = Order.ON_TIME
            order_data['order_time'] = context['time_order']
            order_time = context['time_order'].strftime("%Y-%m-%d %H:%M")
            bot.edit_message_text(chat_id=chat_id, text=f'Замовлення прийняте, сума замовлення {order_data["sum"]}грн\n'
                                                        f'Очікуйте водія {order_time}', message_id=message_id)
        else:
            order_data['status_order'] = Order.WAITING

        Order.objects.create(**order_data)
    except Exception as e:
        bot.send_message(chat_id=515224934, text=str(e))


@app.task(bind=True, max_retries=3, queue='beat_tasks')
def search_driver_for_order(self, order_pk):
    try:
        order = Order.objects.get(id=order_pk)
        client_msg = client_order_info(order.from_address,
                                       order.to_the_address,
                                       order.payment_method,
                                       order.phone_number,
                                       order.sum,
                                       increase=order.car_delivery_price)
        if self.request.retries == self.max_retries:
            if order.chat_id_client:
                bot.edit_message_text(chat_id=order.chat_id_client,
                                      text=no_driver_in_radius,
                                      reply_markup=inline_search_kb(),
                                      message_id=order.client_message_id)
            return
        if self.request.retries == 0:
            text_to_client(order, client_msg, message_id=order.client_message_id)
        elif self.request.retries == 1:
            text_to_client(order, search_driver_1, message_id=order.client_message_id)
        else:
            text_to_client(order, search_driver_2, message_id=order.client_message_id)
        drivers = Driver.objects.filter(chat_id__isnull=False)
        for driver in drivers:
            record = UseOfCars.objects.filter(user_vehicle=driver,
                                              created_at__date=timezone.now().date(),
                                              end_at=None).last()
            if record and driver.driver_status == Driver.ACTIVE:
                ParkStatus.objects.create(driver=driver, status=Driver.GET_ORDER)
                driver.driver_status = Driver.GET_ORDER
                driver.save()
                vehicle = Vehicle.objects.get(licence_plate=record.licence_plate)
                driver_lat, driver_long = get_location_from_db(vehicle)
                distance = haversine(float(driver_lat), float(driver_long),
                                     float(order.latitude), float(order.longitude))
                radius = int(ParkSettings.get_value('FREE_CAR_SENDING_DISTANCE')) + \
                         order.car_delivery_price / int(ParkSettings.get_value('TARIFF_CAR_DISPATCH'))
                if distance <= radius:
                    message = order_info(order.pk, order.from_address, order.to_the_address,
                                         order.payment_method, order.phone_number, order.sum, order.distance_google)
                    markup = inline_markup_accept(order.pk)
                    accept_message = bot.send_message(chat_id=driver.chat_id,
                                                      text=message,
                                                      reply_markup=markup)
                    end_time = time.time() + int(ParkSettings.get_value("MESSAGE_APPEAR"))
                    while time.time() < end_time:
                        upd_driver = Driver.objects.get(id=driver.id)
                        instance = Order.objects.get(id=order.id)
                        if instance.driver == upd_driver:
                            try:
                                bot.edit_message_text(chat_id=order.chat_id_client,
                                                      text=client_msg,
                                                      message_id=order.client_message_id)
                            except BadRequest as e:
                                logger.info(e)
                            return
                    bot.delete_message(chat_id=driver.chat_id,
                                       message_id=accept_message.message_id)
                    bot.send_message(chat_id=driver.chat_id,
                                     text=decline_order)
                ParkStatus.objects.create(driver=driver, status=Driver.ACTIVE)
                driver.driver_status = Driver.ACTIVE
                driver.save()
            else:
                continue
        self.retry(args=[order_pk], countdown=30)
    except ObjectDoesNotExist as e:
        logger.error(e)


@app.task(bind=True, max_retries=90, queue='beat_tasks')
def send_map_to_client(self, order_pk, query_id, vehicle, client_msg, message, chat):
    order = Order.objects.get(id=order_pk)
    if order.chat_id_client:
        try:
            latitude, longitude = get_location_from_db(vehicle)
            distance = haversine(float(latitude), float(longitude), float(order.latitude), float(order.longitude))
            if order.status_order in (Order.CANCELED, Order.WAITING):
                bot.stopMessageLiveLocation(chat, message)
                return
            elif distance < float(ParkSettings.get_value('SEND_DISPATCH_MESSAGE')):
                bot.stopMessageLiveLocation(chat, message)
                text_to_client(order, driver_arrived, delete_id=client_msg)
                bot.edit_message_reply_markup(chat_id=order.driver.chat_id,
                                              message_id=query_id,
                                              reply_markup=inline_client_spot(order_pk, message))
            else:
                bot.editMessageLiveLocation(chat, message, latitude=latitude, longitude=longitude)
                self.retry(args=[order_pk, query_id, vehicle, client_msg, message, chat], countdown=20)
        except BadRequest as e:
            if "Message can't be edited" in str(e) or order.status_order in (Order.CANCELED, Order.WAITING):
                pass
            else:
                raise self.retry(args=[order_pk, query_id, vehicle, client_msg, message, chat], countdown=30) from e
        except StopIteration:
            pass
        except Exception as e:
            logger.error(msg=str(e))
            self.retry(args=[order_pk, query_id, vehicle, client_msg, message, chat], countdown=30)
        if self.request.retries >= self.max_retries:
            bot.stopMessageLiveLocation(chat, message)
        return message


@app.task(bind=True, queue='beat_tasks')
def get_distance_trip(self, order, query, start_trip_with_client, end, gps_id):
    start = datetime.fromtimestamp(start_trip_with_client)
    format_end = datetime.fromtimestamp(end)
    delta = format_end - start
    try:
        result = UaGpsSynchronizer().generate_report(start_trip_with_client, end, gps_id)
        minutes = delta.total_seconds() // 60
        instance = Order.objects.filter(pk=order).first()
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
    sender.add_periodic_task(crontab(minute=f"*/{ParkSettings.get_value('CHECK_ORDER_TIME_MIN', 5)}"),
                             send_time_order.s(), queue='beat_tasks')
    for partner in Partner.objects.exclude(user__is_superuser=True):
        setup_periodic_tasks(partner, sender)


def setup_periodic_tasks(partner, sender=None):
    if sender is None:
        sender = current_app
    partner_id = partner.pk
    sender.add_periodic_task(20, update_driver_status.s(partner_id))
    sender.add_periodic_task(crontab(minute=0, hour=2), update_driver_data.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=0, hour=4), download_daily_report.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=0, hour='*/2'), withdraw_uklon.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=59, hour='*/1'), get_rent_information.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=0, hour=6), send_efficiency_report.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=30, hour=4), get_car_efficiency.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=1, hour=6), send_daily_report.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=55, hour=5, day_of_week=1),
                             send_weekly_report.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=55, hour=8, day_of_week=1),
                             manager_paid_weekly.s(partner_id), queue='beat_tasks')
    sender.add_periodic_task(crontab(minute=55, hour=7, day_of_week=1),
                             get_uber_session.s(partner_id), queue='beat_tasks')


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
