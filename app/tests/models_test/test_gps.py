import pytest
from app.models import GPS


@pytest.fixture
def test_gps(db) -> GPS:
    return GPS.objects.create(
        date_time='2022-08-29+03:00',
        lat=float(5876),
        lat_zone="N",
        lon=float(1425),
        lon_zone="W",
        speed=int(12),
        course=int(0),
        height=int(0))


def test_db(test_gps):
    assert test_gps.date_time == '2022-08-29+03:00'
    assert test_gps.lat == float(5876)
    assert test_gps.lat_zone == "N"
    assert test_gps.lon == float(1425)
    assert test_gps.lon_zone == "W"
    assert test_gps.speed == int(12)
    assert test_gps.course == int(0)
    assert test_gps.height == int(0)


def test_field_length(test_gps):
    assert len(test_gps.lat_zone) <= 1
    assert len(test_gps.lon_zone) <= 1


def test_type(test_gps):
    assert isinstance(test_gps.date_time, str)
    assert isinstance(test_gps.lat, float)
    assert isinstance(test_gps.lat_zone, str)
    assert isinstance(test_gps.lon, float)
    assert isinstance(test_gps.lon_zone, str)
    assert isinstance(test_gps.speed, int)
    assert isinstance(test_gps.course, int)
    assert isinstance(test_gps.height, int)

