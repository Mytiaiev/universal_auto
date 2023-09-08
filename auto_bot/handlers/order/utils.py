import json

import requests
from django.db.models import Q
from django.utils import timezone
from telegram.error import BadRequest

from app.models import ParkSettings, DriverReshuffle
from auto_bot.main import bot
from scripts.conversion import get_addresses_by_radius
from scripts.redis_conn import redis_instance


def validate_text(text):
    if len(text) < 200:
        return True


def check_reshuffle(driver, date=timezone.localtime().date()):
    reshuffle = DriverReshuffle.objects.filter(Q(swap_time__date=date) &
                                               (Q(driver_start=driver) | Q(driver_finish=driver))).first()
    vehicle = reshuffle.swap_vehicle if reshuffle else driver.vehicle
    return vehicle, reshuffle

def buttons_addresses(address):
    center_lat, center_lng = ParkSettings.get_value('CENTRE_CITY_LAT'), ParkSettings.get_value('CENTRE_CITY_LNG')
    center_radius = int(ParkSettings.get_value('CENTRE_CITY_RADIUS'))
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng,
                                             center_radius, ParkSettings.get_value('GOOGLE_API_KEY'))
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def get_geocoding_address(chat_id: str, addresses_key: str, address_key: str):
    addresses_list = redis_instance().hget(chat_id, addresses_key)
    address = redis_instance().hget(chat_id, address_key)
    value_dict = json.loads(addresses_list)
    place_id = value_dict.get(address)
    params = {"placeid": place_id, "language": "uk",
              "key": ParkSettings.get_value('GOOGLE_API_KEY')}
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    response = requests.get(url, params=params).json()

    if response['status'] == 'OK':
        result = response['result']
        latitude = result['geometry']['location']['lat']
        longitude = result['geometry']['location']['lng']
        return str(latitude)[:10], str(longitude)[:10]
    else:
        return None


def save_location_to_redis(chat_id):
    if not redis_instance().hexists(chat_id, 'from_address'):
        location_address = redis_instance().hget(chat_id, 'location_address')
        redis_instance().hset(chat_id, 'from_address', location_address)
    else:
        result = get_geocoding_address(chat_id, 'addresses_first', 'from_address')
        data_ = {
            'latitude': result[0],
            'longitude': result[1]
        }
        redis_instance().hmset(chat_id, data_)


def text_to_client(order=None, text=None, button=None, delete_id=None, message_id=None):
    if order.chat_id_client:
        if delete_id:
            try:
                bot.edit_message_reply_markup(chat_id=order.chat_id_client, message_id=delete_id, reply_markup=None)
            except BadRequest:
                pass
        if message_id:
            bot.edit_message_text(chat_id=order.chat_id_client, text=text, reply_markup=button, message_id=message_id)
        else:
            message = bot.send_message(chat_id=order.chat_id_client, text=text, reply_markup=button)
            message_id = message.message_id
    else:
        params = {
            "recipient": order.phone_number[1:],
            "text": text,
            "apiKey": ParkSettings.get_value('MOBIZON_API_KEY'),
            "output": "json"
        }
        requests.post(ParkSettings.get_value('MOBIZON_DOMAIN'), params=params)
    return message_id
