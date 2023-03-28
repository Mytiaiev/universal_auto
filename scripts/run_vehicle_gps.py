from app.models import RawGPS
from auto.tasks import raw_gps_handler


def run(id):         # ex id= rawGPS_id
    raw_gps_handler.delay(id)