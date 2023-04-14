from app.models import RawGPS
from auto.tasks import raw_gps_handler


def run():         # ex id= rawGPS_id
    for raw in RawGPS.objects.all():
        raw_gps_handler.delay(raw.id)