from app.models import Fleet
from app.uagps_sync import UaGpsSynchronizer
from app.uklon_sync import UklonRequest


def run():

    UaGpsSynchronizer.objects.create(name="Gps", base_url="https://uagps.net/")
    # Fleet.objects.filter(name="Uklon").update(base_url="https://fleets.uklon.com.ua/api/")
    # Fleet.objects.filter(name="Bolt").update(base_url="https://fleetownerportal.live.boltsvc.net/fleetOwnerPortal/")
    # Fleet.objects.filter(name="Uber").update(base_url="https://supplier.uber.com/graphql")
