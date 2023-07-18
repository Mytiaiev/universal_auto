import json
from datetime import datetime, timedelta

import requests

from auto.tasks import get_car_efficiency, upload_db


def run(*args):
    url = 'https://fleets.uklon.com.ua/api/fleets/14f19b9d-4372-4bcf-9823-31e8fb79d080/drivers/a800321c-8a22-4ce5-bc55-b6d16ee5f1d8/restrictions'
    headers = {"Content-Type": "application/json",
               "Authorization": "Bearer ***REMOVED***"
         }
    resp = requests.put(url, headers=headers, data=json.dumps({'type': 'Cash'}))
    print(resp)