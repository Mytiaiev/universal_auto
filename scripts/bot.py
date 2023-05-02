from telegram import *
from telegram.ext import *
from app.models import *
import ast
from liqpay import LiqPay
import os
import threading
import time
import csv
import datetime
import pendulum
import sys
import redis
import re
import html
import json
import logging
import requests
import traceback
from celery.signals import task_postrun
from app.portmone.generate_link import *
from auto.tasks import download_weekly_report_force, send_on_job_application_on_driver_to_Bolt, \
    send_on_job_application_on_driver_to_Uber, get_report_for_tg, get_distance_trip
from scripts.driversrating import DriversRatingMixin
from uuid import uuid4
import traceback
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse
from django.db import IntegrityError
from django.utils import timezone
from scripts.conversion import *
from django.db.models.signals import post_save
from django.dispatch import receiver
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext")

PORT = int(os.environ.get('PORT', '8443'))
DEVELOPER_CHAT_ID = int(os.environ.get('DEVELOPER_CHAT_ID', '803129892'))

url_mobizon = os.environ['MOBIZON_DOMAIN']

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

processed_files = []

start_keyboard = [
    KeyboardButton(text="\U0001f696 Викликати Таксі"),
    KeyboardButton(text="\U0001f4e2 Залишити відгук"),
    KeyboardButton(text="\U0001F4E8 Залишити заявку на роботу"),
    KeyboardButton(text="\U0001f4f2 Надати номер телефону", request_contact=True)
]


# Ordering taxi
def start(update, context):
    chat_id = update.effective_chat.id
    menu(update, context, chat_id)
    user = User.get_by_chat_id(chat_id)
    context.user_data.clear()
    if user:
        if user.phone_number:
            update.message.reply_text('Привіт! Тебе вітає Універсальне таксі - викликай кнопкою нижче.')
            user.chat_id = chat_id
            user.save()
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[start_keyboard[:3]],
                resize_keyboard=True,
            )
            update.message.reply_text('Зробіть вибір', reply_markup=reply_markup)
        else:
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[start_keyboard[3:]],
                resize_keyboard=True, )
            update.message.reply_text("Будь ласка розшарьте номер телефону для роботи з нашим ботом",
                                      reply_markup=reply_markup)
    else:
        User.objects.create(
            chat_id=chat_id,
            name=update.message.from_user.first_name,
            second_name=update.message.from_user.last_name
        )
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[start_keyboard[3:]],
            resize_keyboard=True, )
        update.message.reply_text("Будь ласка розшарьте номер телефону для роботи з нашим ботом",
                                  reply_markup=reply_markup)


def update_phone_number(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    phone_number = update.message.contact.phone_number
    if (phone_number and user):
        if len(phone_number) == 12:
            phone_number = f'+{phone_number}'
        user.phone_number = phone_number
        user.chat_id = chat_id
        user.save()
        update.message.reply_text('Дякуємо ми отримали ваш номер телефону',
                                  reply_markup=ReplyKeyboardMarkup(keyboard=[start_keyboard[:3]], resize_keyboard=True))


STATE = None  # range (1-50)
FROM_ADDRESS, TO_THE_ADDRESS, COMMENT, TIME_ORDER, START_TIME_ORDER = range(1, 6)
U_NAME, U_SECOND_NAME, U_EMAIL, FIRST_ADDRESS_CHECK, SECOND_ADDRESS_CHECK = range(6, 11)
LOCATION_WRONG = "Місце посадки - невірне"
LOCATION_CORRECT = "Місце посадки - вірне"
NOT_CORRECT_ADDRESS = 'Немає вірної адреси'
CONTINUE = 'Продовжити замовлення'
CANCEL = 'Скасувати замовлення'
TOMORROW = "Замовити на завтра"
TODAY = "Замовити на інший час"
_CARD = 'Картка'
CASH = 'Готівка'


def continue_order(update, context):
    order = Order.objects.filter(chat_id_client=update.message.chat.id, status_order__in=[Order.ON_TIME, Order.WAITING])
    if order:
        update.message.reply_text("У вас вже є активне замовлення бажаєте замовити ще одне авто?")
    else:
        update.message.reply_text(f"Ціна поїздки в місті {ParkSettings.get_value('TARIFF_IN_THE_CITY')}грн/км\n" +
                              f"Ціна поїздки за містом {ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY')}грн/км")

    keyboard = [KeyboardButton(text=f"\u2705 {CONTINUE}"),
                KeyboardButton(text=f"\u274c {CANCEL}")]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard],
        resize_keyboard=True,
    )

    update.message.reply_text('Чи бажаєте ви продовжити?', reply_markup=reply_markup)


def time_for_order(update, context):
    global STATE
    STATE = START_TIME_ORDER
    keyboard = [KeyboardButton(text="Замовити на зараз", request_location=True),
                KeyboardButton(text=f"{TODAY}")]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard],
        resize_keyboard=True,
    )
    update.message.reply_text(f"Бажаєте замовити на зараз чи на певний час?", reply_markup=reply_markup)


def cancel_order(update, context):
    update.message.reply_text('Гарного дня. Дякуємо, що скористались нашими послугами',
                              reply_markup=ReplyKeyboardRemove())
    cancel(update, context)


def location(update: Update, context: CallbackContext):
    global STATE
    STATE = None
    m = update.message
    # geocoding lat and lon to address
    context.user_data['latitude'], context.user_data['longitude'] = m.location.latitude, m.location.longitude
    address = get_address(context.user_data['latitude'], context.user_data['longitude'], os.environ["GOOGLE_API_KEY"])
    if address is not None:
        context.user_data['location_address'] = address
        update.message.reply_text(f'Ваша адреса: {address}')
        the_confirmation_of_location(update, context)
    else:
        update.message.reply_text('Нам не вдалось обробити ваше місце знаходження')
        from_address(update, context)


def the_confirmation_of_location(update, context):
    keyboard = [KeyboardButton(text=f"\u2705 {LOCATION_CORRECT}"),
                KeyboardButton(text=f"\u274c {LOCATION_WRONG}")]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard],
        resize_keyboard=True, )

    update.message.reply_text('Оберіть статус посадки', reply_markup=reply_markup)


def from_address(update, context):
    global STATE
    STATE = FROM_ADDRESS
    update.message.reply_text('Введіть адресу місця посадки:', reply_markup=ReplyKeyboardRemove())


def to_the_address(update, context):
    global STATE
    if STATE == FROM_ADDRESS:
        buttons = [[KeyboardButton(f'{NOT_CORRECT_ADDRESS}')], ]
        address = update.message.text
        addresses = buttons_addresses(update, context, address=address)
        if addresses is not None:
            for key in addresses.keys():
                buttons.append([KeyboardButton(key)])
            reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            context.user_data['addresses_first'] = addresses
            update.message.reply_text(
                f"Оберіть вашу адресу. Інакше натисніть - 'Немає вірної адреси' та вкажіть більш детально вашу адресу",
                reply_markup=reply_markup)
            STATE = FIRST_ADDRESS_CHECK
        else:
            update.message.reply_text('Нам не вдалось обробити вашу адресу, спробуйте ще раз')
            from_address(update, context)
    else:
        update.message.reply_text('Введіть адресу місця призначення:', reply_markup=ReplyKeyboardRemove())
        STATE = TO_THE_ADDRESS


def payment_method(update, context):
    global STATE
    if STATE == TO_THE_ADDRESS:
        address = update.message.text
        buttons = [[KeyboardButton(f'{NOT_CORRECT_ADDRESS}')], ]
        addresses = buttons_addresses(update, context, address=address)
        if addresses is not None:
            for key in addresses.keys():
                buttons.append([KeyboardButton(key)])
            reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

            context.user_data['addresses_second'] = addresses
            update.message.reply_text(
                f"Оберіть вашу адресу. Інакше натисніть - 'Немає вірної адреси' та вкажіть більш детально вашу адресу",
                reply_markup=reply_markup)
            STATE = SECOND_ADDRESS_CHECK
        else:
            update.message.reply_text('Нам не вдалось обробити вашу адресу, спробуйте ще раз')
            to_the_address(update, context)
    else:
        STATE = None

        keyboard = [KeyboardButton(text=f"\U0001f4b7 {CASH}"),]
                    #KeyboardButton(text=f"\U0001f4b8 {_CARD}")

        reply_markup = ReplyKeyboardMarkup(
            keyboard=[keyboard],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

        update.message.reply_text('Виберіть спосіб оплати:', reply_markup=reply_markup)


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


def buttons_addresses(update, context, address):
    center_lat, center_lng = f"{ParkSettings.get_value('CENTRE_CITY_LAT')}", f"{ParkSettings.get_value('CENTRE_CITY_LNG')}"
    center_radius = int(f"{ParkSettings.get_value('CENTRE_CITY_RADIUS')}")
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng, center_radius,
                                             os.environ["GOOGLE_API_KEY"])
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def order_create(update, context):
    payment = update.message.text
    user = User.get_by_chat_id(update.message.chat.id)
    context.user_data['phone_number'] = user.phone_number
    destination_place = context.user_data['addresses_second'].get(context.user_data['to_the_address'])
    destination_lat, destination_long = geocode(destination_place, os.environ["GOOGLE_API_KEY"])
    if not context.user_data.get('from_address'):
        context.user_data['from_address'] = context.user_data['location_address']
    else:
        from_place = context.user_data['addresses_first'].get(context.user_data['from_address'])
        context.user_data['latitude'], context.user_data['longitude'] = geocode(from_place, os.environ["GOOGLE_API_KEY"])
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
        update.message.reply_text(f'Замовлення прийняте, очікуйте водія о {timezone.localtime(order.order_time).time()}')
    else:
        Order.objects.create(
            from_address=context.user_data['from_address'],
            latitude=context.user_data['latitude'],
            longitude=context.user_data['longitude'],
            to_the_address=context.user_data['to_the_address'],
            to_latitude=destination_lat,
            to_longitude=destination_long,
            phone_number=user.phone_number,
            chat_id_client=update.message.chat.id,
            payment_method=payment.split()[1],
            status_order=Order.WAITING)


