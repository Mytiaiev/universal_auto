import pytest
from app.models import Fleet


# Check write data to Fleet model
@pytest.mark.django_db
@pytest.mark.parametrize('fleet_name, fees', [("Uber", 0.50),
                                             ("Bolt", 0.50),
                                             ("Uklon", 0.50)])
def test_fleets_create(fleet_name, fees):
    fleet = Fleet.objects.create(name=fleet_name, fees=fees)
    assert fleet.name == fleet_name
    assert fleet.fees == fees
    assert Fleet.objects.count() == 1
