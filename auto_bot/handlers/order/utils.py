import os

import requests

from app.models import ParkSettings
from scripts.conversion import get_addresses_by_radius


def buttons_addresses(address):
    center_lat, center_lng = f"{ParkSettings.get_value('CENTRE_CITY_LAT')}", f"{ParkSettings.get_value('CENTRE_CITY_LNG')}"
    center_radius = int(f"{ParkSettings.get_value('CENTRE_CITY_RADIUS')}")
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng, center_radius, os.environ["GOOGLE_API_KEY"])
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def text_to_client(context,order,text):
    if order.chat_id_client:
        context.bot.send_message(chat_id=order.chat_id_client, text=text)
    else:
        params = {
            "recipient": order.phone_number[1:],
            "text": text,
            "apiKey": os.environ['MOBIZON_API_KEY'],
            "output": "json"
        }
        requests.post(os.environ['MOBIZON_DOMAIN'], params=params)