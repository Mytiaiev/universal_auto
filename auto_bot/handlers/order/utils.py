import os
import time

import requests
from telegram import TelegramError, ReplyKeyboardRemove

from app.models import ParkSettings
from auto_bot.handlers.main.keyboards import markup_keyboard
from scripts.conversion import get_addresses_by_radius
from auto_bot.handlers.order.keyboards import inline_comment_for_client
from auto.tasks import delete_button


def buttons_addresses(address):
    center_lat, center_lng = f"{ParkSettings.get_value('CENTRE_CITY_LAT')}", f"{ParkSettings.get_value('CENTRE_CITY_LNG')}"
    center_radius = int(f"{ParkSettings.get_value('CENTRE_CITY_RADIUS')}")
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng,
                                             center_radius, ParkSettings.get_value('GOOGLE_API_KEY'))
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def text_to_client(context=None, order=None, text=None, button=None, comment=None):
    if order.chat_id_client:
        if comment is None:
            context.bot.send_message(chat_id=order.chat_id_client, text=text)
        else:
            context.bot.send_message(chat_id=order.chat_id_client, text=text,
                                     reply_markup=inline_comment_for_client())
        message = context.bot.send_message(chat_id=order.chat_id_client, text=text, reply_markup=button)
        message_id = message.message_id
        if button is not None:
            order.client_message_id = message_id
            order.save()
            delete_button.delay(order.id, message_id, text)
    else:
        params = {
            "recipient": order.phone_number[1:],
            "text": text,
            "apiKey": ParkSettings.get_value('MOBIZON_API_KEY'),
            "output": "json"
        }
        requests.post(ParkSettings.get_value('MOBIZON_DOMAIN'), params=params)