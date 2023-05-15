import re
import datetime
import threading
import time
import os

from celery.signals import task_postrun
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from telegram import ReplyKeyboardRemove, ParseMode, KeyboardButton, LabeledPrice
from app.models import Order, User, Driver, Vehicle, UseOfCars, ParkStatus
from auto.tasks import logger, get_distance_trip, check_time_order
from auto_bot.handlers.main.handlers import cancel
from auto_bot.handlers.main.keyboards import markup_keyboard, markup_keyboard_onetime
from auto_bot.handlers.order.keyboards import location_keyboard, order_keyboard, timeorder_keyboard, \
    payment_keyboard, inline_markup_accept, inline_spot_keyboard, inline_client_spot, inline_route_keyboard, \
    inline_finish_order, inline_repeat_keyboard, share_location
from auto_bot.handlers.order.utils import buttons_addresses, text_to_client
from auto_bot.main import bot
from scripts.conversion import get_address, geocode, get_location_from_db, get_route_price, haversine
from auto_bot.handlers.order.static_text import *


def continue_order(update, context):
    order = Order.objects.filter(chat_id_client=update.message.chat.id, status_order__in=[Order.ON_TIME, Order.WAITING])
    if order:
        reply_markup = markup_keyboard([order_keyboard])
        update.message.reply_text(already_ordered, reply_markup=reply_markup)
    else:
        time_for_order(update, context)


def time_for_order(update, context):
    context.user_data['state'] = START_TIME_ORDER
    context.user_data['location_button'] = False
    reply_markup = markup_keyboard(timeorder_keyboard)
    update.message.reply_text(price_info, reply_markup=reply_markup)


def cancel_order(update, context):
    order = Order.objects.filter(chat_id_client=update.message.chat.id,
                                 status_order__in=[Order.ON_TIME, Order.WAITING]).first()
    if order:
        order.status_order = Order.CANCELED
        order.save()
    update.message.reply_text(complete_order_text, reply_markup=ReplyKeyboardRemove())
    cancel(update, context)


def location(update, context):
    context.user_data['state'] = None
    context.user_data['location_button'] = True
    m = update.message
    # geocoding lat and lon to address
    context.user_data['latitude'], context.user_data['longitude'] = m.location.latitude, m.location.longitude
    address = get_address(context.user_data['latitude'], context.user_data['longitude'],
                          ParkSettings.get_value('GOOGLE_API_KEY'))
    if address is not None:
        context.user_data['location_address'] = address
        update.message.reply_text(f'Ваша адреса: {address}')
        the_confirmation_of_location(update, context)
    else:
        update.message.reply_text('Нам не вдалось обробити ваше місце знаходження')
        from_address(update, context)


def the_confirmation_of_location(update, context):
    reply_markup = markup_keyboard([location_keyboard])
    update.message.reply_text('Оберіть статус посадки', reply_markup=reply_markup)


def from_address(update, context):
    context.user_data['state'] = FROM_ADDRESS
    if not context.user_data.get('location_button'):
        reply_markup = markup_keyboard(share_location)
    else:
        reply_markup = ReplyKeyboardRemove()
    update.message.reply_text('Введіть адресу місця посадки:', reply_markup=reply_markup)


def to_the_address(update, context):
    if context.user_data['state'] == FROM_ADDRESS:
        buttons = [[KeyboardButton(f'{NOT_CORRECT_ADDRESS}')], ]
        address = update.message.text
        addresses = buttons_addresses(address)
        if addresses is not None:
            for key in addresses.keys():
                buttons.append([KeyboardButton(key)])
            reply_markup = markup_keyboard(buttons)
            context.user_data['addresses_first'] = addresses
            update.message.reply_text(choose_address_text, reply_markup=reply_markup)
            context.user_data['state'] = FIRST_ADDRESS_CHECK
        else:
            update.message.reply_text(wrong_address_request)
            from_address(update, context)
    else:
        update.message.reply_text('Введіть адресу місця призначення:', reply_markup=ReplyKeyboardRemove())
        context.user_data['state'] = TO_THE_ADDRESS


