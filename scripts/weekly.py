import os

import redis
import requests
from requests.auth import HTTPBasicAuth

from selenium_ninja.bolt_sync import BoltRequest


def run():
    bolt = BoltRequest()
    bolt.save_report('2023-06-19', '2023-06-25')

