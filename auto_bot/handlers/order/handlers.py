import json
import os
import re
from datetime import datetime, timedelta
from django.utils import timezone
from telegram import ReplyKeyboardRemove,  LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from app.models import Order, Driver, ParkSettings, Client, FleetOrder, Partner, ReportTelegramPayments
from auto.tasks import get_distance_trip, send_map_to_client, order_create_task
from auto_bot.handlers.main.keyboards import markup_keyboard
from auto_bot.handlers.order.keyboards import inline_spot_keyboard, inline_route_keyboard, inline_finish_order, \
    inline_repeat_keyboard, inline_reject_order, inline_increase_price_kb, inline_search_kb, inline_start_order_kb, \
    share_location, inline_location_kb, inline_payment_kb, inline_comment_for_client, inline_choose_date_kb, \
    inline_add_info_kb, inline_change_currency_trip
from auto_bot.handlers.order.utils import buttons_addresses, text_to_client, validate_text
from auto_bot.main import bot
from scripts.conversion import get_address, get_location_from_db, geocode
from auto_bot.handlers.order.static_text import *
from scripts.redis_conn import redis_instance


def continue_order(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    order = Order.objects.filter(chat_id_client=chat_id,
                                 status_order__in=[Order.ON_TIME, Order.WAITING])
    if order:
        query.edit_message_text(already_ordered)
    else:
        redis_instance().hdel(str(chat_id), 'location_button')
        redis_instance().hset(str(chat_id), 'state', START_TIME_ORDER)
        query.edit_message_text(price_info(ParkSettings.get_value('TARIFF_IN_THE_CITY'),
                                           ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY')))
    query.edit_message_reply_markup(inline_start_order_kb())


def get_location(update, context):
    chat_id = str(update.effective_chat.id)
    if update.message:
        location = update.message.location
        data = {
            'state': 0,
            'location_button': 1,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
        redis_instance().hmset(str(chat_id), data)
        latitude = redis_instance().hget(chat_id, 'latitude')
        longitude = redis_instance().hget(chat_id, 'longitude')
        address = get_address(latitude, longitude,
                              ParkSettings.get_value('GOOGLE_API_KEY'))
        if address is not None:
            redis_instance().hset(chat_id, 'location_address', address)
            update.message.reply_text(text=f'Ваша адреса: {address}')
            # update.message.reply_text(text=f'Ваша адреса: {address}', reply_markup=ReplyKeyboardRemove())
            update.message.reply_text(text=ask_spot_text, reply_markup=inline_location_kb())
        else:
            update.message.reply_text(text=no_location_text)
            from_address(update, context)


def from_address(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    redis_instance().hset(str(chat_id), 'state', FROM_ADDRESS)
    location_button = redis_instance().hget(str(chat_id), 'location_button')
    if not location_button:
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
    state = int(redis_instance().hget(str(chat_id), 'state'))
    if state == FROM_ADDRESS:
        buttons = [[InlineKeyboardButton(f'{NOT_CORRECT_ADDRESS}', callback_data='From_address 0')], ]
        address = update.message.text
        addresses = buttons_addresses(address)
        if addresses is not None:
            for no, key in enumerate(addresses.keys(), 1):
                buttons.append([InlineKeyboardButton(key, callback_data=f'From_address {no}')])
            buttons.append([InlineKeyboardButton(order_inline_buttons[6], callback_data="Call_taxi")])
            reply_markup = InlineKeyboardMarkup(buttons)
            redis_instance().hset(str(chat_id), 'addresses_first', json.dumps(addresses))
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
        redis_instance().hset(str(chat_id), 'state', TO_THE_ADDRESS)


def payment_method(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    state = int(redis_instance().hget(str(chat_id), 'state'))
    if state == TO_THE_ADDRESS:
        address = update.message.text
        buttons = [[InlineKeyboardButton(f'{NOT_CORRECT_ADDRESS}', callback_data='To_the_address 0')], ]
        addresses = buttons_addresses(address)
        if addresses is not None:
            for no, key in enumerate(addresses.keys(), 1):
                buttons.append([InlineKeyboardButton(key, callback_data=f'To_the_address {no}')])
            buttons.append([InlineKeyboardButton(order_inline_buttons[6], callback_data="Wrong_place")])
            reply_markup = InlineKeyboardMarkup(buttons)
            redis_instance().hset(str(chat_id), 'addresses_second', json.dumps(addresses))
            context.bot.send_message(chat_id=chat_id,
                                     text=choose_to_address_text,
                                     reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=chat_id, text=wrong_address_request)
            to_the_address(update, context)
    else:
        query.edit_message_text(add_info_text)
        query.edit_message_reply_markup(inline_add_info_kb())
        redis_instance().hdel(str(chat_id), 'state')


def add_info_to_order(update, context):
    query = update.callback_query
    query.edit_message_text(ask_info_text)
    redis_instance().hset(str(update.effective_chat.id), 'state', ADD_INFO)


def get_additional_info(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    if query:
        query.edit_message_text(payment_text)
        query.edit_message_reply_markup(inline_payment_kb())
    else:
        if validate_text(update.message.text):
            redis_instance().hdel(str(update.effective_chat.id), 'state')
            redis_instance().hset(str(chat_id), 'info', update.message.text)
            context.bot.send_message(chat_id=chat_id, text=payment_text, reply_markup=inline_payment_kb())
        else:
            redis_instance().hset(str(update.effective_chat.id), 'state', ADD_INFO)
            context.bot.send_message(chat_id=chat_id, text=too_long_text)


def second_address_check(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    data = int(query.data.split(' ')[1])
    response = query.message.reply_markup.inline_keyboard[data][0].text
    if data:
        data_ = {
            'to_the_address': response,
            'state': 0
        }
        redis_instance().hmset(str(chat_id), data_)
        payment_method(update, context)
    else:
        to_the_address(update, context)


def first_address_check(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    data = int(query.data.split(' ')[1])
    response = query.message.reply_markup.inline_keyboard[data][0].text
    if data:
        data_ = {
            'from_address': response,
            'state': 0
        }
        redis_instance().hmset(str(chat_id), data_)

        to_the_address(update, context)
    else:
        from_address(update, context)


def payment_request(chat_id_client, provider_token, url, start_parameter, payload, price: int):
    prices = [LabeledPrice(label=payment_price, amount=int(price) * 100)]

    # Sending a request for payment
    bot.send_invoice(chat_id=chat_id_client,
                     title=payment_title,
                     description=payment_description,
                     payload=payload,
                     provider_token=provider_token,
                     currency=payment_currency,
                     start_parameter=start_parameter,
                     prices=prices,
                     photo_url=url,
                     need_shipping_address=False,
                     photo_width=615,
                     photo_height=512,
                     photo_size=50000,
                     is_flexible=False)


def order_create(update, context):
    query = update.callback_query
    chat_id = str(update.effective_chat.id)
    data = int(query.data.split(' ')[1])
    button_text = query.message.reply_markup.inline_keyboard[data][0].text
    payment = button_text.split(' ')[1]
    user = Client.get_by_chat_id(update.effective_chat.id)
    query.edit_message_text(creating_order_text)
    redis_instance().hset(chat_id, 'client_msg', query.message.message_id)
    if not redis_instance().hexists(chat_id, 'from_address'):
        location_address = redis_instance().hget(chat_id, 'location_address')
        redis_instance().hset(chat_id, 'from_address', location_address)
    else:
        addresses_first = redis_instance().hget(chat_id, 'addresses_first')
        from_address = redis_instance().hget(chat_id, 'from_address')
        value_dict = json.loads(addresses_first)
        from_place = value_dict.get(from_address)
        result = geocode(from_place, ParkSettings.get_value('GOOGLE_API_KEY'))
        data_ = {
            'latitude': result[0],
            'longitude': result[1]
        }
        redis_instance().hmset(chat_id, data_)

    addresses_second = redis_instance().hget(chat_id, 'addresses_second')
    to_the_address = redis_instance().hget(chat_id, 'to_the_address')
    value_dict = json.loads(addresses_second)
    destination_place = value_dict.get(to_the_address)
    destination_lat, destination_long = geocode(destination_place, ParkSettings.get_value('GOOGLE_API_KEY'))

    order_data = {
        'from_address': redis_instance().hget(chat_id, 'from_address'),
        'latitude': redis_instance().hget(chat_id, 'latitude'),
        'longitude': redis_instance().hget(chat_id, 'longitude'),
        'to_the_address': to_the_address,
        'to_latitude': destination_lat,
        'to_longitude': destination_long,
        'phone_number': user.phone_number,
        'chat_id_client': user.chat_id,
        'payment_method': payment,
    }
    if redis_instance().hexists(chat_id, 'info'):
        order_data.update({'info': redis_instance().hget(chat_id, 'info')}),
    if not redis_instance().hexists(chat_id, 'time_order'):
        order_data['status_order'] = Order.WAITING
    else:
        order_data['status_order'] = Order.ON_TIME
        order_time = redis_instance().hget(chat_id, 'time_order')
        order_data['order_time'] = datetime.fromisoformat(order_time)
    order_create_task.delay(order_data)


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
    query.edit_message_text(update_text)
    chat_id = query.from_user.id
    order = Order.objects.filter(chat_id_client=chat_id,
                                 status_order=Order.WAITING).last()
    if query.data != "Continue_search":
        order.car_delivery_price += int(query.data)
        order.sum += int(query.data)
    order.checked = False
    order.save()


def choose_date_order(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    # order = Order.objects.filter(chat_id_client=chat_id,
    #                              status_order__in=[Order.ON_TIME, Order.WAITING])
    # if order:
    #     query.edit_message_text(order_not_payment)
    # else:
    query.edit_message_text(order_date_text)
    query.edit_message_reply_markup(inline_choose_date_kb())


def time_order(update, context):
    query = update.callback_query
    chat_id = str(update.effective_chat.id)
    if query.data in ("Today_order", "Tomorrow_order"):
        redis_instance().hset(chat_id, 'time_order', query.data)
    redis_instance().hset(chat_id, 'state', TIME_ORDER)
    query.edit_message_text(text=ask_time_text)


def order_on_time(update, context):
    chat_id = str(update.message.chat.id)
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    user_time, user = update.message.text, Client.get_by_chat_id(chat_id)
    if re.match(pattern, user_time):
        format_time = timezone.datetime.strptime(user_time, '%H:%M').time()
        if redis_instance().hget(chat_id, 'time_order') == "Tomorrow_order":
            tomorrow = datetime.now() + timedelta(days=1)
            order_time = datetime.combine(tomorrow.date(), format_time)
        else:
            order_time = datetime.combine(datetime.now().date(), format_time)
        time_difference = order_time - datetime.now()
        if time_difference.total_seconds() / 60 > int(ParkSettings.get_value('TIME_ORDER_MIN', 60)):
            redis_instance().hdel(chat_id, 'state')
            if not redis_instance().hexists(chat_id, 'time_order'):
                order = Order.objects.filter(chat_id_client=user.chat_id,
                                             status_order=Order.WAITING).last()
                order.status_order, order.order_time, order.checked = Order.ON_TIME, order_time, False
                order.save()
                update.message.reply_text(order_complete)
            else:
                redis_instance().hset(chat_id, 'time_order', timezone.make_aware(order_time).isoformat())
                from_address(update, context)
        else:
            update.message.reply_text(small_time_delta(timezone.localtime(),
                                                       int(ParkSettings.get_value('TIME_ORDER_MIN')) + 5))
            redis_instance().hset(chat_id, 'state', TIME_ORDER)
    else:
        update.message.reply_text(wrong_time_format)
        redis_instance().hset(chat_id, 'state', TIME_ORDER)


def client_reject_order(update, context):
    query = update.callback_query
    order = Order.objects.filter(pk=int(query.data.split(' ')[1])).first()
    if order.driver:
        FleetOrder.objects.create(order_id=order.pk, driver=order.driver,
                                  from_address=order.from_address, destination=order.to_the_address,
                                  accepted_time=order.accepted_time, finish_time=timezone.localtime(),
                                  state=FleetOrder.CLIENT_CANCEL,
                                  partner=order.driver.partner,
                                  fleet='Ninja')

        driver_msg = redis_instance().hget(str(order.driver.chat_id), 'driver_msg')
        bot.delete_message(chat_id=order.driver.chat_id, message_id=driver_msg)
        bot.send_message(
            chat_id=order.driver.chat_id,
            text=f'Вибачте, замовлення за адресою {order.from_address} відхилено клієнтом.'
        )
    else:
        try:
            group_msg = redis_instance().hget('group_msg', order.pk)
            context.bot.delete_message(chat_id=ParkSettings.get_value('ORDER_CHAT'),
                                       message_id=group_msg)
            redis_instance().hdel('group_msg', order.pk)
        except:
            pass
    order.status_order = Order.CANCELED
    order.finish_time = timezone.localtime()
    order.save()
    try:
        for i in range(3):
            context.bot.delete_message(chat_id=order.chat_id_client,
                                       message_id=query.message.message_id + i)
    except:
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
    if order.status_order == Order.ON_TIME:
        if driver.vehicle:
            order.driver = driver
            order.save()
            group_msg = redis_instance().hget('group_msg', order.pk)
            context.bot.delete_message(chat_id=ParkSettings.get_value('ORDER_CHAT'),
                                       message_id=group_msg)
            redis_instance().hdel('group_msg', order.pk)
            send = context.bot.send_message(chat_id=driver.chat_id,
                                            text=time_order_accepted(order.from_address,
                                                 timezone.localtime(order.order_time).time()))
            redis_instance().hset(str(query.from_user.id), 'driver_msg', send.message_id)

            if order.payment_method == price_inline_buttons[5].split()[1]:
                bot.send_message(chat_id=order.chat_id_client,
                                 text=accept_order(order.sum))
                payment_request(order.chat_id_client,
                                os.environ["PAYMENT_TOKEN"],
                                os.environ["BOT_URL_IMAGE_TAXI"],
                                order.pk,
                                order.pk,
                                order.sum)

                redis_instance().hset(order.chat_id_client, 'first_payment', 1)
        else:
            context.bot.send_message(chat_id=query.from_user.id, text=add_many_auto_text)
    else:
        order.driver = driver
        order.save()
        markup = inline_spot_keyboard(order.latitude, order.longitude, pk=order.id)
        query.edit_message_text(text=order_info(order))
        query.edit_message_reply_markup(reply_markup=markup)
        report_for_client = client_order_text(driver, driver.vehicle.name, driver.vehicle.licence_plate,
                                              driver.phone_number, order.sum)
        client_msg = redis_instance().hget(str(order.chat_id_client), 'client_msg')
        text_to_client(order, report_for_client, button=inline_reject_order(order.pk), message_id=client_msg)
        redis_instance().hset(str(query.from_user.id), 'driver_msg', query.message.message_id)
        order.status_order, order.accepted_time = Order.IN_PROGRESS, timezone.localtime()
        order.save()
        if order.chat_id_client:
            lat, long = get_location_from_db(driver.vehicle.licence_plate)
            bot.send_message(chat_id=order.chat_id_client, text=order_customer_text)
            message = bot.sendLocation(order.chat_id_client, latitude=lat, longitude=long, live_period=1800)
            send_map_to_client.delay(order.id, driver.vehicle.licence_plate, message.message_id, message.chat_id)


def fleet_order(instance, state=FleetOrder.COMPLETED):
    FleetOrder.objects.create(order_id=instance.pk, driver=instance.driver,
                              from_address=instance.from_address, destination=instance.to_the_address,
                              accepted_time=instance.accepted_time, finish_time=timezone.localtime(),
                              state=state,
                              partner=instance.driver.partner,
                              fleet='Ninja')


def cash_order(update, query, order):
    query.edit_message_text(driver_complete_text(order.sum))
    text_to_client(order, complete_order_text, button=inline_comment_for_client())
    order.status_order = Order.COMPLETED
    order.partner = order.driver.partner
    order.save()
    fleet_order(order)
    redis_instance().delete(str(update.effective_chat.id))


def handle_order(update, context):
    query = update.callback_query
    data = query.data.split(' ')
    chat_id = str(update.effective_chat.id)
    driver = Driver.get_by_chat_id(chat_id=query.from_user.id)
    order = Order.objects.filter(pk=int(data[1])).first()
    if data[0] == 'Reject_order':
        query.edit_message_text(client_decline)
        client_msg = redis_instance().hget(order.chat_id_client, 'client_msg')
        context.bot.edit_message_reply_markup(chat_id=order.chat_id_client,
                                              message_id=client_msg,
                                              reply_markup=None)
        fleet_order(order, FleetOrder.DRIVER_CANCEL)
        text_to_client(order, driver_cancel)
        order.status_order, order.driver, order.checked = Order.WAITING, None, False
        order.save()

    elif data[0] == "Client_on_site":
        try:
            context.bot.delete_message(order.chat_id_client, message_id=data[2])
            context.bot.delete_message(order.chat_id_client, message_id=int(data[2])-1)
        except:
            pass
        query.edit_message_text(order_info(order))

        reply_markup = inline_finish_order(order.to_latitude,
                                           order.to_longitude,
                                           pk=order.id)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] == "End_trip":
        reply_markup = inline_route_keyboard(order.id)
        query.edit_message_text(text=route_trip_text)
        query.edit_message_reply_markup(reply_markup=reply_markup)
    elif data[0] in ("Along_the_route", "Off_route"):
        redis_instance().hset(chat_id, 'recheck', data[0])
        query.edit_message_text(order_info(order))
        query.edit_message_reply_markup(reply_markup=inline_repeat_keyboard(order.id))
    elif data[0] == "Accept":
        if redis_instance().hget(chat_id, 'recheck') == "Off_route":
            query.edit_message_text(text=calc_price_text)
            start_route = redis_instance().hget(chat_id, 'start_route')
            s, e = int(start_route), int(timezone.localtime().timestamp())
            get_distance_trip.delay(data[1], query.message.message_id, s, e, driver.vehicle.gps_id)
        else:
            if order.payment_method == price_inline_buttons[4].split()[1]:
                cash_order(update, query, order)
            else:
                second_payment = bool(redis_instance().hget(chat_id, 'second_payment'))
                if second_payment:
                    query.edit_message_reply_markup(reply_markup=inline_change_currency_trip(order.pk))
                    first_sum = int(redis_instance().hget(chat_id, 'first_sum'))
                    sum = order.sum - first_sum
                    payment_request(order.chat_id_client,
                                    os.environ["PAYMENT_TOKEN"],
                                    os.environ["BOT_URL_IMAGE_TAXI"],
                                    order.pk,
                                    f'{order.pk} {query.message.message_id}',
                                    sum)
                else:
                    context.bot.edit_message_text(chat_id=order.driver.chat_id, text=end_trip)
                    text_to_client(order, complete_order_text, button=inline_comment_for_client())
                    order.status_order = Order.COMPLETED
                    order.partner = order.driver.partner
                    order.save()
                    fleet_order(order)
                    redis_instance().delete(chat_id)

    elif data[0] == "Change_payments":
        order.payment_method = price_inline_buttons[4].split()[1]
        order.save()
        bot.send_message(chat_id=order.driver.manager.chat_id, text=manager_change_payments_info(order))
        cash_order(update, query, order)


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    chat_id = query.from_user.id
    if redis_instance().hexists(str(chat_id), 'first_payment'):
        query.answer(ok=True)
    else:
        data = query.invoice_payload.split()
        order = Order.objects.filter(chat_id_client=chat_id).last()
        redis_instance().hset(chat_id, 'message_data', data[1])
        if data[0] == f'{order.pk}':
            query.answer(ok=True)
        else:
            query.answer(ok=False, error_message=error_payment)


def successful_payment(update, context):
    chat_id = str(update.message.chat.id)
    successful_payment = update.message.successful_payment
    order = Order.objects.get(chat_id_client=chat_id).last()
    if redis_instance().hexists(chat_id, 'first_payment'):
        redis_instance().hset(chat_id, 'first_payment', 0)
    else:
        data = int(redis_instance().hget(chat_id, 'message_data'))
        fleet_order(order)
        context.bot.edit_message_text(chat_id=order.driver.chat_id, message_id=data, text=trip_paymented)
        text_to_client(order, complete_order_text, button=inline_comment_for_client())

        order.status_order = Order.COMPLETED
        order.partner = order.driver.partner
        order.save()
        redis_instance().delete(chat_id)

    ReportTelegramPayments.objects.create(
        provider_payment_charge_id=successful_payment.provider_payment_charge_id,
        telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        currency=successful_payment.currency,
        total_amount=successful_payment.total_amount / 100,
        order=order)