def payment_method(update, context):
    if context.user_data['state'] == TO_THE_ADDRESS:
        address = update.message.text
        buttons = [[KeyboardButton(f'{NOT_CORRECT_ADDRESS}')], ]
        addresses = buttons_addresses(address)
        if addresses is not None:
            for key in addresses.keys():
                buttons.append([KeyboardButton(key)])
            reply_markup = markup_keyboard(buttons)
            context.user_data['addresses_second'] = addresses
            update.message.reply_text(
                choose_address_text,
                reply_markup=reply_markup)
            context.user_data['state'] = SECOND_ADDRESS_CHECK
        else:
            update.message.reply_text(wrong_address_request)
            to_the_address(update, context)
    else:
        context.user_data['state'] = None
        markup = markup_keyboard_onetime([payment_keyboard])
        update.message.reply_text('Виберіть спосіб оплати:', reply_markup=markup)


def second_address_check(update, context):
    response = update.message.text
    lst = context.user_data['addresses_second']
    if response not in lst.keys() or response == NOT_CORRECT_ADDRESS:
        to_the_address(update, context)
    else:
        context.user_data['to_the_address'] = response
        payment_method(update, context)


def first_address_check(update, context):
    response = update.message.text
    lst = context.user_data['addresses_first']
    if response not in lst.keys() or response == NOT_CORRECT_ADDRESS:
        from_address(update, context)
    else:
        context.user_data['from_address'] = response
        to_the_address(update, context)


def order_create(update, context):
    payment = update.message.text
    context.user_data['client_chat_id'] = update.message.chat.id
    user = User.get_by_chat_id(update.message.chat.id)
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
    order = Order.objects.filter(chat_id_client=update.message.chat.id, payment_method="",
                                 status_order=Order.ON_TIME).first()
    if order:
        order.from_address = context.user_data['from_address']
        order.latitude = context.user_data['latitude']
        order.longitude = context.user_data['longitude']
        order.to_the_address = context.user_data['to_the_address']
        order.to_latitude = destination_lat
        order.to_longitude = destination_long
        order.phone_number = user.phone_number
        order.payment_method = payment.split()[1]
        order.save()
        update.message.reply_text(
            f'Замовлення прийняте, очікуйте водія о {timezone.localtime(order.order_time).time()}')
    else:
        Order.objects.create(
            from_address=context.user_data['from_address'],
            latitude=context.user_data['latitude'],
            longitude=context.user_data['longitude'],
            to_the_address=context.user_data['to_the_address'],
            to_latitude=destination_lat,
            to_longitude=destination_long,
            phone_number=user.phone_number,
            chat_id_client=context.user_data['client_chat_id'],
            payment_method=payment.split()[1],
            status_order=Order.WAITING)


@receiver(post_save, sender=Order)
def send_order_to_driver(sender, instance, **kwargs):
    if instance.status_order == Order.WAITING or not instance.status_order:
        message = order_info(instance.pk, instance.from_address, instance.to_the_address,
                             instance.payment_method, instance.phone_number)

        markup = inline_markup_accept(instance.pk)
        drivers = [i.chat_id for i in Driver.objects.all() if i.driver_status == Driver.ACTIVE]
        # drivers = Driver.objects.filter(driver_status=Driver.ACTIVE).order_by('Fleets_drivers_vehicles_rate__rate')
        if drivers:
            try:
                bot.send_message(chat_id=instance.chat_id_client, text='Замовлення прийнято.Шукаємо водія')
            except:
                #     send sms
                pass
            for driver in drivers:
                try:
                    bot.send_message(chat_id=driver, text=message, reply_markup=markup)
                except:
                    pass
        else:
            bot.send_message(chat_id=instance.chat_id_client,
                             text='Вибачте, але вільних водіїв незалишилось, бажаєте замовити таксі на інший час?',
                             reply_markup=markup_keyboard([order_keyboard]))