@receiver(post_save, sender=Order)
def send_order_to_driver(sender, instance, **kwargs):
    if instance.status_order == Order.WAITING or not instance.status_order:
        try:
            bot.send_message(chat_id=instance.chat_id_client, text='Шукаємо водія')
        except:
            #     send sms
            pass
        drivers = [i.chat_id for i in Driver.objects.all() if i.driver_status == Driver.ACTIVE]
        # drivers = Driver.objects.filter(driver_status=Driver.ACTIVE)
        message = f"Отримано нове замовлення:\n" \
                  f"Адреса посадки: {instance.from_address}\n" \
                  f"Місце прибуття: {instance.to_the_address}\n" \
                  f"Спосіб оплати: {instance.payment_method}\n" \
                  f"Номер телефону: {instance.phone_number}\n"
        keyboard = [
            [InlineKeyboardButton("\u2705 Прийняти замовлення", callback_data=f"Accept_order {instance.pk}")],
            [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {instance.pk}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if drivers:
            for driver in drivers:
                try:
                    bot.send_message(chat_id=driver, text=message, reply_markup=reply_markup)
                except:
                    pass


def time_order(update, context):
    global STATE
    if STATE == START_TIME_ORDER:
        answer = update.message.text
        context.user_data['time_order'] = answer
    STATE = TIME_ORDER
    update.message.reply_text('Вкажіть, будь ласка, час для подачі таксі(напр. 18:45)',
                              reply_markup=ReplyKeyboardRemove())


def order_on_time(update, context):
    global STATE
    STATE = None
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    user_time = update.message.text
    user = User.get_by_chat_id(update.message.chat.id)
    if re.match(pattern, user_time):
        format_time = datetime.datetime.strptime(user_time, '%H:%M').time()
        min_time = timezone.localtime().replace(tzinfo=None) + datetime.timedelta(
            minutes=int(ParkSettings.get_value('SEND_TIME_ORDER_MIN', 15)))
        conv_time = timezone.datetime.combine(timezone.localtime(), format_time)
        if min_time <= conv_time:
            if context.user_data['time_order'] == TODAY:
                Order.objects.create(chat_id_client=update.message.chat.id,
                                     status_order=Order.ON_TIME,
                                     phone_number=user.phone_number,
                                     order_time=conv_time)
                from_address(update, context)
            else:
                order = Order.get_order(chat_id_client=context.user_data['client_chat_id'],
                                        phone=context.user_data['phone_number'],
                                        status_order=Order.WAITING)
                order.status = Order.ON_TIME
                order.order_time = conv_time
                order.save()
        else:
            update.message.reply_text('Вкажіть, будь ласка, більш пізній час')
            STATE = TIME_ORDER
    else:
        update.message.reply_text('Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)')
        STATE = TIME_ORDER


def send_time_orders(context):
    min_sending_time = timezone.localtime() + datetime.timedelta(
        minutes=int(ParkSettings.get_value('SEND_TIME_ORDER_MIN', 15)))
    orders = Order.objects.filter(status_order=Order.ON_TIME,
                                  order_time__gte=timezone.localtime(),
                                  order_time__lte=min_sending_time)
    if orders:
        for timeorder in orders:
            message = f"<u>Замовлення на певний час:</u>\n" \
            f"<b>Час подачі:{timezone.localtime(timeorder.order_time).time()}</b>\n" \
            f"Адреса посадки: {timeorder.from_address}\n" \
            f"Місце прибуття: {timeorder.to_the_address}\n" \
            f"Спосіб оплати: {timeorder.payment_method}\n" \
            f"Номер телефону: {timeorder.phone_number}\n"
            drivers = [i.chat_id for i in Driver.objects.all() if i.driver_status == Driver.ACTIVE]
            if drivers:
                keyboard = [
                    [InlineKeyboardButton("\u2705 Прийняти замовлення", callback_data=f"Accept_order {timeorder.pk}")],
                    [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {timeorder.pk}")],
                ]
                for driver in drivers:
                    try:
                        context.bot.send_message(chat_id=driver, text=message,
                                 reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
                    except:
                        pass


def handle_callback_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    driver = Driver.get_by_chat_id(chat_id=query.message.chat_id)
    order = Order.objects.filter(pk=int(data[1])).first()
    phone = order.phone_number.replace("+", "")
    if phone.startswith("0"):
        phone = "38" + phone
    if data[0] == "Accept_order":
        if order:
            record = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=timezone.now().date())
            if record:
                licence_plate = (list(record))[-1].licence_plate
                vehicle = Vehicle.objects.get(licence_plate=licence_plate)
                driver_lat, driver_long = get_location_from_db(vehicle)
                if not order.sum:
                    distance_price = get_route_price(order.latitude, order.longitude,
                                                     order.to_latitude, order.to_longitude,
                                                     driver_lat, driver_long,
                                                     os.environ["GOOGLE_API_KEY"])
                    order.car_delivery_price, order.sum = distance_price[1], distance_price[0]

                keyboard = [
                    [InlineKeyboardButton("\u2705 Машина вже на місці", callback_data=f"On_the_spot {order.pk}")],
                    [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {order.pk}")],
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                order.status_order, order.driver = Order.IN_PROGRESS, driver
                order.save()
                ParkStatus.objects.create(driver=driver, status=Driver.WAIT_FOR_CLIENT)

                message = f"Адреса посадки: {order.from_address}\n" \
                          f"Місце прибуття: {order.to_the_address}\n" \
                          f"Спосіб оплати: {order.payment_method}\n" \
                          f"Номер телефону: {order.phone_number}\n" \
                          f"Загальна вартість: {order.sum}грн"
                query.edit_message_text(text=message)
                query.edit_message_reply_markup(reply_markup=reply_markup)

                report_for_client = f'Ваш водій: {driver}\n' \
                                    f'Назва: {vehicle.name}\n' \
                                    f'Номер машини: {licence_plate}\n' \
                                    f'Номер телефону: {driver.phone_number}\n' \
                                    f'Сума замовлення:{order.sum}грн'
                if order.chat_id_client:
                    try:
                        context.bot.send_message(chat_id=order.chat_id_client, text=report_for_client)
                        context.user_data['running'] = True
                        #r = threading.Thread(target=send_map_to_client,
                        #                     args=(update, context, order.chat_id_client, vehicle), daemon=True)
                        #r.start()
                    except:
                        pass
                else:
                    sms_for_client = f'Вас вітає Ninja-Taxi!\n' \
                                     f'Ваш водій: {driver}\n' \
                                     f'Назва: {vehicle.name}\n' \
                                     f'Номер машини: {licence_plate}\n' \
                                     f'Номер телефону: {driver.phone_number}\n'
                    params = {
                        "recipient": phone,
                        "text": sms_for_client,
                        "apiKey": os.environ['MOBIZON_API_KEY'],
                        "output": "json"
                    }
                    requests.post(url_mobizon, params=params)

            else:
                query.edit_message_text(
                    text='Щоб приймати замовлення, скористайтесь спочатку командой /status, щоб позначити на якому ви сьогодні авто')
        else:
            query.edit_message_text(text="Це замовлення вже виконується.")
    elif data[0] == 'Reject_order':
        query.edit_message_text(text=f"Ви <<Відмовились від замовлення>>")
        if order:
            order.status_order = Order.WAITING
            order.save()
            # remove inline keyboard markup from the message
            if order.chat_id_client:
                context.bot.send_message(chat_id=order.chat_id_client,
                                         text="Водій відхилив замовлення. Пошук іншого водія...")
            else:
                params = {
                    "recipient": phone,
                    "text": "Водій відхилив замовлення. Пошук іншого водія...",
                    "apiKey": os.environ['MOBIZON_API_KEY'],
                    "output": "json"
                }
                requests.post(url_mobizon, params=params)
        else:
            query.edit_message_text(text="Це замовлення вже виконано.")
    elif data[0] == "On_the_spot":
        keyboard = [[InlineKeyboardButton("\u2705 Клієнт на місці", callback_data=f"Сlient_on_site {order.pk}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_reply_markup(reply_markup=reply_markup)
        if order.chat_id_client:
            context.bot.send_message(chat_id=order.chat_id_client, text='Машину подано. Водій вас очікує')
        else:
            params = {
                "recipient": phone,
                "text": "'Машину подано. Водій вас очікує'.",
                "apiKey": os.environ['MOBIZON_API_KEY'],
                "output": "json"
            }
            requests.post(url_mobizon, params=params)
    elif data[0] == "Сlient_on_site":
        keyboard = [
            [InlineKeyboardButton("\u2705 Рухались по маршруту", callback_data=f"Along_the_route {order.pk}")],
            [InlineKeyboardButton("\u274c Відхилялись від маршрута", callback_data=f"Off_route {order.pk}")],
        ]

        ParkStatus.objects.create(driver=driver, status=Driver.WITH_CLIENT)
        reply_markup, context.user_data['running'] = InlineKeyboardMarkup(keyboard), False
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "Along_the_route" or data[0] == "Off_route":
        if data[0] == "Off_route":
            record = UseOfCars.objects.filter(user_vehicle=driver, created_at__date=timezone.now().date())
            licence_plate = (list(record))[-1].licence_plate
            status_driver = ParkStatus.objects.filter(driver=driver, status=Driver.WITH_CLIENT).first()
            s, e = timezone.localtime(status_driver.created_at), timezone.localtime(timezone.localtime())
            get_distance_trip.delay(data[1], query.message.message_id, s, e, licence_plate)
        else:
            keyboard = [[
                InlineKeyboardButton("Завершити поїздку", callback_data=f"End_trip {order.pk}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "End_trip":
        # if order.payment_method == _CARD:
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
        #else:
        if order.chat_id_client:
            context.bot.send_message(chat_id=order.chat_id_client,
                                     text="Дякуємо, що скористались послугами нашої компанії")
        else:
            params = {
                "recipient": phone,
                "text": "Дякуємо, що скористались послугами нашої компанії",
                "apiKey": os.environ['MOBIZON_API_KEY'],
                "output": "json"
            }
            requests.post(url_mobizon, params=params)
        query.edit_message_text(text=f"<<Поїздку завершено>>")
        order.status_order = Order.COMPLETED
        order.save()
        ParkStatus.objects.create(driver=order.driver, status=Driver.ACTIVE)


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


@task_postrun.connect
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
            ParkStatus.objects.create(driver=order.driver, status=Driver.ACTIVE)


@task_postrun.connect
def change_sum_trip(sender=None, **kwargs):
    if sender == get_distance_trip:
        rep = kwargs.get("retval")
        order_id, query_id, minutes_of_trip, distance = rep
        order = Order.objects.filter(pk=order_id).first()
        AVERAGE_DISTANCE_PER_HOUR, COST_PER_KM = int(f"{ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR')}"), int(
            f"{ParkSettings.get_value('COST_PER_KM')}")
        price_per_minute = (AVERAGE_DISTANCE_PER_HOUR * COST_PER_KM) / 60
        price_per_minute = price_per_minute * minutes_of_trip
        price_per_distance = round(COST_PER_KM * distance)
        if price_per_distance > price_per_minute:
            order.sum = int(price_per_distance) + int(order.car_delivery_price)
        else:
            order.sum = int(price_per_minute) + int(order.car_delivery_price)
        order.save()
        bot.send_message(chat_id=order.chat_id_client,
                         text=f'Сума до оплати: {order.sum}грн')

        message = f"Адреса посадки: {order.from_address}\n" \
                  f"Місце прибуття: {order.to_the_address}\n" \
                  f"Спосіб оплати: {order.payment_method}\n" \
                  f"Номер телефону: {order.phone_number}\n" \
                  f"Загальна вартість: {order.sum}грн"

        keyboard = [[
            InlineKeyboardButton("Завершити поїздку", callback_data=f"End_trip {order.pk}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=order.driver.chat_id, message_id=query_id, text=message)
        bot.edit_message_reply_markup(chat_id=order.driver.chat_id, message_id=query_id, reply_markup=reply_markup)


def send_map_to_client(update, context, client_chat_id, licence_plate):
    # client_chat_id, car_gps_imei = context.args[0], context.args[1]
    latitude, longitude = get_location_from_db(licence_plate)

    # send map client
    report = 'Коли водій буде на місці, ви отримаєте повідомлення. На карті нижче ви можете спостерігати, де зараз ваш водій'
    context.bot.send_message(chat_id=client_chat_id, text=report)
    m = context.bot.sendLocation(client_chat_id, latitude=latitude, longitude=longitude, live_period=600)

    while context.user_data['running']:
        latitude, longitude = get_location_from_db(licence_plate)
        try:
            m = context.bot.editMessageLiveLocation(m.chat_id, m.message_id, latitude=latitude, longitude=longitude)
            time.sleep(10)
        except Exception as e:
            logger.error(msg=e.message)
            time.sleep(30)


# Changing status of driver
def status(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        record = UseOfCars.objects.filter(user_vehicle=driver,
                                          created_at__date=timezone.now().date(),
                                          end_at=None)
        if record:
            send_set_status(update, context)
        else:
            get_vehicle_of_driver(update, context)
    else:
        update.message.reply_text(f'Зареєструйтесь як водій')


def send_set_status(update, context):
    buttons = [[KeyboardButton(Driver.ACTIVE)],
               [KeyboardButton(Driver.WITH_CLIENT)],
               [KeyboardButton(Driver.WAIT_FOR_CLIENT)],
               [KeyboardButton(Driver.OFFLINE)],
               [KeyboardButton(Driver.RENT)]
               ]

    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус',
                             reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))


def set_status(update, context):
    status = update.message.text
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    try:
        events = Event.objects.filter(full_name_driver=driver, status_event=False)
        event = [i for i in events]
        event[-1].status_event = True
        event[-1].save()
        update.message.reply_text(f'{driver}: Ваш - {event[-1].event} завершено')
    except:
        pass
    ParkStatus.objects.create(driver=driver, status=status)
    if status == Driver.OFFLINE:
        record = UseOfCars.objects.get(user_vehicle=driver, created_at__date=timezone.now().date(), end_at=None)
        record.end_at = timezone.now()
        record.save()
        update.message.reply_text(f'Ви закінчили працювати, до зустрічі', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Твій статус: <b>{status}</b>', reply_markup=ReplyKeyboardRemove(),
                                  parse_mode=ParseMode.HTML)


CORRECT_AUTO = '- ТАК -'
NOT_CORRECT_AUTO = '- НІ -'


def get_vehicle_of_driver(update, context):
    chat_id = update.message.chat.id
    driver_ = Driver.get_by_chat_id(chat_id)
    context.user_data['u_driver'] = driver_

    keyboard = [[KeyboardButton(f'{CORRECT_AUTO}')],
                [KeyboardButton(f'{NOT_CORRECT_AUTO}')]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard[0], keyboard[1]],
        resize_keyboard=True)

    vehicles = [i.licence_plate for i in Vehicle.objects.filter(driver=driver_.id)]
    if vehicles:
        if len(vehicles) == 1:
            vehicle = Vehicle.objects.get(licence_plate=vehicles[0])
            if vehicle.gps_imei:
                update.message.reply_text(f'Ви сьогодні на авто з номерним знаком {vehicles[0]}?',
                                          reply_markup=reply_markup)
                context.user_data['use_vehicle'] = vehicles[0]
            else:
                update.message.reply_text(
                    'За вашим авто не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
        else:
            global STATE_D
            licence_plates = {i.id: i.licence_plate for i in Vehicle.objects.all() if i.licence_plate in vehicles}
            vehicles = {k: licence_plates[k] for k in sorted(licence_plates)}
            context.user_data['data_vehicles'] = vehicles
            report_list_vehicles = ''
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(f'Укажіть номер машини, яку ви будете використовувати сьогодні')
            STATE_D = V_CAR
    else:
        update.message.reply_text("За вами не закріплено жодного авто. Зверніться до менеджерів")


def add_vehicle_to_driver(update, context):
    global STATE_D
    id_vehicle = update.message.text
    chat_id = update.message.chat.id
    try:
        id_vehicle = int(id_vehicle)
        if id_vehicle in context.user_data['data_vehicles']:
            vehicle = Vehicle.objects.get(id=id_vehicle)
        else:
            update.message.reply_text('Такого ключа немає у вашому списку, спробуйте ще раз')
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
    record = UseOfCars.objects.filter(licence_plate=vehicle, created_at__date=timezone.now().date(), end_at=None)
    if record:
        update.message.reply_text(
            'Це авто вже використовує інший водій. Спробуйте інше авто. Якщо всі авто заняті зверніться до менеджерів')
        get_vehicle_of_driver(update, context)
    else:
        if vehicle.gps_imei:
            UseOfCars.objects.create(
                user_vehicle=context.user_data['u_driver'],
                chat_id=chat_id,
                licence_plate=vehicle)
            update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня')
            STATE_D = None
            send_set_status(update, context)
        else:
            update.message.reply_text(
                'За авто, яке ви обрали не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
            STATE_D = None


def correct_or_not_auto(update, context):
    option = update.message.text
    chat_id = update.message.chat.id
    if option == f'{CORRECT_AUTO}':
        record = UseOfCars.objects.filter(licence_plate=context.user_data['use_vehicle'],
                                          created_at__date=timezone.now().date(), end_at=None)
        if record:
            update.message.reply_text('Ваше авто вже використовує інший водій. Зверніться до менеджерів')
        else:
            UseOfCars.objects.create(
                user_vehicle=context.user_data['u_driver'],
                chat_id=chat_id,
                licence_plate=context.user_data['use_vehicle'])
            update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня',
                                      reply_markup=ReplyKeyboardRemove())
            send_set_status(update, context)
    else:
        update.message.reply_text(
            'Зверніться до менеджерів водіїв та проконсультуйтесь, яку машину вам використовувати сьогодні.' +
            ' Та скористайтесь наступною командою /car_change', reply_markup=ReplyKeyboardRemove())


def get_vehicle_licence_plate(update, context):
    global STATE_D
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        vehicles = {i.id: i.licence_plate for i in Vehicle.objects.all()}
        vehicles = {k: vehicles[k] for k in sorted(vehicles)}
        report_list_vehicles = ''
        if vehicles:
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(
                f'Укажіть номер машини від 1-{len(vehicles)}, яку ви будете використовувати сьогодні',
                reply_markup=ReplyKeyboardRemove())
            STATE_D = V_ID
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку. Зверніться до Менеджера автопарку",
                                      reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Зареєструйтесь як водій')


CORRECT_CHOICE = 'Так'
NOT_CORRECT_CHOICE = 'Ні'


def correct_choice(update, context):
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
        context.user_data['vehicle'] = False
    if context.user_data['vehicle']:
        keyboard = [KeyboardButton(f'{CORRECT_CHOICE}'),
                    KeyboardButton(f'{NOT_CORRECT_CHOICE}')]

        reply_markup = ReplyKeyboardMarkup(
            keyboard=[keyboard],
            resize_keyboard=True)
        licence_plate = context.user_data['vehicle']
        update.message.reply_text(f"Ви обрали {licence_plate}. Вірно?", reply_markup=reply_markup)


def get_imei(update, context):
    global STATE_D
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id=chat_id)
    if context.user_data['vehicle'].gps_imei:
        UseOfCars.objects.create(
            user_vehicle=driver,
            chat_id=chat_id,
            licence_plate=context.user_data['vehicle'])
        update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня',
                                  reply_markup=ReplyKeyboardRemove())
        send_set_status(update, context)
    else:
        update.message.reply_text('Авто яке ви обрали без imei_gps. Зверніться до менеджера автопарку/водіїв',
                                  reply_markup=ReplyKeyboardRemove())
    STATE_D = None


def get_licence_plate_for_gps_imei(update, context):
    global STATE_DM
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    vehicles = {i.id: i.licence_plate for i in Vehicle.objects.all()}
    vehicles = {k: vehicles[k] for k in sorted(vehicles)}
    report_list_vehicles = ''
    if driver_manager is not None:
        if vehicles:
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(
                f'Укажіть номер машини від 1-{len(vehicles)}, для якого ви бажаєте добавити gps_imei')
            STATE_DM = V_GPS
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку")
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


def get_n_vehicle(update, context):
    global STATE_DM
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
        update.message.reply_text('Введіть gps_imei для данного авто')
        STATE_DM = V_GPS_IMEI
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')


def get_gps_imea(update, context):
    global STATE_DM
    gps_imei = update.message.text
    gps_imei = Vehicle.gps_imei_validator(gps_imei=gps_imei)
    if gps_imei is not None:
        context.user_data['vehicle'].gps_imei = gps_imei
        context.user_data['vehicle'].save()
        update.message.reply_text('Ми встановили GPS imei до авто, яке ви вказали')
        STATE_DM = None
    else:
        update.message.reply_text("Задовне значення. Спробуйте ще раз")


@receiver(post_save, sender=RentInformation)
def send_day_rent(sender, instance, **kwargs):
    try:
        chat_id = instance.driver.chat_id
        if instance.rent_distance > 20 and instance.driver.driver_status != Driver.OFFLINE:
            rent_cost = int((instance.rent_distance - ParkSettings.get_value('FREE_RENT', 20)) * ParkSettings.get_value(
                'RENT_PRICE', 15))
            message = f"""Ваша оренда сьогодні {instance.rent_distance} км,
             вартість оренди {rent_cost}грн"""
            bot.send_message(chat_id=chat_id, text=message)
    except:
        pass


JOB_DRIVER = 'Водій'


# Add job application

def job_application(update, context):
    buttons = [[KeyboardButton(f'{JOB_DRIVER}')]]
    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть посаду на яку ви притендуєте:',
                             reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True,
                                                              one_time_keyboard=True))
    update.message.reply_text(
        "Якщо ви десь помилитесь, ви завжди можете почати спочатку, скориставшись командою /restart")


def restart_jobapplication(update, context):
    context.user_data.clear()
    context.user_data['role'] = f"{JOB_DRIVER}"
    update.message.reply_text("Ви почали подачу заявки спочатку.")
    update.message.reply_text("Введіть ваше Ім`я:")
    return "JOB_USER_NAME"


# Update information for users
def update_name(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['role'] = f"{JOB_DRIVER}"
    if user:
        update.message.reply_text("Введіть ваше Ім`я:", reply_markup=ReplyKeyboardRemove())
        return "JOB_USER_NAME"
    else:
        update.message.reply_text('Спочатку надайте телефон')


def update_second_name(update, context):
    name = update.message.text
    clear_name = User.name_and_second_name_validator(name=name)
    if clear_name is not None:
        context.user_data['u_name'] = clear_name
        update.message.reply_text("Введіть Прізвище:")
        return "JOB_LAST_NAME"
    else:
        update.message.reply_text('Ім`я занадто довге. Спробуйте ще раз')
        return "JOB_USER_NAME"


def update_email(update, context):
    second_name = update.message.text
    clear_second_name = User.name_and_second_name_validator(name=second_name)
    if clear_second_name is not None:
        context.user_data['u_second_name'] = clear_second_name
        update.message.reply_text("Введіть електронну адресу:")
        return "JOB_EMAIL"
    else:
        update.message.reply_text('Прізвище занадто довге. Спробуйте ще раз')
        return "JOB_LAST_NAME"


def update_user_information(update, context):
    email = update.message.text
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    clear_email = User.email_validator(email=email)
    context.user_data['phone'] = user.phone_number
    if clear_email is not None:
        user.name = context.user_data['u_name']
        user.second_name = context.user_data['u_second_name']
        user.email = clear_email
        user.save()
        buttons = [[InlineKeyboardButton(text='Завантажити документи', callback_data='job_photo')]]
        update.message.reply_text(
            'Ваші дані оновлені, надайте будь-ласка необхідні документи, скориставшись кнопкою під повідомленням',
            reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_FOR_JOB_OPTION"
    else:
        update.message.reply_text('Eлектронна адреса некоректна. Спробуйте ще раз')
        return 'JOB_EMAIL'


def get_job_photo(update, context):
    empty_inline_keyboard = InlineKeyboardMarkup([])
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text='Надішліть ваше фото не розмите, без головного убору та окулярів (селфі).Для відправки скористайтеся \U0001F4CE біля menu',
        reply_markup=empty_inline_keyboard)
    return 'WAIT_FOR_JOB_PHOTO'


def upload_photo(update, context):
    os.makedirs('data/mediafiles/job/photo/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/photo/{image["file_unique_id"]}.jpg'
        context.user_data['photo_job'] = f'job/photo/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Ваше фото збережено.Надішліть лицьову сторону посвідчення')
        context.bot.send_photo(update.effective_chat.id,
                               'https://kourier.in.ua/uploads/posts/2016-12/1480604684_1702.jpg')
        return 'WAIT_FOR_FRONT_PHOTO'
    else:
        update.message.reply_text('Будь ласка, надішліть фото (селфі).Для відправки скористайтеся \U0001F4CE біля menu',
                                  reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_JOB_PHOTO'


def upload_license_front_photo(update, context):
    os.makedirs('data/mediafiles/job/licenses/front/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/licenses/front/{image["file_unique_id"]}.jpg'
        context.user_data['front_license'] = f'job/licenses/front/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Лицьова сторона посвідчення збережена.Надішліть тильну сторону')
        context.bot.send_photo(update.effective_chat.id,
                               'https://www.autoconsulting.com.ua/pictures/_upload/1582561870fbTo_h.jpg')
        return 'WAIT_FOR_BACK_PHOTO'
    else:
        update.message.reply_text('Будь ласка, надішліть лицьову сторону', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_FRONT_PHOTO'


def upload_license_back_photo(update, context):
    os.makedirs('data/mediafiles/job/licenses/back/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/licenses/back/{image["file_unique_id"]}.jpg'
        context.user_data['back_license'] = f'job/licenses/back/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text(
            'Тильна сторона посвідчення збережена.Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25).')
        update.message.reply_text(
            'Якщо посвідчення безстрокове введіть 2077-12-31 або будь-яку іншу дату у далекому майбутньому до 2077р.:')
        return 'WAIT_FOR_EXPIRED'
    else:
        update.message.reply_text('Будь ласка, надішліть тильну сторону', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_BACK_PHOTO'


def upload_expired_date(update, context):
    date = update.message.text
    if JobApplication.validate_date(date):
        context.user_data['expired_license'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        buttons = [[InlineKeyboardButton(text='так', callback_data='have_auto')],
                   [InlineKeyboardButton(text='ні', callback_data='no_auto')]]
        update.message.reply_text('Чи є у вас авто для роботи:', reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_ANSWER"
    else:
        update.message.reply_text(
            f'{date} не вірний формат або дата, Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_EXPIRED'


def check_auto(update, context):
    query = update.callback_query
    empty_inline_keyboard = InlineKeyboardMarkup([])
    if query.data == 'have_auto':
        query.answer()
        query.edit_message_text('Дякуємо! Будь ласка, надішліть фото посвідчення про реєстрацію авто.',
                                reply_markup=empty_inline_keyboard)
        context.bot.send_photo(query.message.chat_id,
                               'https://protocol.ua/userfiles/tehpasport-na-avto.jpg')
        return 'WAIT_FOR_AUTO_YES_OPTION'
    else:
        chat_id = update.effective_chat.id
        user = User.get_by_chat_id(chat_id)
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            update.message.reply_text('Ви вже подали заявку.Очікуйте дзвінка від нашого менеджера')
        except JobApplication.DoesNotExist:
            JobApplication.objects.create(
                first_name=user.name,
                last_name=user.second_name,
                email=user.email,
                phone_number=user.phone_number,
                license_expired=context.user_data['expired_license'],
                driver_license_front=context.user_data['front_license'],
                driver_license_back=context.user_data['back_license'],
                photo=context.user_data['photo_job'],
                role=context.user_data['role'])
        finally:
            query.edit_message_text(
                f'Заявка сформована.На номер {user.phone_number} відправлено СМС перешліть чотири цифри коду мені будь-ласка')
            context.user_data['thread'] = True
            t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
            t.start()
            return "JOB_UKLON_CODE"


def upload_auto_doc(update, context):
    os.makedirs('data/mediafiles/job/car/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/car/{image["file_unique_id"]}.jpg'
        context.user_data['auto_doc'] = f'job/car/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Якщо щось пішло не так, ви можете почати спочатку за допомогою команди /restart')
        update.message.reply_text(
            'Фото техпаспорту збережено.Надішліть фото автоцивілки')
        context.bot.send_photo(update.effective_chat.id,
                               'https://rinokstrahovka.ua/img/content/2019/07/paper_client_green1.jpg')
        return 'WAIT_FOR_INSURANCE'
    else:
        update.message.reply_text('Будь ласка, надішліть фото техпаспорту', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_insurance(update, context):
    os.makedirs('data/mediafiles/job/insurance/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/insurance/{image["file_unique_id"]}.jpg'
        context.user_data['insurance'] = f'job/insurance/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text(
            'Фото автоцивілки збережено.Надішліть срок дії автоцивілки у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_INSURANCE_EXPIRED'
    else:
        update.message.reply_text('Будь ласка, надішліть фото автоцивілки', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_INSURANCE'


def upload_expired_insurance(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    date = update.message.text
    if JobApplication.validate_date(date):
        context.user_data['expired_insurance'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            update.message.reply_text('Ви вже подали заявку.Очікуйте дзвінка від нашого менеджера')
        except JobApplication.DoesNotExist:
            JobApplication.objects.create(
                first_name=user.name,
                last_name=user.second_name,
                email=user.email,
                phone_number=user.phone_number,
                license_expired=context.user_data['expired_license'],
                driver_license_front=context.user_data['front_license'],
                driver_license_back=context.user_data['back_license'],
                photo=context.user_data['photo_job'],
                role=context.user_data['role'],
                car_documents=context.user_data['auto_doc'],
                insurance=context.user_data['insurance'],
                insurance_expired=context.user_data['expired_insurance']
            )
        finally:
            context.user_data['thread'] = True
            t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
            t.start()
            update.message.reply_text(
                f'Заявка сформована.На номер {user.phone_number} відправлено СМС перешліть чотири цифри коду нам протягом 3 хвилин будь-ласка')
            return "JOB_UKLON_CODE"
    else:
        update.message.reply_text(
            f'{date} не вірний формат або дата, Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_EXPIRED'


def uklon_code(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['thread'] = False
    r = redis.Redis.from_url(os.environ["REDIS_URL"])
    r.publish(f'{user.phone_number} code', update.message.text)
    update.message.reply_text(
        'Ваш код прийнято.Наш менеджер з вами зв\'яжеться.Не забудьте зареєструватись на сайті https://supplier.uber.com, як водій')
    return ConversationHandler.END


def code_timer(update, context, timer, sleep):
    def timer_callback(context):
        context.bot.send_message(update.effective_chat.id,
                                 f'Заявку відхилено.Ви завжди можете подати її повторно')
        JobApplication.objects.filter(phone_number=context.user_data['phone']).first().delete()
        return ConversationHandler.END

    remaining_time = timer
    while remaining_time > 0:
        try:
            tread_state = context.user_data['thread']
            if tread_state:
                if remaining_time < sleep + 1:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Залишилось {int(remaining_time)} секунд.Якщо ви не відправите код заявку буде скасовано')
                    time.sleep(remaining_time)
                    remaining_time = 0
                    timer_callback(context)
                else:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Коду лишилось діяти {int(remaining_time)} секунд.Поспішіть будь-ласка')
                    time.sleep(sleep)
                    remaining_time = int(remaining_time - sleep)
            else:
                break
        except KeyError:
            break


# Sending comment
def comment(update, context):
    global STATE
    STATE = COMMENT
    order = Order.get_order(chat_id_client=update.message.chat.id,
                            phone=context.user_data['phone_number'],
                            status_order=Order.WAITING)
    keyboard = [
        KeyboardButton(text="\U00002b50*5"),
        KeyboardButton(text="\U00002b50*4"),
        KeyboardButton(text="\U00002b50*3"),
        KeyboardButton(text="\U00002b50*2")
    ]
    if order:
        order.status_order = Order.CANCELED
        order.save()
        update.message.reply_text('Поставте оцінку або напишіть відгук',
                                  reply_markup=ReplyKeyboardMarkup(keyboard=[keyboard]))
    else:
        update.message.reply_text('Залишіть відгук або сповістіть про проблему', reply_markup=ReplyKeyboardRemove())


def save_comment(update, context):
    global STATE
    order = Order.objects.filter(chat_id_client=update.message.chat.id,
                                 status_order=Order.CANCELED,
                                 created_at__date=timezone.now().date())
    user_comment = Comment.objects.create(
        comment=update.message.text,
        chat_id=update.message.chat.id)
    if order:
        last_order = list(order)[-1]
        last_order.comment = user_comment
        last_order.save()
    STATE = None
    update.message.reply_text("Ваш відгук було збережено. Очікуйте, менеджер скоро з вами зв`яжеться!")


# Getting id for users
def get_id(update, context):
    chat_id = update.message.chat.id
    update.message.reply_text(f"Ваш id: {chat_id}")


# Create driver and other
USER_DRIVER, USER_MANAGER_DRIVER = 'Водія', 'Менеджера водія'
CREATE_USER, CREATE_VEHICLE = 'Добавити користувача', 'Добавити автомобіль'


# Add users and vehicle to db and others
def add(update, context):
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    keyboard = [[KeyboardButton(f'{CREATE_USER}')],
                [KeyboardButton(f'{CREATE_VEHICLE}')]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard[0], keyboard[1]],
        resize_keyboard=True)
    if driver_manager is not None:
        context.user_data['role'] = driver_manager
        update.message.reply_text('Оберіть опцію, що ви бажаєте створити', reply_markup=reply_markup)
    else:
        update.message.reply_text("Зареєструйтесь, як менеджер водіїв")


def create(update, context):
    keyboard = [[KeyboardButton(text=f"{USER_DRIVER}")],
                [KeyboardButton(text=f"{USER_MANAGER_DRIVER}")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard[0], keyboard[1]],
        resize_keyboard=True)

    update.message.reply_text('Оберіть користувача, якого ви бажаєте створити', reply_markup=reply_markup)


def name(update, context):
    global STATE_DM
    context.user_data['role'] = update.message.text
    update.message.reply_text("Введіть Ім`я:", reply_markup=ReplyKeyboardRemove())
    STATE_DM = NAME


def second_name(update, context):
    global STATE_DM
    name = update.message.text
    name = User.name_and_second_name_validator(name=name)
    if name is not None:
        context.user_data['name'] = name
        update.message.reply_text("Введіть Прізвище:")
        STATE_DM = SECOND_NAME
    else:
        update.message.reply_text('Ім`я занадто довге. Спробуйте ще раз')


def email(update, context):
    global STATE_DM
    second_name = update.message.text
    second_name = User.name_and_second_name_validator(name=second_name)
    if second_name is not None:
        context.user_data['second_name'] = second_name
        update.message.reply_text("Введіть електронну адресу:")
        STATE_DM = EMAIL
    else:
        update.message.reply_text('Прізвище занадто довге. Спробуйте ще раз')


def phone_number(update, context):
    global STATE_DM
    email = update.message.text
    email = User.email_validator(email=email)
    if email is not None:
        context.user_data['email'] = email
        update.message.reply_text("Введіть телефонний номер:")
        STATE_DM = PHONE_NUMBER
    else:
        update.message.reply_text('Eлектронна адреса некоректна. Спробуйте ще раз')


def create_user(update, context):
    global STATE_DM
    phone_number = update.message.text
    chat_id = update.message.chat.id
    phone_number = User.phone_number_validator(phone_number=phone_number)
    if phone_number is not None:
        if context.user_data['role'] == USER_DRIVER:
            driver = Driver.objects.create(
                name=context.user_data['name'],
                second_name=context.user_data['second_name'],
                email=context.user_data['email'],
                phone_number=phone_number)

            manager = DriverManager.get_by_chat_id(chat_id)
            manager.driver_id.add(driver.id)
            manager.save()
            update.message.reply_text('Водія було добавленно в базу данних')
        elif context.user_data['role'] == USER_MANAGER_DRIVER:
            DriverManager.objects.create(
                name=context.user_data['name'],
                second_name=context.user_data['second_name'],
                email=context.user_data['email'],
                phone_number=phone_number)

            update.message.reply_text('Менеджера водія було добавленно в базу данних')
        STATE_DM = None
    else:
        update.message.reply_text('Телефонний номер некоректний')


SERVICEABLE = 'Придатна'
BROKEN = 'Зламана'

STATE_D = None  # range(50 - 100)
NUMBERPLATE, REPORT, V_ID, V_CAR = range(50, 54)


# Changing status car
def status_car(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        buttons = [[KeyboardButton(f'{SERVICEABLE}')], [KeyboardButton(f'{BROKEN}')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус автомобіля',
                                 reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())


def numberplate(update, context):
    global STATE_D
    context.user_data['status'] = update.message.text
    update.message.reply_text('Введіть номер автомобіля', reply_markup=ReplyKeyboardRemove())
    STATE_D = NUMBERPLATE


def change_status_car(update, context):
    global STATE_D
    context.user_data['licence_place'] = update.message.text.upper()
    number_car = context.user_data['licence_place']
    numberplates = [i.licence_plate for i in Vehicle.objects.all()]
    if number_car in numberplates:
        vehicle = Vehicle.get_by_numberplate(number_car)
        vehicle.car_status = context.user_data['status']
        vehicle.save()
        numberplates.clear()
        update.message.reply_text('Статус авто був змінений')
    else:
        update.message.reply_text(
            'Цього номера немає в базі даних або надіслано неправильні дані. Зверніться до менеджера або повторіть команду')

    STATE_D = None


SEND_REPORT_DEBT = 'Надіслати звіт про оплату заборгованості'


# Sending report for drivers(payment debt)
def sending_report(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        buttons = [[InlineKeyboardButton(text=f'{SEND_REPORT_DEBT}', callback_data='photo_debt')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                                 reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_FOR_DEBT_OPTION"
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())


def get_debt_photo(update, context):
    empty_inline_keyboard = InlineKeyboardMarkup([])
    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Надішліть фото оплати заборгованості',
                                            reply_markup=empty_inline_keyboard)
    return 'WAIT_FOR_DEBT_PHOTO'


def save_debt_report(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'{image.file_unique_id}.jpg'
        image.download(filename)
        Report_of_driver_debt.objects.create(
            driver=driver,
            image=f'static/{filename}'
        )
        update.message.reply_text(text='Ваш звіт збережено')
        return ConversationHandler.END
    else:
        update.message.reply_text('Будь ласка, надішліть фото', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_DEBT_PHOTO'


# Viewing broken car
def broken_car(update, context):
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    if driver_manager is not None:
        vehicle = Vehicle.objects.filter(car_status=f'{BROKEN}')
        report = ''
        result = [f'{i.licence_plate}' for i in vehicle]
        if len(result) == 0:
            update.message.reply_text("Немає зламаних авто")
        else:
            for i in result:
                report += f'{i}\n'
            update.message.reply_text(f'{report}')
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


STATE_DM = None  # range (100 -150)
NAME, SECOND_NAME, EMAIL, PHONE_NUMBER = range(100, 104)
STATUS, DRIVER, CAR_NUMBERPLATE, RATE, NAME_VEHICLE, MODEL_VEHICLE, LICENCE_PLATE_VEHICLE, VIN_CODE_VEHICLE = range(104,
                                                                                                                    112)
JOB_APPLICATION, V_GPS, V_GPS_IMEI = range(112, 115)


# Viewing status driver
def driver_status(update, context):
    global STATE_DM
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    if driver_manager is not None:
        buttons = [[KeyboardButton(f'- {Driver.ACTIVE}')],
                   [KeyboardButton(f'- {Driver.WITH_CLIENT}')],
                   [KeyboardButton(f'- {Driver.WAIT_FOR_CLIENT}')],
                   [KeyboardButton(f'- {Driver.OFFLINE}')],
                   [KeyboardButton(f'- {Driver.RENT}')]
                   ]
        STATE_DM = STATUS
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус',
                                 reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


def viewing_status_driver(update, context):
    global STATE_DM
    status = update.message.text
    status = status[2:]
    driver = Driver.objects.filter(driver_status=status)
    report = ''
    result = [f'{i.name} {i.second_name}' for i in driver]
    if len(result) == 0:
        update.message.reply_text('Зараз немає водіїв з таким статусом', reply_markup=ReplyKeyboardRemove())
    else:
        for i in result:
            report += f'{i}\n'
    update.message.reply_text(f'{report}', reply_markup=ReplyKeyboardRemove())
    STATE_DM = None


TAKE_A_DAY_OFF = 'Взяти вихідний'
TAKE_SICK_LEAVE = 'Взяти лікарняний'
SIGN_UP_FOR_A_SERVICE_CENTER = 'Записатись до сервісного центру'
REPORT_CAR_DAMAGE = 'Оповістити про пошкодження авто'


def option(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    keyboard = [KeyboardButton(text=f"{SIGN_UP_FOR_A_SERVICE_CENTER}"),
                KeyboardButton(text=f"{REPORT_CAR_DAMAGE}"),
                KeyboardButton(text=f"{TAKE_A_DAY_OFF}"),
                KeyboardButton(text=f"{TAKE_SICK_LEAVE}")]
    if driver is not None:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[keyboard],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        update.message.reply_text('Оберіть опцію: ', reply_markup=reply_markup)
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())


def take_a_day_off_or_sick_leave(update, context):
    event = update.message.text
    chat_id = update.message.chat.id
    event = event.split()
    driver = Driver.get_by_chat_id(chat_id)
    events = Event.objects.filter(full_name_driver=driver, status_event=False)
    list_event = [i for i in events]
    if len(list_event) > 0:
        update.message.reply_text(
            f"У вас вже відкритий <<Лікарняний>> або <<Вихідний>>.\nЩоб закрити подію скористайтесь командою /status")
    else:
        driver.driver_status = f'{Driver.OFFLINE}'
        driver.save()
        Event.objects.create(
            full_name_driver=driver,
            event=event[1].title(),
            chat_id=chat_id,
            created_at=datetime.datetime.now())
        update.message.reply_text(
            f'Ваш статус зміненно на <<{Driver.OFFLINE}>> та ваш <<{event[1].title()}>> розпочато',
            reply_markup=ReplyKeyboardRemove())


# Add Vehicle to driver
def get_list_drivers(update, context):
    global STATE_DM
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    if driver_manager is not None:
        drivers = {i.id: f'{i.name} {i.second_name}' for i in Driver.objects.all()}
        if len(drivers) == 0:
            update.message.reply_text('Кількість зареєстрованих водіїв 0')
        else:
            drivers_keys = sorted(drivers)
            drivers = {i: drivers[i] for i in drivers_keys}
            report_list_drivers = ''
            for k, v in drivers.items():
                report_list_drivers += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_drivers}')
            STATE_DM = DRIVER
            update.message.reply_text('Укажіть номер водія, якому хочете добавити авто.')
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


def get_list_vehicle(update, context):
    global STATE_DM
    id_driver = update.message.text
    try:
        id_driver = int(id_driver)
        context.user_data['driver'] = Driver.objects.get(id=id_driver)
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер водія виявився недійсним. Спробуйте ще раз')
    vehicles = {i.id: i.licence_plate for i in Vehicle.objects.all()}
    if len(vehicles) == 0:
        update.message.reply_text('Кількисть зареєстрованих траспортних засобів 0')
    else:
        if context.user_data['driver'] is not None:
            report_list_vehicles = ''
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            STATE_DM = CAR_NUMBERPLATE
            update.message.reply_text('Укажіть номер авто, який ви хочете прикріпити до водія')


F_UKLON, F_UBER, F_BOLT = 'NewUklon', 'Uber', 'Bolt'


def get_fleet(update, context):
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
    if context.user_data['vehicle'] is not None:
        buttons = [[KeyboardButton(F_UKLON)],
                   [KeyboardButton(F_UBER)],
                   [KeyboardButton(F_BOLT)]]
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Оберіть автопарк. Для прикріплення автомобіля водію',
                                 reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))


def get_driver_external_id(update, context):
    global STATE_DM
    fleet = update.message.text
    context.user_data['fleet'] = fleet
    try:
        response = Fleets_drivers_vehicles_rate.objects.get(
            fleet=Fleet.objects.get(name=fleet),
            driver=context.user_data['driver'],
            vehicle=context.user_data['vehicle'])
        response = str(response)
    except:
        if fleet == F_UKLON:
            try:
                driver = str(context.user_data['driver'])
                driver = driver.split()
                driver = f'{driver[1]} {driver[0]}'
                driver_external_id = NewUklonPaymentsOrder.objects.get(full_name=driver)
                driver_external_id = driver_external_id.signal
            except:
                pass
        elif fleet == F_BOLT:
            try:
                driver_external_id = BoltPaymentsOrder.objects.get(driver_full_name=str(context.user_data['driver']))
                driver_external_id = driver_external_id.mobile_number
            except:
                pass
        else:
            try:
                driver = str(context.user_data['driver'])
                driver = driver.split()
                driver_external_id = UberPaymentsOrder.objects.get(first_name=driver[0], last_name=driver[1])
                driver_external_id = driver_external_id.driver_uuid
            except:
                pass

        try:
            context.user_data['driver_external_id'] = driver_external_id
        except:
            context.user_data['driver_external_id'] = 'pass'

        drivers_rate = {key: round(key * 0.05, 2) for key in range(1, 21)}
        rate = ''
        for k, v in drivers_rate.items():
            rate += f'{k}: {v}\n'

        context.user_data['rate'] = drivers_rate
        update.message.reply_text(f"{rate}", reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(
            f"Укажіть номер рейтингу, який ви хочете встановити для {context.user_data['driver']} в автопарку {context.user_data['fleet']}")
        STATE_DM = RATE
    try:
        if isinstance(response, str):
            update.message.reply_text('Для даного водія вже прикріплене данне авто та автопарк. Спробуйте спочатку')
            STATE_DM = None
    except:
        pass


def add_information_to_driver(update, context):
    global STATE_DM
    id_rate = update.message.text
    try:
        id_rate = int(id_rate)
        rate = context.user_data['rate']
        rate = rate[id_rate]
    except:
        update.message.reply_text(
            'Не вдалось обробити ваше значення, або переданий номер рейтингу не є дійсним. Спробуйте ще раз')
    if isinstance(rate, float):
        Fleets_drivers_vehicles_rate.objects.create(
            fleet=Fleet.objects.get(name=context.user_data['fleet']),
            driver=context.user_data['driver'],
            vehicle=context.user_data['vehicle'],
            driver_external_id=context.user_data['driver_external_id'],
            rate=rate)
        update.message.reply_text(f"Ви добавили водію машину та рейтинг в автопарк {context.user_data['fleet']}")
        if context.user_data['driver_external_id'] == 'pass':
            update.message.reply_text(f"Водія {context.user_data['driver']} збереженно зі значенням driver_external_id = \
                        {context.user_data['driver_external_id']}. Ви можете його змінити власноруч, через панель адміністратора")
        STATE_DM = None


# Push job application to fleets
def get_list_job_application(update, context):
    global STATE_DM
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    if driver_manager is not None:
        applications = {i.id: f'{i}' for i in JobApplication.objects.all() if
                        (i.role == f'{JOB_DRIVER}' and i.status_job_application == False)}
        if len(applications) == 0:
            update.message.reply_text('Заявок на роботу водія поки немає')
        else:
            report_list_applications = ''
            for k, v in applications.items():
                report_list_applications += f'{k}: {v}\n'
            update.message.reply_text(report_list_applications)
            update.message.reply_text('Укажіть номер користувача, заявку якого ви бажаєте відправити')
            STATE_DM = JOB_APPLICATION
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


def get_fleet_for_job_application(update, context):
    global STATE_DM
    id_job_application = update.message.text
    try:
        id_job_application = int(id_job_application)
        context.user_data['job_application'] = JobApplication.objects.get(id=id_job_application)
        buttons = [[KeyboardButton(f'- {F_BOLT}')],
                   [KeyboardButton(f'- {F_UBER}')]]
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Оберіть автопарк. Куди ви бажаєте подати заявку',
                                 reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        STATE_DM = None
    except:
        update.message.reply_text('Не вдалось обробити ваше значення. Спробуйте ще раз')


def add_job_application_to_fleet(update, context):
    response = update.message.text
    data = context.user_data['job_application']
    if response == f'- {F_BOLT}':
        send_on_job_application_on_driver_to_Bolt.delay(email=data.email, phone_number=data.phone_number)
        update.message.reply_text('Заявка була додана в автопарк Bolt', reply_markup=ReplyKeyboardRemove())
    elif response == f'- {F_UBER}':
        send_on_job_application_on_driver_to_Uber.delay(phone_number=data.phone_number,
                                                        email=data.email,
                                                        name=data.first_name,
                                                        second_name=last_name)

        update.message.reply_text('Заявка була додана в автопарк Uber', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(
            'Якщо заявки немає в автопарку, користувачу потрібно зареєструватись на сайті як водій')


# Add vehicle to db
def name_vehicle(update, context):
    global STATE_DM
    update.message.reply_text('Введіть назву авто:', reply_markup=ReplyKeyboardRemove())
    STATE_DM = NAME_VEHICLE


def get_name_vehicle(update, context):
    global STATE_DM
    name_vehicle = update.message.text
    name_vehicle = Vehicle.name_validator(name=name_vehicle)
    if name_vehicle is not None:
        context.user_data['name_vehicle'] = name_vehicle
        update.message.reply_text('Введіть модель авто:')
        STATE_DM = MODEL_VEHICLE
    else:
        update.message.reply_text('Назва занадто довга. Спробуйте ще раз')


def get_model_vehicle(update, context):
    global STATE_DM
    model_vehicle = update.message.text
    model_vehicle = Vehicle.model_validator(model=model_vehicle)
    if model_vehicle is not None:
        context.user_data['model_vehicle'] = model_vehicle
        update.message.reply_text('Введіть автомобільний номер:')
        STATE_DM = LICENCE_PLATE_VEHICLE
    else:
        update.message.reply_text('Назва занадто довга. Спробуйте ще раз')


def get_licence_plate_vehicle(update, context):
    global STATE_DM
    licence_plate_vehicle = update.message.text
    licence_plate_vehicle = Vehicle.licence_plate_validator(licence_plate=licence_plate_vehicle)
    if licence_plate_vehicle is not None:
        context.user_data['licence_plate_vehicle'] = licence_plate_vehicle
        update.message.reply_text('Введіть vin_code для машини (максимальна кількість символів 17)')
        STATE_DM = VIN_CODE_VEHICLE
    else:
        update.message.reply_text('Номерний знак занадто довгий. Спробуйте ще раз')


def get_vin_code_vehicle(update, context):
    global STATE_DM
    vin_code = update.message.text
    vin_code = Vehicle.vin_code_validator(vin_code=vin_code)
    if vin_code is not None:
        Vehicle.objects.create(
            name=context.user_data['name_vehicle'],
            model=context.user_data['model_vehicle'],
            licence_plate=context.user_data['licence_plate_vehicle'],
            vin_code=vin_code)
        update.message.reply_text('Машину додано до бази даних')
        STATE_DM = None
    else:
        update.message.reply_text('Vin code занадто довгий. Спробуйте ще раз')


STATE_SSM = None  # range(150-200)
LICENCE_PLATE, PHOTO, START_OF_REPAIR, END_OF_REPAIR = range(150, 154)


# Sending report on repair
def numberplate_car(update, context):
    global STATE_SSM
    chat_id = update.message.chat.id
    service_station_manager = ServiceStationManager.get_by_chat_id(chat_id)
    if service_station_manager is not None:
        STATE_SSM = LICENCE_PLATE
        update.message.reply_text('Будь ласка, введіть номерний знак автомобіля')
    else:
        update.message.reply_text('Зареєструйтесь як менеджер сервісного центру')


def photo(update, context):
    global STATE_SSM
    context.user_data['licence_plate'] = update.message.text.upper()
    numberplates = [i.licence_plate for i in Vehicle.objects.all()]
    if context.user_data['licence_plate'] not in numberplates:
        update.message.reply_text('Написаного вами номера немає в базі, зверніться до менеджера парку')
    STATE_SSM = PHOTO
    update.message.reply_text('Будь ласка, надішліть мені фото звіту про ремонт (Одне фото)')


def start_of_repair(update, context):
    global STATE_SSM
    context.user_data['photo'] = update.message.photo[-1].get_file()
    update.message.reply_text('Будь ласка, введіть дату та час початку ремонту у форматі: %Y-%m-%d %H:%M:%S')
    STATE_SSM = START_OF_REPAIR


def end_of_repair(update, context):
    global STATE_SSM
    context.user_data['start_of_repair'] = update.message.text + "+00"
    try:
        time.strptime(context.user_data['start_of_repair'], "%Y-%m-%d %H:%M:%S+00")
    except ValueError:
        update.message.reply_text('Недійсна дата')
    STATE_SSM = END_OF_REPAIR
    update.message.reply_text("Будь ласка, введіть дату та час закінченяя ремонту у форматі: %Y-%m-%d %H:%M:%S")


def send_report_to_db_and_driver(update, context):
    global STATE_SSM
    context.user_data['end_of_repair'] = update.message.text + '+00'
    try:
        time.strptime(context.user_data['end_of_repair'], "%Y-%m-%d %H:%M:%S+00")
    except ValueError:
        update.message.reply_text('Недійсна дата')

    order = RepairReport(
        repair=context.user_data['photo']["file_path"],
        numberplate=context.user_data['licence_plate'],
        start_of_repair=context.user_data['start_of_repair'],
        end_of_repair=context.user_data['end_of_repair'])
    order.save()
    STATE_SSM = None
    update.message.reply_text('Ваш звіт збережено в базі даних')


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def code(update: Update, context: CallbackContext):
    pattern = r'^\d{4}$'
    m = update.message.text
    if re.match(pattern, m) is not None:
        r = redis.Redis.from_url(os.environ["REDIS_URL"])
        r.publish('code', update.message.text)
        update.message.reply_text('Формування звіту...')
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    else:
        update.message.reply_text('Боту не вдалось опрацювати ваше повідомлення. Спробуйте пізніше')


def help(update, context) -> str:
    update.message.reply_text('Для першого кроку зробіть реєстрацію або авторизуйтеся командою /start')


STATE_O = None  # range(200-250)
CARD, SUM, PORTMONE_SUM, PORTMONE_COMMISSION, GENERATE_LINK = range(200, 205)

TRANSFER_MONEY = 'Перевести кошти'
_GENERATE_LINK = 'Сгенерувати лінк'


# Transfer money
def payments(update, context):
    chat_id = update.message.chat.id
    owner = Owner.get_by_chat_id(chat_id)
    if owner is not None:
        buttons = [[KeyboardButton(f'{TRANSFER_MONEY}')],
                   [KeyboardButton(f'{_GENERATE_LINK}')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                                 reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    else:
        update.message.reply_text('Ця команда тільки для власника')


def get_card(update, context):
    global STATE_O
    update.message.reply_text('Введіть номер картки отримувача', reply_markup=ReplyKeyboardRemove())
    STATE_O = CARD


def get_sum(update, context):
    global STATE_O
    card = update.message.text
    card = Privat24.card_validator(card=card)
    if card is not None:
        context.user_data['card'] = card
        update.message.reply_text('Введіть суму в форматі DD.CC')
        STATE_O = SUM
    else:
        update.message.reply_text('Введена карта невалідна')


THE_DATA_IS_CORRECT = "Транзакція заповнена вірно"
THE_DATA_IS_WRONG = "Транзакція заповнена невірно"


def transfer(update, context):
    global STATE_O
    global p

    buttons = [[KeyboardButton(f'{THE_DATA_IS_CORRECT}')],
               [KeyboardButton(f'{THE_DATA_IS_WRONG}')]]

    context.user_data['sum'] = update.message.text

    p = Privat24(card=context.user_data['card'], sum=context.user_data['sum'], driver=True, sleep=7, headless=True)
    p.login()
    p.password()
    p.money_transfer()

    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('privat_3.png', 'rb'))
    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                             reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    STATE_O = None


def correct_transfer(update, context):
    p.transfer_confirmation()
    update.message.reply_text("Транзакція пройшла успішно")


def wrong_transfer(update, context):
    update.message.reply_text("Транзакція відмінена")
    p.quit()


# Generate link debt
COMMISSION_ONLY_PORTMONE = 'Використати стандартну комісію'
MY_COMMISSION = "Встановити свою комісію"


def commission(update, context):
    buttons = [[KeyboardButton(f'{COMMISSION_ONLY_PORTMONE}')],
               [KeyboardButton(f'{MY_COMMISSION}')]]
    context.bot.send_message(chat_id=update.effective_chat.id, text='Виберіть, яку комісію бажаєте встановити:',
                             reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))


def get_my_commission(update, context):
    global STATE_O
    update.message.reply_text(
        "Введіть суму комісії в форматі DD.CC (ваша комісія з комісієй сервісу Portmone буде вирахувана від загальної суми)")
    STATE_O = PORTMONE_COMMISSION


def get_sum_for_portmone(update, context):
    global STATE_O
    if STATE_O == PORTMONE_COMMISSION:
        commission = update.message.text
        commission = conversion_to_float(sum=commission)
        if commission is not None:
            context.user_data['commission'] = commission
            update.message.reply_text(f'Введіть суму на яку ви хочете виставити запит, в форматі DD.CC')
            STATE_O = GENERATE_LINK
            STATE_O = GENERATE_LINK
        else:
            update.message.reply_text('Не вдалось опрацювати суму вашої комісії, спробуйте ще раз')
    else:
        update.message.reply_text(f'Введіть суму на яку ви хочете виставити запит, в форматі DD.CC')
        STATE_O = PORTMONE_SUM


def generate_link_v1(update, context):
    global STATE_O
    sum = update.message.text
    n_sum = conversion_to_float(sum=sum)
    if n_sum is not None:
        p = Portmone(sum=n_sum)
        result = p.get_link()
        update.message.reply_text(f'{result}')
        STATE_O = None
    else:
        update.message.reply_text('Не вдалось обробити вашу суму, спробуйте ще раз')


def generate_link_v2(update, context):
    global STATE_O
    sum = update.message.text
    n_sum = conversion_to_float(sum=sum)
    if n_sum is not None:
        p = Portmone(sum=n_sum, commission=context.user_data['commission'])
        result = p.get_link()
        update.message.reply_text(f'{result}')
        STATE_O = None
    else:
        update.message.reply_text('Не вдалось обробити вашу суму, спробуйте ще раз')


def menu(update, context, chat_id):
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    driver = Driver.get_by_chat_id(chat_id)
    manager = ServiceStationManager.get_by_chat_id(chat_id)
    owner = Owner.get_by_chat_id(chat_id)
    standart_commands = [
        BotCommand("/start", "Щоб зареєструватись та замовити таксі"),
        BotCommand("/help", "Допомога"),
        BotCommand("/id", "Дізнатись id"),
        BotCommand("/cancel", "Вийти з процесу"),
    ]
    if driver is not None:
        standart_commands.extend([
            BotCommand("/status", "Змінити статус водія"),
            BotCommand("/car_change", "Реєстрація робочого автомобіля на сьогодні"),
            BotCommand("/status_car", "Змінити статус автомобіля"),
            BotCommand("/sending_report", "Відправити звіт про оплату заборгованості"),
            BotCommand("/option", "Взяти вихідний/лікарняний/Сповістити про пошкодження/Записатись до СТО")])
    elif driver_manager is not None:
        standart_commands.extend([
            BotCommand("/car_status", "Показати всі зломлені машини"),
            BotCommand("/driver_status", "Показати водіїв за їх статусом"),
            BotCommand("/add", "Створити користувачів та автомобілі"),
            BotCommand("/add_imei_gps_to_driver", "Додати авто gps_imei"),
            BotCommand("/add_vehicle_to_driver", "Додати водію автомобіль"),
            BotCommand("/add_job_application_to_fleets", "Додати водія в автопарк")])
    elif manager is not None:
        standart_commands.extend([
            BotCommand("/send_report", "Відправити звіт про ремонт")])
    elif owner is not None:
        standart_commands.extend([
            BotCommand("/report", "Загрузити та побачити недільні звіти"),
            BotCommand("/rating", "Побачити рейтинг водіїв по автопарках за тиждень"),
            BotCommand("/total_weekly_rating", "Побачити рейтинг водіїв загальну за тиждень"),
            BotCommand("/payment", "Перевести кошти або сгенерити лінк на оплату"),
            BotCommand("/download_report", "Загрузити тижневі звіти")])

    context.bot.set_my_commands(standart_commands)


def text(update, context):
    """ STATE - for all users, STATE_D - for drivers, STATE_O - for owner,
            STATE_DM - for driver manager, STATE_SSM - for service station manager"""
    global STATE
    global STATE_O
    global STATE_D
    global STATE_DM
    global STATE_SSM

    if STATE is not None:
        if STATE == FROM_ADDRESS:
            return to_the_address(update, context)
        elif STATE == TO_THE_ADDRESS:
            return payment_method(update, context)
        elif STATE == COMMENT:
            return save_comment(update, context)
        elif STATE == FIRST_ADDRESS_CHECK:
            return first_address_check(update, context)
        elif STATE == SECOND_ADDRESS_CHECK:
            return second_address_check(update, context)
        elif STATE == TIME_ORDER:
            return order_on_time(update, context)
    elif STATE_D is not None:
        if STATE_D == NUMBERPLATE:
            return change_status_car(update, context)
        elif STATE_D == V_ID:
            return correct_choice(update, context)
        elif STATE_D == V_CAR:
            return add_vehicle_to_driver(update, context)
    elif STATE_O is not None:
        if STATE_O == CARD:
            return get_sum(update, context)
        elif STATE_O == SUM:
            return transfer(update, context)
        elif STATE_O == PORTMONE_SUM:
            return generate_link_v1(update, context)
        elif STATE_O == PORTMONE_COMMISSION:
            return get_sum_for_portmone(update, context)
        elif STATE_O == GENERATE_LINK:
            return generate_link_v2(update, context)
    elif STATE_DM is not None:
        if STATE_DM == STATUS:
            return viewing_status_driver(update, context)
        elif STATE_DM == NAME:
            return second_name(update, context)
        elif STATE_DM == SECOND_NAME:
            return email(update, context)
        elif STATE_DM == EMAIL:
            return phone_number(update, context)
        elif STATE_DM == PHONE_NUMBER:
            return create_user(update, context)
        elif STATE_DM == DRIVER:
            return get_list_vehicle(update, context)
        elif STATE_DM == CAR_NUMBERPLATE:
            return get_fleet(update, context)
        elif STATE_DM == RATE:
            return add_information_to_driver(update, context)
        elif STATE_DM == NAME_VEHICLE:
            return get_name_vehicle(update, context)
        elif STATE_DM == MODEL_VEHICLE:
            return get_model_vehicle(update, context)
        elif STATE_DM == LICENCE_PLATE_VEHICLE:
            return get_licence_plate_vehicle(update, context)
        elif STATE_DM == VIN_CODE_VEHICLE:
            return get_vin_code_vehicle(update, context)
        elif STATE_DM == JOB_APPLICATION:
            return get_fleet_for_job_application(update, context)
        elif STATE_DM == V_GPS:
            return get_n_vehicle(update, context)
        elif STATE_DM == V_GPS_IMEI:
            return get_gps_imea(update, context)
    elif STATE_SSM is not None:
        if STATE_SSM == LICENCE_PLATE:
            return photo(update, context)
        elif STATE_SSM == PHOTO:
            return start_of_repair(update, context)
        elif STATE_SSM == START_OF_REPAIR:
            return end_of_repair(update, context)
        elif STATE_SSM == END_OF_REPAIR:
            return send_report_to_db_and_driver(update, context)
    else:
        return code(update, context)


def drivers_rating(update, context):
    text = 'Рейтинг водіїв\n\n'
    for fleet in DriversRatingMixin().get_rating():
        text += fleet['fleet'] + '\n'
        for period in fleet['rating']:
            text += f"{period['start']:%d.%m.%Y} - {period['end']:%d.%m.%Y}" + '\n'
            if period['rating']:
                text += '\n'.join([
                    f"{item['num']} {item['driver']} {item['amount']:15.2f} {- item['trips'] if item['trips'] > 0 else ''}"
                    for item in period['rating']]) + '\n\n'
            else:
                text += 'Отримання даних... Спробуйте пізніше\n'
    update.message.reply_text(text)


def driver_total_weekly_rating(update, context):
    text = 'Рейтинг водіїв\n'
    totals = {}
    rate = DriversRatingMixin().get_rating()
    text += f"{rate[0]['rating'][0]['start']:%d.%m.%Y} - {rate[0]['rating'][0]['end']:%d.%m.%Y}" + '\n\n'
    for fleet in DriversRatingMixin().get_rating():
        for period in fleet['rating']:
            if period['rating']:
                for item in period['rating']:
                    totals.setdefault(item['driver'], 0)
                    totals[item['driver']] += round(item['amount'], 2)
            else:
                text += 'Отримання даних... Спробуйте пізніше\n'

    totals = dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    id = 1
    for key, value in totals.items():
        text += f"{id} {key}: {value}\n"
        id += 1
    update.message.reply_text(text)


def report(update, context):
    update.message.reply_text('Ваш запит прийнято.\nМи надішлемо вам звіт, як тільки він сформується')
    update.message.reply_text("Введіть ваш Uber OTP код з SMS, якщо ви отримали його")
    get_report_for_tg.delay()


@task_postrun.connect
def send_report(sender=None, **kwargs):
    if sender == get_report_for_tg:
        rep = kwargs.get("retval")
        owner, totals = rep[0], rep[1]
        drivers = {f'{i}': i.chat_id for i in Driver.objects.all()}
        # sending report to owner
        message = f'Fleet Owner: {"%.2f" % owner["Fleet Owner"]}\n\n' + '\n'.join(totals.values())
        bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message)

        # sending report to driver
        if drivers:
            for driver in drivers:
                try:
                    message, chat_id = totals[f'{driver}'], drivers[f'{driver}']
                    bot.send_message(chat_id=chat_id, text=message)
                except:
                    pass


def download_report(update, context):
    update.message.reply_text("Запит на завантаження щотижневого звіту подано")
    download_weekly_report_force.delay()


def cancel(update, context):
    global STATE
    global STATE_D
    global STATE_O
    global STATE_DM
    global STATE_SSM

    STATE, STATE_D, STATE_O, STATE_DM, STATE_SSM = None, None, None, None, None


# Need fix
def update_db(update, context):
    """Pushing data to database from weekly_csv files"""
    # getting and opening files
    directory = '../app'
    files = os.listdir(directory)

    UberPaymentsOrder.download_weekly_report()
    UklonPaymentsOrder.download_weekly_report()
    BoltPaymentsOrder.download_weekly_report()

    files = os.listdir(directory)
    files_csv = filter(lambda x: x.endswith('.csv'), files)
    list_new_files = list(set(files_csv) - set(processed_files))

    if len(list_new_files) == 0:
        update.message.reply_text('No new updates yet')
    else:
        update.message.reply_text('Please wait')
        for name_file in list_new_files:
            processed_files.append(name_file)
            with open(f'{directory}/{name_file}', encoding='utf8') as file:
                if 'Куцко - Income_' in name_file:
                    UklonPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)
                elif '-payments_driver-___.csv' in name_file:
                    UberPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)
                elif 'Kyiv Fleet 03_232 park Universal-auto.csv' in name_file:
                    BoltPaymentsOrder.parse_and_save_weekly_report_to_database(file=file)

        FileNameProcessed.save_filename_to_db(processed_files)
        list_new_files.clear()
        update.message.reply_text('Database updated')


def save_reports(update, context):
    wrf = WeeklyReportFile()
    wrf.save_weekly_reports_to_db()
    update.message.reply_text("Reports have been saved")


def get_owner_today_report(update, context) -> str:
    pass


def get_driver_today_report(update, context) -> str:
    driver_first_name = User.objects.filter(user_id={update.message.chat.id})
    driver_ident = PaymentsOrder.objects.filter(driver_uuid='')
    if user.type == 0:
        data = PaymentsOrder.objects.filter(transaction_time=date.today(), driver_uuid={driver_ident})
        update.message.reply_text(f'Hi {update.message.chat.username} driver')
        update.message.reply_text(text=data)


def get_driver_week_report(update, context) -> str:
    pass


def choice_driver_option(update, context) -> list:
    update.message.reply_text(f'Hi {update.message.chat.username} driver')
    buttons = [[KeyboardButton('Get today statistic')], [KeyboardButton('Choice week number')],
               [KeyboardButton('Update report')]]
    context.bot.send_message(chat_id=update.effective_chat.id, text='choice option',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def get_manager_today_report(update, context) -> str:
    if user.type == 1:
        data = PaymentsOrder.objects.filter(transaction_time=date.today())
        update.message.reply_text(text=data)
    else:
        error_handler()


def get_stat_for_manager(update, context) -> list:
    update.message.reply_text(f'Hi {update.message.chat.username} manager')
    buttons = [[KeyboardButton('Get all today statistic')]]
    context.bot.send_message(chat_id=update.effective_chat.id, text='choice option',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def aut_handler(update, context) -> list:
    if 'Get autorizate' in update.message.text:
        if user.type == 0:
            choice_driver_option(update, context)
        elif user.type == 2:
            get_owner_today_report(update, context)
        elif user.type == 1:
            get_stat_for_manager(update, context)
        else:
            update_phone_number()


def get_update_report(update, context):
    user = User.get_by_chat_id(chat_id)
    if user in uklon_drivers_list:
        uklon.run()
        aut_handler(update, context)
    elif username in bolt_drivers_list:
        bolt.run()
        aut_handler(update, context)
    elif username in uber_drivers_list:
        update.message.reply_text("Enter you Uber OTP code from SMS:")
        uber.run()
        aut_handler(update, context)


# Conversations
debt_conversation = ConversationHandler(
    entry_points=[CommandHandler('sending_report', sending_report)],
    states={
        'WAIT_FOR_DEBT_OPTION': [CallbackQueryHandler(get_debt_photo, pattern='photo_debt')],
        'WAIT_FOR_DEBT_PHOTO': [MessageHandler(Filters.all, save_debt_report)]
    },
    fallbacks=[MessageHandler(Filters.text('cancel'), cancel)],
)

job_docs_conversation = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(r'^Водій$'), update_name),
                  CommandHandler("restart", restart_jobapplication)],
    states={
        "JOB_USER_NAME": [MessageHandler(Filters.all, update_second_name, pass_user_data=True)],
        "JOB_LAST_NAME": [MessageHandler(Filters.all, update_email, pass_user_data=True)],
        "JOB_EMAIL": [MessageHandler(Filters.all, update_user_information, pass_user_data=True)],
        'WAIT_FOR_JOB_OPTION': [CallbackQueryHandler(get_job_photo, pattern='job_photo', pass_user_data=True)],
        'WAIT_FOR_JOB_PHOTO': [MessageHandler(Filters.all, upload_photo, pass_user_data=True)],
        'WAIT_FOR_FRONT_PHOTO': [MessageHandler(Filters.all, upload_license_front_photo, pass_user_data=True)],
        'WAIT_FOR_BACK_PHOTO': [MessageHandler(Filters.all, upload_license_back_photo, pass_user_data=True)],
        'WAIT_FOR_EXPIRED': [MessageHandler(Filters.all, upload_expired_date, pass_user_data=True)],
        'WAIT_ANSWER': [CallbackQueryHandler(check_auto, pass_user_data=True)],
        'WAIT_FOR_AUTO_YES_OPTION': [MessageHandler(Filters.all, upload_auto_doc, pass_user_data=True)],
        'WAIT_FOR_INSURANCE': [MessageHandler(Filters.all, upload_insurance, pass_user_data=True)],
        'WAIT_FOR_INSURANCE_EXPIRED': [MessageHandler(Filters.all, upload_expired_insurance, pass_user_data=True)],
        'JOB_UKLON_CODE': [MessageHandler(Filters.regex(r'^\d{4}$'), uklon_code)]
    },

    fallbacks=[MessageHandler(Filters.text('cancel'), cancel)],
    allow_reentry=True,
)

WEBHOOK_URL = os.environ['WEBHOOK_URL']
bot = Bot(token=os.environ['TELEGRAM_TOKEN'])
updater = Updater(os.environ['TELEGRAM_TOKEN'], use_context=True)
dp = updater.dispatcher


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        json_string = request.body.decode('utf-8')
        update = Update.de_json(json.loads(json_string), bot)
        dp.process_update(update)
        return HttpResponse(status=200)


dp.add_handler(CommandHandler("buy", payment_request))
# Command for Owner
dp.add_handler(CommandHandler("report", report))
dp.add_handler(CommandHandler("download_report", download_report))
dp.add_handler(CommandHandler("rating", drivers_rating))
dp.add_handler(CommandHandler("total_weekly_rating", driver_total_weekly_rating))

# Transfer money
dp.add_handler(CommandHandler("payment", payments))
dp.add_handler(MessageHandler(Filters.regex(fr"^{TRANSFER_MONEY}$"), get_card))
dp.add_handler(MessageHandler(Filters.regex(fr"^{THE_DATA_IS_CORRECT}$"), correct_transfer))
dp.add_handler(MessageHandler(Filters.regex(fr"^{THE_DATA_IS_WRONG}$"), wrong_transfer))

# Generate link debt
dp.add_handler(MessageHandler(Filters.regex(fr"^{_GENERATE_LINK}$"), commission))
dp.add_handler(MessageHandler(Filters.regex(fr"^{COMMISSION_ONLY_PORTMONE}$"), get_sum_for_portmone))
dp.add_handler(MessageHandler(Filters.regex(fr"^{MY_COMMISSION}$"), get_my_commission))

# Publicly available commands
# Getting id
dp.add_handler(CommandHandler("id", get_id))
# Information on commands
dp.add_handler(CommandHandler("help", help))

# Commands for Users
# Ordering taxi
dp.add_handler(CommandHandler("start", start))
# incomplete auth
dp.add_handler(MessageHandler(Filters.contact, update_phone_number))
# ordering taxi
dp.add_handler(MessageHandler(Filters.location, location))

dp.add_handler(MessageHandler(Filters.regex(fr"^\U0001f696 Викликати Таксі$"), continue_order))

dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {LOCATION_CORRECT}$"), to_the_address))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {LOCATION_WRONG}$"), from_address))
dp.add_handler(MessageHandler(Filters.regex(fr"^Замовити на інший час$"), time_order))
updater.job_queue.run_repeating(send_time_orders, interval=int(ParkSettings.get_value('CHECK_ORDER_TIME_SEC', 100)))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {CANCEL}$"), cancel_order))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {CONTINUE}$"), time_for_order))

dp.add_handler(MessageHandler(
    Filters.regex(fr"^\U0001f4b7 {CASH}$") |
    Filters.regex(fr"^\U0001f4b8 {_CARD}$"),
    order_create))

# sending comment
dp.add_handler(MessageHandler(Filters.regex(r"^\U0001f4e2 Залишити відгук$") |
                              Filters.regex(fr"^Відмовитись від замовлення$"),
                              comment))
# Add job application
dp.add_handler(MessageHandler(Filters.regex(r"^\U0001F4E8 Залишити заявку на роботу$"), job_application))

dp.add_handler(job_docs_conversation)

# Commands for Drivers
# Changing status of driver
dp.add_handler(CommandHandler("status", status))
dp.add_handler(MessageHandler(
    Filters.regex(fr"^{Driver.ACTIVE}$") |
    Filters.regex(fr"^{Driver.WITH_CLIENT}$") |
    Filters.regex(fr"^{Driver.WAIT_FOR_CLIENT}$") |
    Filters.regex(fr"^{Driver.OFFLINE}$") |
    Filters.regex(fr"^{Driver.RENT}$"),
    set_status))

# Updating status_car
dp.add_handler(CommandHandler("status_car", status_car))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{SERVICEABLE}$') |
    Filters.regex(fr'^{BROKEN}$'),
    numberplate))

# Sending report(payment debt)
dp.add_handler(debt_conversation)

# Take a day off/Take sick leave
dp.add_handler(CommandHandler("option", option))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{TAKE_A_DAY_OFF}$') |
    Filters.regex(fr'^{TAKE_SICK_LEAVE}$'),
    take_a_day_off_or_sick_leave))

# Сar registration for today
dp.add_handler(CommandHandler("car_change", get_vehicle_licence_plate))

# Get correct auto
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CORRECT_AUTO}$') |
    Filters.regex(fr'^{NOT_CORRECT_AUTO}$'),
    correct_or_not_auto))

# Correct choice change_auto
dp.add_handler(MessageHandler(Filters.regex(fr'^{CORRECT_CHOICE}$'), get_imei))
dp.add_handler(MessageHandler(Filters.regex(fr'^{NOT_CORRECT_CHOICE}$'), get_vehicle_licence_plate))

# Commands for Driver Managers
# Returns status cars
dp.add_handler(CommandHandler("car_status", broken_car))
# Viewing status driver
dp.add_handler(CommandHandler("driver_status", driver_status))
# Add user and other
dp.add_handler(CommandHandler("add", add))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CREATE_USER}$'),
    create))
# Add vehicle to db
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CREATE_VEHICLE}$'),
    name_vehicle))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{USER_DRIVER}$') |
    Filters.regex(fr'^{USER_MANAGER_DRIVER}$'),
    name))
# Add vehicle to drivers
dp.add_handler(CommandHandler("add_vehicle_to_driver", get_list_drivers))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{F_UKLON}$') |
    Filters.regex(fr'^{F_UBER}$') |
    Filters.regex(fr'^{F_BOLT}$'),
    get_driver_external_id))

