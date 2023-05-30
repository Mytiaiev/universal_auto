from app.models import get_report
from auto.tasks import download_uber_trips

def run(*args):
    download_uber_trips.delay()



