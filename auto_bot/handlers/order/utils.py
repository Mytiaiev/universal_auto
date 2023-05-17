import os

import requests

from app.models import ParkSettings
from auto_bot.main import bot
from scripts.conversion import get_addresses_by_radius


def buttons_addresses(address):
    center_lat, center_lng = f"{ParkSettings.get_value('CENTRE_CITY_LAT')}", f"{ParkSettings.get_value('CENTRE_CITY_LNG')}"
    center_radius = int(f"{ParkSettings.get_value('CENTRE_CITY_RADIUS')}")
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng,
                                             center_radius, ParkSettings.get_value('GOOGLE_API_KEY'))
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def text_to_client(order=None, text=None, markup=None):
    if order.chat_id_client:
        bot.send_message(chat_id=order.chat_id_client, text=text, reply_markup=markup)
    else:
        params = {
            "recipient": order.phone_number[1:],
            "text": text,
            "apiKey": ParkSettings.get_value('MOBIZON_API_KEY'),
            "output": "json"
        }
        requests.post(ParkSettings.get_value('MOBIZON_DOMIAN'), params=params)