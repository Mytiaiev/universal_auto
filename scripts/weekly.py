import json
from datetime import datetime, timedelta

import requests

from auto.tasks import get_car_efficiency, upload_db


def run(*args):
    url = 'https://fleets.uklon.com.ua/api/fleets/14f19b9d-4372-4bcf-9823-31e8fb79d080/drivers/d33b8d3a-8991-4716-a8d6-a1505f007319/restrictions'
    headers = {"Content-Type": "application/json",
            'Authorization': f'Bearer ***REMOVED***'
         }
    resp = requests.delete(url, headers=headers, data=json.dumps({"type": "Cash"}))
    print(resp)