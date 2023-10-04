import os

from cryptography.fernet import Fernet
from django.core.exceptions import ObjectDoesNotExist

from selenium_ninja.uklon_sync import UklonRequest
from app.models import CredentialPartner

def run(*args):
    sett = CredentialPartner.get_value(key="CLIENT_ID", partner=1)
    key = os.environ.get("CRYPT_KEY").encode('utf-8')
    print(key)
    print(sett)
