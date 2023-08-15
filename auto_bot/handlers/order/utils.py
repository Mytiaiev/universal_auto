import requests
from app.models import ParkSettings
from auto_bot.main import bot
from scripts.conversion import get_addresses_by_radius


def validate_text(text):
    if len(text) < 200:
        return True


def buttons_addresses(address):
    center_lat, center_lng = ParkSettings.get_value('CENTRE_CITY_LAT'), ParkSettings.get_value('CENTRE_CITY_LNG')
    center_radius = int(ParkSettings.get_value('CENTRE_CITY_RADIUS'))
    dict_addresses = get_addresses_by_radius(address, center_lat, center_lng,
                                             center_radius, ParkSettings.get_value('GOOGLE_API_KEY'))
    if dict_addresses is not None:
        return dict_addresses
    else:
        return None


def text_to_client(order=None, text=None, button=None, delete_id=None, message_id=None):
    if order.chat_id_client:
        if delete_id:
            bot.edit_message_reply_markup(chat_id=order.chat_id_client, message_id=delete_id, reply_markup=None)
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
