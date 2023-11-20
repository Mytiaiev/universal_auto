import pytest
from app.models import Vehicle


# Check write data to Vehicle model
@pytest.mark.django_db
@pytest.mark.parametrize('name, licence_plate, vin_code',
                         [('Lamborgini', 'АА 0880 ВР', 'JH4DA9340LS003571'),
                          ('Acura', 'АА 1881 ВР', 'JH4CC2642RC001364'),
                          ('Chevrolet', 'АА 2882 ВР', '1GNDS13S132266223'),
                          ('Cadillac', 'АА 3883 ВР', '1G6CD6988G4334344'),
                          ('Audi', 'АА 4885 ВР', 'WAULFAFR3DA006959'),
                          ('Chrysler', 'АА 5885 ВР', '3C8FY68B72T322831')])
def test_vehicles_create(name, licence_plate, vin_code):
    vehicle = Vehicle.objects.create(name=name,
                                     licence_plate=licence_plate,
                                     vin_code=vin_code)
    assert vehicle.name == name
    assert vehicle.licence_plate == licence_plate
    assert vehicle.vin_code == vin_code
    assert Vehicle.objects.count() == 1
