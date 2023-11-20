import pytest

from app.models import Fleet, Driver, Fleets_drivers_vehicles_rate, DriverRateLevels, Vehicle
from scripts.initmodels import init_models, DRIVERS_MAP


@pytest.mark.django_db
def test_init():
    init_models()
    assert Fleet.objects.count() == len(DRIVERS_MAP['fleets'])
    assert Driver.objects.count() == len(DRIVERS_MAP['drivers'])
    assert Vehicle.objects.count() == len(DRIVERS_MAP['drivers'])
    assert Fleets_drivers_vehicles_rate.objects.count() == sum([len(x['fleets_drivers_vehicles_rate']) for x in DRIVERS_MAP['drivers']])
    assert DriverRateLevels.objects.count() == len(DRIVERS_MAP['driver_rate_levels'])
