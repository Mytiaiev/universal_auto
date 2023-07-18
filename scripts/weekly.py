import json
from datetime import datetime, timedelta

import requests

from auto.tasks import get_car_efficiency, upload_db


def run(*args):
    url = 'https://fleets.uklon.com.ua/api/fleets/14f19b9d-4372-4bcf-9823-31e8fb79d080/drivers/a800321c-8a22-4ce5-bc55-b6d16ee5f1d8/restrictions'
    headers = {"Content-Type": "application/json",
               "Authorization": "Bearer eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNyc2Etc2hhMzg0IiwidHlwIjoiSldUIn0.eyJqdGkiOiIzNTBmOWRkMGY3ZTM0Y2Y0YjU4NmQzNDk3MmNlM2RiNSIsInVuaXF1ZV9uYW1lIjoiMzgwNjgxMzczMzM1IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6IjM4MDY4MTM3MzMzNSIsIm5hbWVpZCI6ImE4MDAzMjFjLThhMjItNGNlNS1iYzU1LWI2ZDE2ZWU1ZjFkOCIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWVpZGVudGlmaWVyIjoiYTgwMDMyMWMtOGEyMi00Y2U1LWJjNTUtYjZkMTZlZTVmMWQ4IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbW9iaWxlcGhvbmUiOiIzODA2ODEzNzMzMzUiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9sb2NhbGl0eSI6IjEiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2dyb3Vwc2lkIjoiU3pEZ1AxalI3SXJ2b1E5VVIwM0dsWE5Ga3JIeG53djV4WFNRems3bkMrcz0iLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJUYXhpRHJpdmVyIiwibmJmIjoxNjg5NjcyODcwLCJleHAiOjE2ODk2NzY0NzAsImlhdCI6MTY4OTY3Mjg3MCwiaXNzIjoiaHR0cHM6Ly91a2xvbi5jb20udWEvIiwiYXVkIjoiaHR0cHM6Ly91a2xvbi5jb20udWEvIiwicHJvcGVydGllcyI6eyJkZXZpY2VfaWQiOiJjOGE0OThiMy1lOTQyLTQ2MGItOTA4Yy03NjQyMjg5YjFiZjkiLCJhcHBfdWlkIjoiYzhhNDk4YjMtZTk0Mi00NjBiLTkwOGMtNzY0MjI4OWIxYmY5IiwiY2xpZW50X2lkIjoiN2JmNmI2NmMyNmQ4NDA3MTk0NDJiMDljYTMzNjk3N2IifX0.m95zdCrR1cGOlE6S1C5G_YLSOIx_Oi8iE_gxSC6Y7Zo8m-wGqdxzGnssBWsRPOJL2tIWjJq6mEEqdmFreDugPyD6J352s7OStWUSY6GAyg0n-Mtq-0myQMg7cUh06yTHdlURGrN6Uo_GHu6brZjK9WIe6NkfsFE7am5R7CM7OBMCyu7jN3rOxC2uE5JxVHC4_VM4TOUFVavxMHq_puQC5eG_1baqF2TPw4R_Sm9hIBhQkzdqxEmeqU3l-wI03m8m1_gxzm0y3kxwusMhMnmmxxlqMj-gM9_OlabjOaZzjnEj8rjDBDY1J8D8ftSgg9lY9D73wm9VSVun77wjh42Wgg"
         }
    resp = requests.put(url, headers=headers, data=json.dumps({'type': 'Cash'}))
    print(resp)