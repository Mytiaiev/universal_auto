import pytest
from app.models import Fleets_drivers_vehicles_rate, Fleet, Driver, Vehicle


# Check write data to Fleets_drivers_vehicles_rate model
@pytest.mark.django_db
@pytest.mark.parametrize('fleet_name, full_name, vehicle, driver_external_id, rate',
                [('Uber', 'Олександр Холін', 'Lamborgini', '775f8943-b0ca-4079-90d3-c81d6563d0f1', '0.50'),
                 ('Bolt', 'Олександр Холін', 'Lamborgini', '+380661891408', '0.50'),
                 ('Uklon', 'Олександр Холін', 'Lamborgini', '372353', '0.50'),
                 ('Uber', 'Анатолій Мухін', 'Lamborgini', '9a182345-fd18-490f-a908-94f520a9d2d1', '0.65'),
                 ('Bolt', 'Анатолій Мухін', 'Lamborgini', '+380936503350', '0.65'),
                 ('Uklon', 'Анатолій Мухін', 'Lamborgini', '362612', '0.35')])
def test_fleets_drivers_vehicles_rate_create(fleet_name, full_name, vehicle, driver_external_id, rate):
    if Fleet.objects.filter(name=fleet_name, fees='0.50').exists():
        fleet = Fleet.objects.get(name=fleet_name, fees='0.50')
    else:
        fleet = Fleet.objects.create(name=fleet_name, fees='0.50')
    if Driver.objects.filter(full_name=full_name).exists():
        driver = Driver.objects.get(full_name=full_name)
    else:
        driver = Driver.objects.create(full_name=full_name)
    if Vehicle.objects.filter(name=vehicle).exists():
        vehicle = Vehicle.objects.get(
            name=vehicle,
            licence_plate='АА 0880 ВР',
            vin_code='JH4DA9340LS003571')
    else:
        vehicle = Vehicle.objects.create(
            name=vehicle,
            licence_plate='АА 0880 ВР',
            vin_code='JH4DA9340LS003571')

    fleets_drivers_vehicles = Fleets_drivers_vehicles_rate.objects.create(
        fleet=fleet,
        driver=driver,
        vehicle=vehicle,
        driver_external_id=driver_external_id,
        rate=rate)

    assert fleets_drivers_vehicles.fleet == fleet
    assert fleets_drivers_vehicles.driver == driver
    assert fleets_drivers_vehicles.vehicle == vehicle
    assert fleets_drivers_vehicles.driver_external_id == driver_external_id
    assert fleets_drivers_vehicles.rate == rate
    assert Fleets_drivers_vehicles_rate.objects.count() == 1
