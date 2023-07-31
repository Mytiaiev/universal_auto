import os
import re
import datetime
import hashlib
import requests
from django.utils import timezone
from telegram import ReplyKeyboardRemove,  LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from app.models import Order, User, Driver, Vehicle, UseOfCars, ParkStatus, ParkSettings, Client
from app.portmone.portmone import Portmone
from auto.tasks import get_distance_trip, order_create_task, send_map_to_client, check_payment_status_tg
from auto_bot.handlers.main.keyboards import markup_keyboard, get_start_kb, inline_owner_kb, inline_manager_kb
from auto_bot.handlers.order.keyboards import inline_spot_keyboard, inline_route_keyboard, inline_finish_order, \
    inline_repeat_keyboard, inline_reject_order, inline_increase_price_kb, inline_search_kb, inline_start_order_kb, \
    share_location, inline_location_kb, inline_payment_kb, inline_comment_for_client, inline_payment_card
from auto_bot.handlers.order.utils import buttons_addresses, text_to_client
from auto_bot.main import bot
from scripts.conversion import get_address, get_location_from_db
from auto_bot.handlers.order.static_text import *


def continue_order(update, context):
    query = update.callback_query
    order = Order.objects.filter(chat_id_client=update.effective_chat.id,
                                 status_order__in=[Order.ON_TIME, Order.WAITING])
    if order:
        query.edit_message_text(already_ordered)
    else:
        context.user_data['state'] = START_TIME_ORDER
        context.user_data['location_button'] = False
        query.edit_message_text(price_info(ParkSettings.get_value('TARIFF_IN_THE_CITY'),
                                           ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY')))
    query.edit_message_reply_markup(inline_start_order_kb())


def cancel_order(update, context):
    query = update.callback_query
    query.edit_message_text(complete_order_text)
    users = User.objects.filter(chat_id=query.message.chat_id)
    if len(users) == 1:
        user = users.first()
        reply_markup = get_start_kb(user)
    else:
        reply_markup = inline_owner_kb() if any(user.role == "OWNER" for user in users) else inline_manager_kb()
    query.edit_message_reply_markup(reply_markup)
    context.user_data.clear()


def get_location(update, context):
    if update.message:
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
        if query:
            query.edit_message_text(info_address_text)
        else:
            context.bot.send_message(chat_id=chat_id, text=info_address_text)
        context.bot.send_message(chat_id=chat_id, text=from_address_text, reply_markup=reply_markup)
    else:
        query.edit_message_text(from_address_text)


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
            buttons.append([InlineKeyboardButton(order_inline_buttons[6], callback_data="Call_taxi")])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.user_data['addresses_first'] = addresses
            context.bot.send_message(chat_id=chat_id, text=from_address_search, reply_markup=ReplyKeyboardRemove())
            context.bot.send_message(chat_id=chat_id, text=choose_from_address_text, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text=wrong_address_request, reply_markup=ReplyKeyboardRemove())
            from_address(update, context)
    else:
        if query:
            query.edit_message_text(arrival_text)
        else:
            context.bot.send_message(chat_id=chat_id, text=arrival_text)
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
            buttons.append([InlineKeyboardButton(order_inline_buttons[6], callback_data="Wrong_place")])
            reply_markup = InlineKeyboardMarkup(buttons)
            context.user_data['addresses_second'] = addresses
            context.bot.send_message(chat_id=chat_id,
                                     text=choose_to_address_text,
                                     reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text=wrong_address_request)
            to_the_address(update, context)
    else:
        context.user_data['state'] = None
        query.edit_message_text(payment_text)
        query.edit_message_reply_markup(inline_payment_kb())


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
    data = int(query.data.split(' ')[1])
    button_text = query.message.reply_markup.inline_keyboard[data][0].text
    payment = button_text.split(' ')[1]
    user = Client.get_by_chat_id(update.effective_chat.id)
    query.edit_message_text(creating_order_text)
    order_create_task.delay(context.user_data, user.phone_number,
                            user.chat_id, payment, query.message.message_id)


def increase_search_radius(update, context):
    query = update.callback_query
    query.edit_message_text(increase_radius_text)
    query.edit_message_reply_markup(inline_increase_price_kb())


def ask_client_action(update, context):
    query = update.callback_query
    query.edit_message_text(no_driver_in_radius)
    query.edit_message_reply_markup(inline_search_kb())


def increase_order_price(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    order = Order.objects.filter(chat_id_client=chat_id,
                                 status_order=Order.WAITING).last()
    if query.data != "Continue_search":
        order.car_delivery_price += int(query.data)
        order.sum += int(query.data)
    order.checked = False
    order.save()


def time_order(update, context):
    query = update.callback_query
    if query.data == "On_time_order":
        context.user_data['time_order'] = query.data
    context.user_data['state'] = TIME_ORDER
    query.edit_message_text(text=ask_time_text)


def order_on_time(update, context):
    context.user_data['state'], pattern = None, r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$',
    user_time, user = update.message.text, Client.get_by_chat_id(update.message.chat.id)

    if re.match(pattern, user_time):
        format_time = timezone.datetime.strptime(user_time, '%H:%M').time()
        min_time = timezone.localtime().replace(tzinfo=None) + datetime.timedelta(minutes=int(
                                                                       ParkSettings.get_value('TIME_ORDER_MIN', 60)))
        conv_time = timezone.datetime.combine(timezone.localtime(), format_time)

        if min_time <= conv_time:
            if context.user_data.get('time_order') is not None:
                context.user_data['time_order'] = conv_time
                from_address(update, context)
            else:
                order = Order.objects.filter(chat_id_client=user.chat_id,
                                             status_order=Order.WAITING).last()
                order.status_order, order.order_time, order.checked = Order.ON_TIME, conv_time, False
                order.save()
                update.message.reply_text(order_complete)
        else:
            update.message.reply_text(small_time_delta)
            context.user_data['state'] = TIME_ORDER
    else:
        update.message.reply_text(wrong_time_format)
        context.user_data['state'] = TIME_ORDER


def client_reject_order(update, context):
    query = update.callback_query
    order = Order.objects.filter(pk=int(query.data.split(' ')[1])).first()
    order.status_order = Order.CANCELED
    order.save()
    try:
        for i in range(3):
            context.bot.delete_message(chat_id=order.chat_id_client,
                                       message_id=query.message.message_id + i)
    except:
        pass
    try:
        driver_chat_id = order.driver.chat_id
        driver = Driver.get_by_chat_id(chat_id=driver_chat_id)
        message_id = order.driver_message_id
        bot.delete_message(chat_id=driver_chat_id, message_id=message_id)
        bot.send_message(
            chat_id=driver_chat_id,
            text=f'Вибачте, замовлення за адресою {order.from_address} відхилено клієнтом.'
        )
        ParkStatus.objects.create(driver=driver, status=Driver.ACTIVE)
    except Exception:
        pass
    text_to_client(order=order,
                   text=client_cancel,
                   button=inline_comment_for_client())


def handle_callback_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    driver = Driver.get_by_chat_id(chat_id=query.from_user.id)
    order = Order.objects.filter(pk=int(data[1])).first()
    if order.status_order in (Order.COMPLETED, Order.IN_PROGRESS):
        query.edit_message_text(text=already_accepted)
        return
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
                context.bot.delete_message(chat_id=int(ParkSettings.get_value('ORDER_CHAT')),
                                           message_id=int(order.driver_message_id))
                context.bot.send_message(chat_id=driver.chat_id,
                                         text=time_order_accepted(order.from_address,
                                                                  timezone.localtime(order.order_time).time()))
            else:
                ParkStatus.objects.create(driver=driver, status=Driver.WAIT_FOR_CLIENT)
                message = order_info(order.id, order.from_address, order.to_the_address, order.payment_method,
                                     order.phone_number, order.sum, order.distance_google)
                query.edit_message_text(text=message)
                query.edit_message_reply_markup(reply_markup=markup)
                report_for_client = client_order_text(driver, vehicle.name, record.licence_plate,
                                                      driver.phone_number, order.sum)
                client_msg = text_to_client(order, report_for_client, button=inline_reject_order(order.pk))
                order.status_order, order.driver_message_id = Order.IN_PROGRESS, query.message.message_id
                order.client_message_id = client_msg
                order.save()
                if order.chat_id_client:
                    lat, long = get_location_from_db(vehicle)
                    bot.send_message(chat_id=order.chat_id_client, text=order_customer_text)
                    message = bot.sendLocation(order.chat_id_client, latitude=lat, longitude=long, live_period=1800)
                    send_map_to_client.delay(order.id, query.message.message_id,
                                             vehicle.pk, client_msg, message.message_id, message.chat_id)
        else:
            context.bot.send_message(chat_id=query.from_user.id, text=select_car_error)


def handle_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    driver = Driver.get_by_chat_id(chat_id=query.from_user.id)
    order = Order.objects.filter(pk=int(data[1])).first()
    if data[0] == 'Reject_order':
        query.edit_message_text(client_decline)
        driver.driver_status = Driver.ACTIVE
        driver.save()
        ParkStatus.objects.create(driver=driver, status=Driver.ACTIVE)

        context.bot.edit_message_reply_markup(chat_id=order.chat_id_client,
                                              message_id=order.client_message_id,
                                              reply_markup=None)
        text_to_client(order, driver_cancel)
        order.status_order, order.driver, order.checked = Order.WAITING, None, False
        order.save()
    elif data[0] == "Client_on_site":
        try:
            context.bot.delete_message(order.chat_id_client, message_id=data[2])
            context.bot.delete_message(order.chat_id_client, message_id=int(data[2])-1)
        except:
            pass
        if not context.user_data.get('recheck'):
            ParkStatus.objects.create(driver=driver,
                                      status=Driver.WITH_CLIENT)
        message = order_info(order.id,
                             order.from_address,
                             order.to_the_address,
                             order.payment_method,
                             order.phone_number,
                             order.sum,
                             order.distance_google)
        query.edit_message_text(text=message)

        reply_markup = inline_finish_order(order.to_latitude,
                                           order.to_longitude,
                                           pk=order.id)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "End_trip":
        reply_markup = inline_route_keyboard(order.id)
        query.edit_message_text(text=route_trip_text)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] in ("Along_the_route", "Off_route"):
        context.user_data['recheck'] = data[0]
        message = order_info(order.id,
                             order.from_address,
                             order.to_the_address,
                             order.payment_method,
                             order.phone_number,
                             order.sum,
                             order.distance_google)
        query.edit_message_text(text=message)
        query.edit_message_reply_markup(reply_markup=inline_repeat_keyboard(order.id))
    elif data[0] == "Accept":
        ParkStatus.objects.create(driver=order.driver,
                                  status=Driver.ACTIVE)
        if context.user_data['recheck'] == "Off_route":
            query.edit_message_text(text=calc_price_text)
            record = UseOfCars.objects.filter(user_vehicle=driver,
                                              created_at__date=timezone.now().date(), end_at=None).last()
            vehicle = Vehicle.objects.filter(licence_plate=record.licence_plate).first()
            status_driver = ParkStatus.objects.filter(driver=driver, status=Driver.WITH_CLIENT).first()
            s, e = int(timezone.localtime(status_driver.created_at).timestamp()), int(timezone.localtime().timestamp())
            get_distance_trip.delay(data[1], query.message.message_id, s, e, vehicle.gps_id)
        else:
            context.user_data.clear()
            if order.payment_method == price_inline_buttons[4].split()[1]:
                message = driver_complete_text(order.sum)
                query.edit_message_text(text=message)
                text_to_client(order, complete_order_text, button=inline_comment_for_client())
                order.status_order = Order.COMPLETED
                order.partner = order.driver.partner
                order.save()
            else:
                json = {
                    'order_id': str(order.pk),
                    'payment_description': payment_description,
                }

                portmone = Portmone(order.sum, **json)
                payment_link = portmone.create_link()
                query.edit_message_text(text=payment_title)
                query.edit_message_reply_markup(reply_markup=inline_payment_card(payment_link))
                check_payment_status_tg.delay(data[1], query.message.message_id, portmone)

