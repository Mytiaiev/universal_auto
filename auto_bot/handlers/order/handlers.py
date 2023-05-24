import re
import datetime
import threading
import time
import requests
import os

from celery.signals import task_postrun
from django.utils import timezone
from telegram import ReplyKeyboardRemove, ParseMode, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from app.models import Order, User, Driver, Vehicle, UseOfCars, ParkStatus
from auto.tasks import logger, get_distance_trip, check_time_order, delete_button, check_order, send_time_order
from auto_bot.handlers.main.keyboards import markup_keyboard
from auto_bot.handlers.order.keyboards import inline_markup_accept, inline_spot_keyboard, inline_client_spot, \
    inline_route_keyboard, inline_finish_order, inline_repeat_keyboard, inline_reject_order, inline_time_order_kb, \
    inline_increase_price_kb, inline_search_kb, inline_start_order_kb, share_location, inline_location_kb,\
    inline_payment_kb
from auto_bot.handlers.order.utils import buttons_addresses, text_to_client
from auto_bot.main import bot
from scripts.conversion import get_address, geocode, get_location_from_db, get_route_price, haversine
from auto_bot.handlers.order.static_text import *


def continue_order(update, context):
    query = update.callback_query
    order = Order.objects.filter(chat_id_client=update.effective_chat.id,
                                 status_order__in=[Order.ON_TIME, Order.WAITING])
    reply_markup = inline_start_order_kb()
    if order:
        query.edit_message_text(text=already_ordered)
    else:
        context.user_data['state'] = START_TIME_ORDER
        context.user_data['location_button'] = False
        query.edit_message_text(text=price_info)
    query.edit_message_reply_markup(reply_markup=reply_markup)


def cancel_order(update, context):
    query = update.callback_query
    query.edit_message_text(text=complete_order_text)
    context.user_data.clear()


