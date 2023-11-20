import pytest
from app.models import ServiceStation


@pytest.fixture
def test_service_station(db) -> ServiceStation:
    return ServiceStation.objects.create(
        name='СТО-СЕРВІС',
        owner='Залужний П.Н.',
        lat=float(5024.3779),
        lat_zone='N',
        lon=float(03036.6892),
        lon_zone='E',
        description='Good service station in Kyiv. Founder Залужний П.Н.')


def test_db(test_service_station):
    assert test_service_station.name == 'СТО-СЕРВІС'
    assert test_service_station.owner == 'Залужний П.Н.'
    assert test_service_station.lat == float(5024.3779)
    assert test_service_station.lat_zone == 'N'
    assert test_service_station.lon == float(03036.6892)
    assert test_service_station.lon_zone == 'E'
    assert test_service_station.description == 'Good service station in Kyiv. Founder Залужний П.Н.'


def test_field_length(test_service_station):
    assert len(test_service_station.name) <= 120
    assert len(test_service_station.owner) <= 150
    assert len(test_service_station.lat_zone) <= 1
    assert len(test_service_station.lon_zone) <= 1
    assert len(test_service_station.description) <= 255


def test_type(test_service_station):
    assert isinstance(test_service_station.name, str)
    assert isinstance(test_service_station.owner, str)
    assert isinstance(test_service_station.lat, float)
    assert isinstance(test_service_station.lat_zone, str)
    assert isinstance(test_service_station.lon, float)
    assert isinstance(test_service_station.lon_zone, str)
    assert isinstance(test_service_station.description, str)