def time_order(update, context):
    if not context.user_data.get('to_the_address'):
        answer = update.message.text
        context.user_data['time_order'] = ' '.join(answer.split()[1:])
    context.user_data['state'] = TIME_ORDER
    update.message.reply_text('Вкажіть, будь ласка, час для подачі таксі(напр. 18:45)',
                              reply_markup=ReplyKeyboardRemove())


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
            if context.user_data.get('time_order') == TODAY:
                Order.objects.create(chat_id_client=update.message.chat.id,
                                     status_order=Order.ON_TIME,
                                     phone_number=user.phone_number,
                                     order_time=conv_time)
                from_address(update, context)
            else:
                order = Order.get_order(chat_id_client=context.user_data['client_chat_id'],
                                        phone=context.user_data['phone_number'],
                                        status_order=Order.WAITING)
                order.status_order = Order.ON_TIME
                order.order_time = conv_time
                order.save()
                update.message.reply_text(order_complete)
        else:
            update.message.reply_text('Вкажіть, будь ласка, більш пізній час')
            context.user_data['state'] = TIME_ORDER
    else:
        update.message.reply_text('Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)')
        context.user_data['state'] = TIME_ORDER


@task_postrun.connect
def send_time_orders(sender=None, **kwargs):
    if sender == check_time_order:
        min_sending_time = timezone.localtime() + datetime.timedelta(
            minutes=int(ParkSettings.get_value('SEND_TIME_ORDER_MIN', 15)))
        orders = Order.objects.filter(status_order=Order.ON_TIME,
                                      order_time__gte=timezone.localtime(),
                                      order_time__lte=min_sending_time)
        if orders:
            for timeorder in orders:
                message = order_info(timeorder.pk, timeorder.from_address, timeorder.to_the_address,
                                     timeorder.payment_method, timeorder.phone_number,
                                     time=timezone.localtime(timeorder.order_time).time())
                drivers = [i.chat_id for i in Driver.objects.all() if i.driver_status == Driver.ACTIVE]
                if drivers:
                    for driver in drivers:
                        try:
                            bot.send_message(chat_id=driver, text=message,
                                             reply_markup=inline_markup_accept(timeorder.pk),
                                             parse_mode=ParseMode.HTML)
                        except:
                            pass