def get_location(update, context):
    location = update.message.location
    context.user_data['state'] = None
    context.user_data['location_button'] = True
    context.user_data['latitude'], context.user_data['longitude'] = location.latitude, location.longitude
    address = get_address(context.user_data['latitude'], context.user_data['longitude'],
                          ParkSettings.get_value('GOOGLE_API_KEY'))
    if address is not None:
        context.user_data['location_address'] = address
        update.message.reply_text(text=f'Ваша адреса: {address}', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(text=ask_spot_text, reply_markup=inline_location_kb())
    else:
        update.message.reply_text(text=no_location_text)
        from_address(update, context)


def from_address(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    context.user_data['state'] = FROM_ADDRESS
    if not context.user_data.get('location_button'):
        reply_markup = markup_keyboard(share_location)
        query.edit_message_text(text=info_address_text)
        context.bot.send_message(chat_id=chat_id,
                                 text=from_address_text,
                                 reply_markup=reply_markup)
    else:
        query.edit_message_text(text=from_address_text)


def to_the_address(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    if context.user_data['state'] == FROM_ADDRESS:
        buttons = [[InlineKeyboardButton(f'{NOT_CORRECT_ADDRESS}', callback_data='From_address 0')], ]
        address = update.message.text
        addresses = buttons_addresses(address)
        if addresses is not None:
            for no, key in enumerate(addresses.keys(), 1):
                buttons.append([InlineKeyboardButton(key, callback_data=f'From_address {no}')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.user_data['addresses_first'] = addresses
            context.bot.send_message(chat_id=chat_id, text=choose_address_text, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text=wrong_address_request)
            from_address(update, context)
    else:
        query.edit_message_text(text=arrival_text)
        context.user_data['state'] = TO_THE_ADDRESS


def payment_method(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    if context.user_data['state'] == TO_THE_ADDRESS:
        address = update.message.text
        buttons = [[InlineKeyboardButton(f'{NOT_CORRECT_ADDRESS}', callback_data='To_the_address 0')], ]
        addresses = buttons_addresses(address)
        if addresses is not None:
            for no, key in enumerate(addresses.keys(), 1):
                buttons.append([InlineKeyboardButton(key, callback_data=f'To_the_address {no}')])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.user_data['addresses_second'] = addresses
            context.bot.send_message(chat_id=chat_id, text=choose_address_text, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text=wrong_address_request)
            to_the_address(update, context)
    else:
        context.user_data['state'] = None
        context.user_data['client_msg'] = query.message.message_id
        query.edit_message_text(payment_text)
        query.edit_message_reply_markup(reply_markup=inline_payment_kb())


def second_address_check(update, context):
    query = update.callback_query
    data = int(query.data.split(' ')[1])
    response = query.message.reply_markup.inline_keyboard[data][0].text
    if data:
        context.user_data['to_the_address'] = response
        context.user_data['state'] = None
        payment_method(update, context)
    else:
        to_the_address(update, context)


def first_address_check(update, context):
    query = update.callback_query
    data = int(query.data.split(' ')[1])
    response = query.message.reply_markup.inline_keyboard[data][0].text
    if data:
        context.user_data['from_address'] = response
        context.user_data['state'] = None
        to_the_address(update, context)
    else:
        from_address(update, context)


def order_create(update, context):
    query = update.callback_query
    payment = query.data.split('_')[0]
    user = User.get_by_chat_id(update.effective_chat.id)
    context.user_data['phone_number'] = user.phone_number
    destination_place = context.user_data['addresses_second'].get(context.user_data['to_the_address'])
    destination_lat, destination_long = geocode(destination_place, ParkSettings.get_value('GOOGLE_API_KEY'))
    if not context.user_data.get('from_address'):
        context.user_data['from_address'] = context.user_data['location_address']
    else:
        from_place = context.user_data['addresses_first'].get(context.user_data['from_address'])
        context.user_data['latitude'], context.user_data['longitude'] = geocode(from_place,
                                                                                ParkSettings.get_value(
                                                                                    'GOOGLE_API_KEY'))
    distance_price = get_route_price(context.user_data['latitude'], context.user_data['longitude'],
                                     destination_lat, destination_long,
                                     ParkSettings.get_value('GOOGLE_API_KEY'))
    price = distance_price[0]
    distance_google = round(distance_price[1], 2)
    order = Order.objects.filter(chat_id_client=user.chat_id, payment_method="",
                                 status_order=Order.ON_TIME).last()
    if order:
        order.from_address = context.user_data['from_address']
        order.latitude = context.user_data['latitude']
        order.longitude = context.user_data['longitude']
        order.to_the_address = context.user_data['to_the_address']
        order.to_latitude = destination_lat
        order.to_longitude = destination_long
        order.phone_number = user.phone_number
        order.client_message_id = context.user_data['client_msg']
        order.payment_method = payment
        order.sum = price
        order.distance_google = distance_google
        order.save()
        update.message.reply_text(
            f'Замовлення прийняте, сума замовлення {price} грн\n '
            f'Очікуйте водія о {timezone.localtime(order.order_time).time()}')
    else:
        Order.objects.create(
            from_address=context.user_data['from_address'],
            latitude=context.user_data['latitude'],
            longitude=context.user_data['longitude'],
            to_the_address=context.user_data['to_the_address'],
            to_latitude=destination_lat,
            to_longitude=destination_long,
            phone_number=user.phone_number,
            client_message_id=context.user_data['client_msg'],
            chat_id_client=user.chat_id,
            payment_method=payment,
            sum=price,
            distance_google=distance_google,
            status_order=Order.WAITING)


@task_postrun.connect
def send_order_to_driver(sender=None, **kwargs):
    if sender == check_order:
        order = Order.objects.get(id=kwargs.get('retval'))
        try:
            bot.delete_message(chat_id=order.chat_id_client, message_id=order.client_message_id)
        except:
            pass
        client_msg = client_order_info(order.from_address, order.to_the_address,
                                       order.payment_method, order.phone_number, order.sum,
                                       increase=order.car_delivery_price)
        count = 0
        order.checked = True
        order.save()
        while count < 3:
            if not count:
                text_to_client(order, client_msg)
            elif count == 1:
                text_to_client(order, search_driver_1)
            elif count == 2:
                text_to_client(order, search_driver_2)
            drivers = Driver.objects.filter(chat_id__isnull=False)
            for driver in drivers:
                record = UseOfCars.objects.filter(user_vehicle=driver,
                                                  created_at__date=timezone.now().date(),
                                                  end_at=None).last()
                if record:
                    if driver.driver_status == Driver.ACTIVE:
                        vehicle = Vehicle.objects.get(licence_plate=record.licence_plate)
                        driver_lat, driver_long = get_location_from_db(vehicle)
                        distance = haversine(float(driver_lat), float(driver_long),
                                             float(order.latitude), float(order.longitude))
                        radius = round(ParkSettings.get_value("FREE RADIUS", 3), 1) + \
                                 round(order.car_delivery_price/10, 1)
                        if distance <= radius:
                            message = order_info(order.pk, order.from_address, order.to_the_address,
                                                 order.payment_method, order.phone_number)
                            markup = inline_markup_accept(order.pk)
                            accept_message = bot.send_message(chat_id=driver.chat_id, text=message, reply_markup=markup)
                            time.sleep(ParkSettings.get_value("MESSAGE_APPEAR", 30))
                            upd_driver = Driver.objects.get(id=driver.id)
                            instance = Order.objects.get(id=order.id)
                            if instance.driver == upd_driver:
                                return
                            else:
                                bot.delete_message(chat_id=driver.chat_id, message_id=accept_message.message_id)
                                bot.send_message(chat_id=driver.chat_id, text=decline_order)
                    else:
                        continue
            time.sleep(20)
            count += 1
            if count == 3:
                bot.send_message(chat_id=order.chat_id_client,
                                 text=no_driver_in_radius,
                                 reply_markup=inline_search_kb())


def increase_search_radius(update, context):
    query = update.callback_query
    query.edit_message_text(text=increase_radius_text)
    query.edit_message_reply_markup(reply_markup=inline_increase_price_kb())


def increase_order_price(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    order = Order.objects.filter(chat_id_client=chat_id, status_order=Order.WAITING).last()
    order.car_delivery_price += int(query.data)
    order.sum += int(query.data)
    order.checked = False
    order.save()


def continue_search(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    order = Order.objects.filter(chat_id_client=chat_id, status_order=Order.WAITING).last()
    order.checked = False
    order.save()


def time_order(update, context):
    query = update.callback_query
    if not context.user_data.get('to_the_address'):
        context.user_data['time_order'] = query.data
    context.user_data['state'] = TIME_ORDER
    query.edit_message_text(text=ask_time_text)


def order_on_time(update, context):
    context.user_data['state'] = None
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    user_time = update.message.text
    user = User.get_by_chat_id(update.message.chat.id)
    if re.match(pattern, user_time):
        format_time = timezone.datetime.strptime(user_time, '%H:%M').time()
        min_time = timezone.localtime().replace(tzinfo=None) + datetime.timedelta(minutes=int(
            ParkSettings.get_value('SEND_TIME_ORDER_MIN', 15)))
        conv_time = timezone.datetime.combine(timezone.localtime(), format_time)
        if min_time <= conv_time:
            if context.user_data.get('time_order') is not None:
                Order.objects.create(chat_id_client=update.message.chat.id,
                                     status_order=Order.ON_TIME,
                                     phone_number=user.phone_number,
                                     order_time=conv_time)
                from_address(update, context)
            else:
                order = Order.get_order(chat_id_client=user.chat_id,
                                        phone=context.user_data['phone_number'],
                                        status_order=Order.WAITING)
                order.status_order = Order.ON_TIME
                order.order_time = conv_time
                order.checked = False
                order.save()
                update.message.reply_text(order_complete)
        else:
            update.message.reply_text(small_time_delta)
            context.user_data['state'] = TIME_ORDER
    else:
        update.message.reply_text(wrong_time_format)
        context.user_data['state'] = TIME_ORDER


@task_postrun.connect
def send_time_orders(sender=None, **kwargs):
    if sender == check_time_order:
        timeorder = Order.objects.get(id=kwargs.get('retval'))
        message = order_info(timeorder.pk, timeorder.from_address, timeorder.to_the_address,
                             timeorder.payment_method, timeorder.phone_number,
                             time=timezone.localtime(timeorder.order_time).time())
        group_msg = bot.send_message(chat_id=-863882769, text=message,
                                     reply_markup=inline_markup_accept(timeorder.pk),
                                     parse_mode=ParseMode.HTML)
        timeorder.driver_message_id = group_msg.message_id
        timeorder.checked = True
        timeorder.save()


@task_postrun.connect
def delete_button_client(sender=None, **kwargs):
    if sender == delete_button:
        order_id, message_id, text = kwargs.get("retval")
        time.sleep(120)
        order = Order.objects.filter(pk=order_id).first()
        try:
            bot.edit_message_text(
                chat_id=order.chat_id_client,
                message_id=message_id,
                text=text,
                reply_markup=None
            )
        except Exception:
            return


def handle_callback_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    driver = Driver.get_by_chat_id(chat_id=query.from_user.id)
    order = Order.objects.filter(pk=int(data[1])).first()
    if data[0] in ("Accept_order", "Start_route"):
        if data[0] == "Start_route":
            order.status_order = Order.IN_PROGRESS
            order.save()
        record = UseOfCars.objects.filter(user_vehicle=driver,
                                          created_at__date=timezone.now().date(),
                                          end_at=None).last()
        if record:
            vehicle = Vehicle.objects.get(licence_plate=record.licence_plate)
            markup = inline_spot_keyboard(order.latitude, order.longitude, pk=order.id)
            order.driver = driver
            order.save()
            if order.status_order == Order.ON_TIME:
                context.bot.delete_message(chat_id=-863882769, message_id=int(order.driver_message_id))
                context.bot.send_message(chat_id=driver.chat_id, text=time_order_accepted)
            else:
                order.status_order, order.driver_message_id = Order.IN_PROGRESS, query.message.message_id
                order.save()
                ParkStatus.objects.create(driver=driver,
                                          status=Driver.WAIT_FOR_CLIENT)
                message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                                     order.phone_number, order.sum, order.distance_google)
                query.edit_message_text(text=message)
                query.edit_message_reply_markup(reply_markup=markup)
                report_for_client = client_order_text(driver, vehicle.name, record.licence_plate, driver.phone_number, order.sum)
                try:
                    context.user_data['running'] = True
                    r = threading.Thread(target=send_map_to_client,
                                         args=(update, context, order, query.message.message_id, vehicle), daemon=True)
                    r.start()
                except:
                    pass
                text_to_client(order, report_for_client, button=inline_reject_order(order.pk))
        else:
            context.bot.send_message(chat_id=driver.chat_id, text=select_car_error)
    elif data[0] == 'Reject_order':
        query.edit_message_text(text=f"Ви <<Відмовились від замовлення>>")
        if order:
            order.status_order = Order.WAITING
            order.driver = None
            order.checked = False
            order.save()
            # remove inline keyboard markup from the message
            text_to_client(order, driver_cancel)
        else:
            query.edit_message_text(text="Це замовлення вже виконано.")

    elif data[0] == "Client_reject":
        order.status_order = Order.CANCELED
        order.save()
        try:
            for i in range(3):
                context.bot.delete_message(chat_id=order.chat_id_client, message_id=int(order.client_message_id) + i)
            context.bot.send_message(chat_id=order.chat_id_client, text=client_cancel)
        except:
            pass
    elif data[0] == "Client_on_site":
        if not context.user_data.get('recheck'):
            context.user_data['running'] = False
            ParkStatus.objects.create(driver=driver, status=Driver.WITH_CLIENT)
        message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                             order.phone_number, order.sum, order.distance_google)
        query.edit_message_text(text=message)
        reply_markup = inline_finish_order(order.to_latitude, order.to_longitude, pk=order.id)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "End_trip":
        reply_markup = inline_route_keyboard(order.id)
        query.edit_message_text(text=route_trip_text)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] in ("Along_the_route", "Off_route"):
        context.user_data['recheck'] = data[0]
        message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                             order.phone_number, order.sum, order.distance_google)
        query.edit_message_text(text=message)
        query.edit_message_reply_markup(reply_markup=inline_repeat_keyboard(order.id))
    elif data[0] == "Accept":
        ParkStatus.objects.create(driver=order.driver, status=Driver.ACTIVE)
        if context.user_data['recheck'] == "Off_route":
            query.edit_message_text(text=calc_price_text)
            record = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=timezone.now().date())
            licence_plate = (list(record))[-1].licence_plate
            status_driver = ParkStatus.objects.filter(driver=driver, status=Driver.WITH_CLIENT).first()
            s, e = timezone.localtime(status_driver.created_at), timezone.localtime(timezone.localtime())
            get_distance_trip.delay(data[1], query.message.message_id, s, e, licence_plate)
        else:
            message = driver_complete_text(order.sum)
            query.edit_message_text(text=message)
            text_to_client(order, complete_order_text, comment=True)


        # if order.payment_method == PAYCARD:
        #     payment_id = str(uuid4())
        #     payment_request(update, context, order.chat_id_client, os.environ["LIQ_PAY_TOKEN"],
        #                     os.environ["BOT_URL_IMAGE_TAXI"], payment_id, 1)
        #     liqpay_cert_path = os.environ["LIQPAY_CERF"]
        #     liqpay_client = LiqPay(os.environ["LIQPAY_PUBLIC_KEY"], os.environ["LIQPAY_PRIVATE_KEY"],
        #                            ssl_cert=liqpay_cert_path)
        #
        #     response = liqpay_client.api("request",
        #                                  data={
        #                                      "action": "status",
        #                                      "version": "3",
        #                                      "order_id": payment_id
        #                                  },
        #                                  headers={
        #                                      "Content-Type": "application/json",
        #                                      "Accept": "application/json",
        #                                  },
        #                                  cert=liqpay_cert_path,
        #                                  verify=True
        #                                  )
        #
        #     check_payment_status_tg.delay(data[1], query.message.message_id, response)
        # else:
        context.user_data.clear()
        order.status_order = Order.COMPLETED
        order.save()


def payment_request(update, context, chat_id_client, provider_token, url, start_parameter, price: int):
    title = 'Послуга особистого водія'
    description = 'Ninja Taxi - це надійний та професійний провайдер послуг таксі'
    payload = 'Додаткові дані для ідентифікації користувача'
    currency = 'UAH'
    prices = [LabeledPrice(label='Ціна', amount=int(price) * 100)]
    need_shipping_address = False

    # Sending a request for payment
    context.bot.send_invoice(chat_id=chat_id_client, title=title, description=description, payload=payload,
                             provider_token=provider_token, currency=currency, start_parameter=start_parameter,
                             prices=prices, photo_url=url, need_shipping_address=need_shipping_address,
                             photo_width=615, photo_height=512, photo_size=50000, is_flexible=False)


'''@task_postrun.connect
def check_payment_status(sender=None, **kwargs):
    if sender == check_payment_status_tg:
        rep = kwargs.get("retval")
        query_id, order_id, status_payment = rep
        if status_payment:
            order = Order.objects.filter(pk=order_id).first()
            bot.edit_message_text(chat_id=order.driver.chat_id, message_id=query_id, text=f"<<Поїздка оплачена>>")
            bot.send_message(chat_id=order.chat_id_client,
                             text='Оплата успішна. Дякуємо, що скористались послугами нашої компанії')
            order.status_order = Order.COMPLETED
            order.save()
            ParkStatus.objects.create(driver=order.driver, status=Driver.ACTIVE)'''


@task_postrun.connect
def notify_driver(sender=None, **kwargs):
    if sender == send_time_order:
        accepted_orders = Order.objects.filter(status_order=Order.ON_TIME, driver__isnull=False)
        for order in accepted_orders:
            if timezone.localtime() < order.order_time + datetime.timedelta(minutes=int(
                    ParkSettings.get_value('SEND_TIME_ORDER_MIN', 10))):
                markup = inline_time_order_kb(order.id)
                text = order_info(order.pk, order.from_address, order.to_the_address,
                                  order.payment_method, order.phone_number,
                                  time=timezone.localtime(order.order_time).time())
                bot.send_message(chat_id=order.driver.chat_id, text=text,
                                 reply_markup=markup, parse_mode=ParseMode.HTML)


@task_postrun.connect
def change_sum_trip(sender=None, **kwargs):
    if sender == get_distance_trip:
        rep = kwargs.get("retval")
        order_id, query_id, minutes_of_trip, distance = rep
        order = Order.objects.filter(pk=order_id).first()
        order.distance_gps = distance
        price_per_minute = (AVERAGE_DISTANCE_PER_HOUR * COST_PER_KM) / 60
        price_per_minute = price_per_minute * minutes_of_trip
        price_per_distance = round(COST_PER_KM * distance)
        if price_per_distance > price_per_minute:
            order.sum = int(price_per_distance) + int(order.car_delivery_price)
        else:
            order.sum = int(price_per_minute) + int(order.car_delivery_price)
        order.save()
        text_to_client(order=order, text=f'Сума до cплати: {order.sum} грн\n {complete_order_text}')
        message = driver_complete_text(order.sum)
        bot.edit_message_text(chat_id=order.driver.chat_id, message_id=query_id, text=message)


def send_map_to_client(update, context, order, query_id, licence_plate):
    # client_chat_id, car_gps_imei = context.args[0], context.args[1]
    if order.chat_id_client:
        lat, long = get_location_from_db(licence_plate)
        context.bot.send_message(chat_id=order.chat_id_client, text=order_customer_text)
        m = context.bot.sendLocation(order.chat_id_client, latitude=lat, longitude=long, live_period=600)
    context.user_data['flag'] = True
    while True:
        if context.user_data.get('running'):
            latitude, longitude = get_location_from_db(licence_plate)
            distance = haversine(float(latitude), float(longitude), float(order.latitude), float(order.longitude))
            if context.user_data['flag']:
                if distance < float(ParkSettings.get_value('SEND_DISPATCH_MESSAGE', 0.3)):
                    text_to_client(order, driver_arrived)
                    bot.edit_message_reply_markup(chat_id=order.driver.chat_id,
                                                  message_id=query_id,
                                                  reply_markup=inline_client_spot(pk=order.id))
                    context.user_data['flag'] = False
            try:
                if order.status_order == Order.CANCELED:
                    context.user_data['running'] = False
                    return
                if order.chat_id_client:
                    m = context.bot.editMessageLiveLocation(m.chat_id, m.message_id, latitude=latitude,
                                                            longitude=longitude)
                time.sleep(10)
            except Exception as e:
                logger.error(msg=str(e))
                time.sleep(30)
        else:
            break


