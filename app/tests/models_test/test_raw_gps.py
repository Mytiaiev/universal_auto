import pytest
from app.models import RawGPS


@pytest.fixture
def test_raw_gps(db) -> RawGPS:
    return RawGPS.objects.create(
        imei='350424063413353',
        client_ip='172.19.2.9',
        client_port=int(43377),
        data='191122;182342;5026.5456;N;03038.6892;E;0;0;0.000000;0;0.000000;NA;NA;NA;NA;prior:1:0,event_io_id:1:0,total_io:1:15,io_239:1:1,io_240:1:0,gsm:1:3,io_21:1:3,io_200:1:0,io_69:1:2,io_1:1:0,io_179:1:0,pdop:2:0.000000,io_181:1:0,io_182:1:0,pwr_ext:2:14.722000,io_66:1:14722,pwr_int:2:4.057000,io_67:1:4057,io_68:1:0,io_9:1:260,mcc:1:255,mnc:1:6,io_241:1:25506,io_16:1:568065')


def test_db(test_raw_gps):
    assert test_raw_gps.imei == '350424063413353'
    assert test_raw_gps.client_ip == '172.19.2.9'
    assert test_raw_gps.client_port == int(43377)
    assert test_raw_gps.data == '191122;182342;5026.5456;N;03038.6892;E;0;0;0.000000;0;0.000000;NA;NA;NA;NA;prior:1:0,event_io_id:1:0,total_io:1:15,io_239:1:1,io_240:1:0,gsm:1:3,io_21:1:3,io_200:1:0,io_69:1:2,io_1:1:0,io_179:1:0,pdop:2:0.000000,io_181:1:0,io_182:1:0,pwr_ext:2:14.722000,io_66:1:14722,pwr_int:2:4.057000,io_67:1:4057,io_68:1:0,io_9:1:260,mcc:1:255,mnc:1:6,io_241:1:25506,io_16:1:568065'


def test_type(test_raw_gps):
    assert isinstance(test_raw_gps.imei, str)
    assert isinstance(test_raw_gps.client_ip, str)
    assert isinstance(test_raw_gps.client_port, int)
    assert isinstance(test_raw_gps.data, str)


def test_field_length(test_raw_gps):
    assert len(test_raw_gps.imei) <= 100
    assert len(test_raw_gps.client_ip) <= 100
    assert len(test_raw_gps.data) <= 1024