# The job application on driver sent to fleet
dp.add_handler(CommandHandler("add_job_application_to_fleets", get_list_job_application))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^- {F_BOLT}$') |
    Filters.regex(fr'^- {F_UBER}$'),
    add_job_application_to_fleet))

dp.add_handler(CommandHandler("add_imei_gps_to_driver", get_licence_plate_for_gps_imei))

# Commands for Service Station Manager
# Sending report on repair
dp.add_handler(CommandHandler("send_report", numberplate_car))

# dp.add_handler(CallbackQueryHandler(inline_buttons_for_driver, pattern='^(Accept order|Reject order|On the spot|Сlient on site|Along the route|Off route|End trip)$'))
dp.add_handler(CallbackQueryHandler(handle_callback_order))

# System commands
dp.add_handler(CommandHandler("cancel", cancel))
dp.add_handler(MessageHandler(Filters.text, text))
dp.add_error_handler(error_handler)

# need fix
dp.add_handler(CommandHandler('update', update_db, run_async=True))
dp.add_handler(CommandHandler("save_reports", save_reports))

dp.add_handler(MessageHandler(Filters.text('Get all today statistic'), get_manager_today_report))
dp.add_handler(MessageHandler(Filters.text('Get today statistic'), get_driver_today_report))
dp.add_handler(MessageHandler(Filters.text('Choice week number'), get_driver_week_report))
dp.add_handler(MessageHandler(Filters.text('Update report'), get_update_report))


def main():
    bot_prod_env = os.environ.get('BOT_PROD_ENV')
    if bot_prod_env is not None:
        bot_prod_env = ast.literal_eval(bot_prod_env)
    if bot_prod_env:
        updater.start_webhook(
            listen='0.0.0.0',
            port=PORT,
            webhook_url=f'{WEBHOOK_URL}/webhook/'
        )
        updater.idle()
    else:
        updater.start_polling()
        updater.idle()


def run():
    main()
