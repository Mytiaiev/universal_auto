import secrets

import requests
from app.models import Service
from selenium_ninja.uklon_sync import UklonRequest


def run(*args):
    # hex_length = 16  # For a 128-bit hexadecimal value
    # random_hex = secrets.token_hex(hex_length)
    # print(random_hex)
    # payload = {
    #     "client_id": f"{random_hex}",
    #     "contact": "+380681373335",
    #     "device_id": "38c13dc5-2ef3-4637-99f5-8de26b2e8216",
    #     "grant_type": "password_mfa",
    #     "password": "***REMOVED***",
    # }
    # response = requests.post(Service.get_value('UKLON_SESSION'), json=payload)
    # print(response.json())
    print(UklonRequest(4).uklon_id())