def handle_callback_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    driver = Driver.get_by_chat_id(chat_id=query.message.chat_id)
    order = Order.objects.filter(pk=int(data[1])).first()
    if data[0] == "Accept_order":
        if order:
            record = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=timezone.now().date(), end_at=None)
            if record:
                licence_plate = (list(record))[-1].licence_plate
                vehicle = Vehicle.objects.get(licence_plate=licence_plate)
                driver_lat, driver_long = get_location_from_db(vehicle)
                if not order.sum:
                    distance_price = get_route_price(order.latitude, order.longitude,
                                                     order.to_latitude, order.to_longitude,
                                                     driver_lat, driver_long,
                                                     ParkSettings.get_value('GOOGLE_API_KEY'))
                    order.car_delivery_price, order.sum = distance_price[1], distance_price[0],
                    order.distance_google = round(distance_price[2], 2)
                markup = inline_spot_keyboard(driver_lat, driver_long, order.latitude, order.longitude, order.pk)
                order.status_order, order.driver = Order.IN_PROGRESS, driver
                order.save()
                ParkStatus.objects.create(driver=driver,
                                          status=Driver.WAIT_FOR_CLIENT)
                message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                                     order.phone_number, order.sum, order.distance_google)
                query.edit_message_text(text=message)
                query.edit_message_reply_markup(reply_markup=markup)
                report_for_client = f'Вас вітає Ninja-Taxi!\n' \
                                    f'Ваш водій: {driver}\n' \
                                    f'Назва: {vehicle.name}\n' \
                                    f'Номер машини: {licence_plate}\n' \
                                    f'Номер телефону: {driver.phone_number}\n' \
                                    f'Сума замовлення: {order.sum}грн'
                try:
                    context.user_data['running'] = True
                    r = threading.Thread(target=send_map_to_client,
                                         args=(update, context, order, query.message.message_id, vehicle), daemon=True)
                    r.start()
                except:
                    pass
                text_to_client(context, order, report_for_client)
            else:
                query.edit_message_text(text=select_car_error)
        else:
            query.edit_message_text(text="Це замовлення вже виконується.")
    elif data[0] == 'Reject_order':
        query.edit_message_text(text=f"Ви <<Відмовились від замовлення>>")
        if order:
            order.status_order = Order.WAITING
            order.save()
            # remove inline keyboard markup from the message
            text_to_client(context, order, driver_cancel)
        else:
            query.edit_message_text(text="Це замовлення вже виконано.")
    elif data[0] == "Сlient_on_site":
        if not context.user_data.get('recheck'):
            context.user_data['running'] = False
            ParkStatus.objects.create(driver=driver, status=Driver.WITH_CLIENT)
        message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                             order.phone_number, order.sum, order.distance_google)
        query.edit_message_text(text=message)
        reply_markup = inline_route_keyboard(order.latitude, order.longitude,
                                             order.to_latitude, order.to_longitude, pk=order.id)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] in ("Along_the_route", "Off_route"):
        context.user_data['recheck'] = data[0]
        reply_markup = inline_repeat_keyboard(order.id)
        message = "Ви вже доїхали до місця призначення?"
        query.edit_message_text(text=message)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "Accept":
        ParkStatus.objects.create(driver=order.driver, status=Driver.ACTIVE)
        if context.user_data['recheck'] == "Off_route":
            message = 'Проводимо розрахунок вартості...'
            query.edit_message_text(text=message)
            record = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=timezone.now().date())
            licence_plate = (list(record))[-1].licence_plate
            status_driver = ParkStatus.objects.filter(driver=driver, status=Driver.WITH_CLIENT).first()
            s, e = timezone.localtime(status_driver.created_at), timezone.localtime(timezone.localtime())
            get_distance_trip.delay(data[1], query.message.message_id, s, e, licence_plate)
        else:
            message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                                 order.phone_number, order.sum, order.distance_google)
            query.edit_message_text(text=message)
            query.edit_message_reply_markup(reply_markup=inline_finish_order(order.id))

    elif data[0] == "End_trip":
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
        text_to_client(context, order, complete_order_text)
        query.edit_message_text(text=f"<<Поїздку завершено>>")
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
def change_sum_trip(sender=None, **kwargs):
    if sender == get_distance_trip:
        rep = kwargs.get("retval")
        order_id, query_id, minutes_of_trip, distance = rep
        order = Order.objects.filter(pk=order_id).first()
        order.distance_gps = distance
        order.save()
        price_per_minute = (AVERAGE_DISTANCE_PER_HOUR * COST_PER_KM) / 60
        price_per_minute = price_per_minute * minutes_of_trip
        price_per_distance = round(COST_PER_KM * distance)
        if price_per_distance > price_per_minute:
            order.sum = int(price_per_distance) + int(order.car_delivery_price)
        else:
            order.sum = int(price_per_minute) + int(order.car_delivery_price)
        order.save()
        if order.chat_id_client:
            bot.send_message(chat_id=order.chat_id_client,
                             text=f'Сума до оплати: {order.sum}грн')
        else:
            text_to_client(order=order, text=f'Сума до оплати: {order.sum}грн')
        message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                             order.phone_number, order.sum, order.distance_gps)

        bot.edit_message_text(chat_id=order.driver.chat_id, message_id=query_id, text=message)
        bot.edit_message_reply_markup(chat_id=order.driver.chat_id,
                                      message_id=query_id, reply_markup=inline_finish_order(order.id))


def send_map_to_client(update, context, order, query_id, licence_plate):
    # client_chat_id, car_gps_imei = context.args[0], context.args[1]
    lat, long = get_location_from_db(licence_plate)
    context.bot.send_message(chat_id=order.chat_id_client, text=order_customer_text)
    m = context.bot.sendLocation(order.chat_id_client, latitude=lat, longitude=long, live_period=600)
    context.user_data['flag'] = True
    while context.user_data['running']:
        latitude, longitude = get_location_from_db(licence_plate)
        distance = haversine(float(latitude), float(longitude), float(order.latitude), float(order.longitude))
        if context.user_data['flag']:
            if distance < float(ParkSettings.get_value('SEND_DISPATCH_MESSAGE', 0.3)):
                text_to_client(context, order, driver_arrived)
                bot.edit_message_reply_markup(chat_id=order.driver.chat_id,
                                              message_id=query_id,
                                              reply_markup=inline_client_spot(pk=order.id,
                                                                              phone_number=order.phone_number))
                context.user_data['flag'] = False
        try:
            m = context.bot.editMessageLiveLocation(m.chat_id, m.message_id, latitude=latitude, longitude=longitude)
            time.sleep(10)
        except Exception as e:
            logger.error(msg=e.message)
            time.sleep(30)