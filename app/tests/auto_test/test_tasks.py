import pytest
from asgiref.sync import async_to_sync

from app.models import RawGPS, GPS, VehicleGPS
from auto.tasks import raw_gps_handler
from scripts.async_gps_server import PackageHandler

RAW_GPS_DATA = b'#L#357073298728193;NA\r\n#D#271022;104627;5024.3779;N;03036.6892;E;0;293;100.000000;19;0.600000;NA;NA;NA;NA;prior:1:0,event_io_id:1:240,total_io:1:15,io_239:1:0,io_240:1:1,gsm:1:5,io_21:1:5,io_200:1:0,io_69:1:1,io_1:1:0,io_179:1:0,pdop:2:0.900000,io_181:1:9,io_182:1:6,pwr_ext:2:12.952000,io_66:1:12952,pwr_int:2:3.967000,io_67:1:3967,io_68:1:0,io_9:1:0,mcc:1:255,mnc:1:6,io_241:1:25506,io_16:1:479876\r\n'
ADDRESS = ('1.1.1.1', '2222')

@async_to_sync
async def run_async_process_package():
    ph = PackageHandler()
    return await ph.process_package(ADDRESS, RAW_GPS_DATA.decode('utf-8'))


@pytest.fixture(scope='session')
def populate_raw_gps(django_db_setup, django_db_blocker) :
    with django_db_blocker.unblock():
        run_async_process_package()
    return True


@pytest.mark.usefixtures('populate_db', 'populate_raw_gps')
class TestDriverMethods:

    @pytest.mark.django_db
    def test_async_gps_server_package_handler(self, populate_db, populate_raw_gps):
        assert len(RawGPS.objects.all()) == 1

    @pytest.mark.django_db
    def test_celery_raw_gps_handler(self, populate_db, populate_raw_gps):
        raw_gps_handler(RawGPS.objects.all()[0].id)
        assert len(VehicleGPS.objects.all()) == 1



