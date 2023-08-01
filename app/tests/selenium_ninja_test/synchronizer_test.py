import pytest
import datetime
from app.models import Fleet, Fleets_drivers_vehicles_rate, Driver, Vehicle, Role, JobApplication
from selenium_ninja.synchronizer import Synchronizer


@pytest.fixture
def synchronizer():
    return Synchronizer(123, 'Uklon')


def test_r_dup_without_dup():
    # Arrange
    text_without_dup = 'Some Text Without DUP'
    synchronizer = Synchronizer(123, 'Uklon')

    # Act
    result = synchronizer.r_dup(text_without_dup)

    # Assert
    assert result == 'Some Text Without DUP'


def test_parameters(synchronizer):
    # Act
    result = synchronizer.parameters()

    # Assert
    assert isinstance(result, dict)
    assert result == {'limit': '50', 'offset': '0'}


def test_get_drivers_table_not_implemented(synchronizer):
    # Act & Assert
    with pytest.raises(NotImplementedError):
        synchronizer.get_drivers_table()


def test_get_vehicles_not_implemented(synchronizer):
    # Act & Assert
    with pytest.raises(NotImplementedError):
        synchronizer.get_vehicles()


def test_create_driver(synchronizer):
    # Arrange
    fleet_name = 'Fleet1'
    driver_external_id = '12345'
    pay_cash = True
    name = 'John'
    second_name = 'Doe'
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    kwargs = {
        'fleet_name': fleet_name,
        'driver_external_id': driver_external_id,
        'pay_cash': pay_cash,
        'name': name,
        'second_name': second_name,
        'phone_number': phone_number,
        'email': email,
    }

    # Act
    synchronizer.create_driver(**kwargs)

    # Assert
    fleet = Fleet.objects.get(name=fleet_name)
    driver = Driver.objects.get(name=name, second_name=second_name, partner=123)
    vehicle = Vehicle.objects.get(licence_plate=driver_external_id, partner=123)
    fleets_drivers_vehicles_rate = Fleets_drivers_vehicles_rate.objects.get(
        fleet=fleet, driver_external_id=driver_external_id, partner=123)
    assert fleets_drivers_vehicles_rate.driver == driver
    assert fleets_drivers_vehicles_rate.vehicle == vehicle
    assert fleets_drivers_vehicles_rate.pay_cash == pay_cash


def test_get_or_create_driver(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    kwargs = {
        'name': name,
        'second_name': second_name,
        'phone_number': phone_number,
        'email': email,
    }

    # Act
    driver = synchronizer.get_or_create_driver(**kwargs)

    # Assert
    assert isinstance(driver, Driver)
    assert driver.name == name
    assert driver.second_name == second_name
    assert driver.phone_number == phone_number
    assert driver.email == email
    assert driver.partner_id == 123


def test_get_or_create_vehicle(synchronizer):
    # Arrange
    licence_plate = 'ABC123'
    vehicle_name = 'Car1'
    vin_code = 'XYZ789'
    kwargs = {
        'licence_plate': licence_plate,
        'vehicle_name': vehicle_name,
        'vin_code': vin_code,
    }

    # Act
    vehicle = synchronizer.get_or_create_vehicle(**kwargs)

    # Assert
    assert isinstance(vehicle, Vehicle)
    assert vehicle.licence_plate == licence_plate
    assert vehicle.name == vehicle_name.upper()
    assert vehicle.vin_code == vin_code
    assert vehicle.partner_id == 123


def test_update_driver_fields_with_phone(synchronizer):
    # Arrange
    phone_number = '+1234567890'
    driver = Driver.objects.create(name='John', second_name='Doe', partner_id=123)

    # Act
    synchronizer.update_driver_fields(driver, phone_number=phone_number)

    # Assert
    updated_driver = Driver.objects.get(pk=driver.pk)
    assert updated_driver.phone_number == phone_number


def test_update_driver_fields_with_email(synchronizer):
    # Arrange
    email = 'john.doe@example.com'
    driver = Driver.objects.create(name='John', second_name='Doe', partner_id=123)

    # Act
    synchronizer.update_driver_fields(driver, email=email)

    # Assert
    updated_driver = Driver.objects.get(pk=driver.pk)
    assert updated_driver.email == email


def test_update_vehicle_fields_with_vehicle_name(synchronizer):
    # Arrange
    vehicle_name = 'Car1'
    vehicle = Vehicle.objects.create(licence_plate='ABC123', partner_id=123)

    # Act
    synchronizer.update_vehicle_fields(vehicle, vehicle_name=vehicle_name)

    # Assert
    updated_vehicle = Vehicle.objects.get(pk=vehicle.pk)
    assert updated_vehicle.name == vehicle_name.upper()


def test_update_vehicle_fields_with_vin_code(synchronizer):
    # Arrange
    vin_code = 'XYZ789'
    vehicle = Vehicle.objects.create(licence_plate='ABC123', partner_id=123)

    # Act
    synchronizer.update_vehicle_fields(vehicle, vin_code=vin_code)

    # Assert
    updated_vehicle = Vehicle.objects.get(pk=vehicle.pk)
    assert updated_vehicle.vin_code == vin_code


def test_update_vehicle_fields_with_no_changes(synchronizer):
    # Arrange
    vehicle = Vehicle.objects.create(licence_plate='ABC123', partner_id=123)

    # Act
    synchronizer.update_vehicle_fields(vehicle)

    # Assert
    updated_vehicle = Vehicle.objects.get(pk=vehicle.pk)
    assert updated_vehicle.name == 'ABC123'
    assert updated_vehicle.vin_code == ''


def test_start_report_interval(synchronizer):
    # Arrange
    day = datetime.date(2023, 4, 25)

    # Act
    result = synchronizer.start_report_interval(day)

    # Assert
    assert result == datetime.datetime(2023, 4, 25, 0, 0)


def test_end_report_interval(synchronizer):
    # Arrange
    day = datetime.date(2023, 4, 25)

    # Act
    result = synchronizer.end_report_interval(day)

    # Assert
    assert result == datetime.datetime(2023, 4, 25, 23, 59, 59)


def test_r_dup_with_dup(synchronizer):
    # Arrange
    text_with_dup = 'Some Text With DUP'

    # Act
    result = synchronizer.r_dup(text_with_dup)

    # Assert
    assert result == 'Some Text With'


def test_get_driver_by_name_with_exact_match(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123
    driver = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_name(name, second_name, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_name_with_multiple_matches(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123
    driver1 = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)
    driver2 = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)

    # Act & Assert
    with pytest.raises(Driver.MultipleObjectsReturned):
        synchronizer.get_driver_by_name(name, second_name, partner_id)


def test_get_driver_by_name_with_no_matches(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123

    # Act & Assert
    with pytest.raises(Driver.DoesNotExist):
        synchronizer.get_driver_by_name(name, second_name, partner_id)


def test_get_driver_by_phone_or_email_with_phone_number(synchronizer):
    # Arrange
    phone_number = '+1234567890'
    partner_id = 123
    driver = Driver.objects.create(phone_number=phone_number, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_phone_or_email(phone_number, None, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_phone_or_email_with_email(synchronizer):
    # Arrange
    email = 'john.doe@example.com'
    partner_id = 123
    driver = Driver.objects.create(email=email, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_phone_or_email(None, email, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_phone_or_email_with_multiple_matches(synchronizer):
    # Arrange
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    partner_id = 123
    driver1 = Driver.objects.create(phone_number=phone_number, partner_id=partner_id)
    driver2 = Driver.objects.create(email=email, partner_id=partner_id)

    # Act & Assert
    with pytest.raises(Driver.MultipleObjectsReturned):
        synchronizer.get_driver_by_phone_or_email(phone_number, email, partner_id)


def test_get_or_create_driver_with_multiple_attempts(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    partner_id = 123

    # Act
    driver = synchronizer.get_or_create_driver(name=name, second_name=second_name, phone_number=phone_number,
                                               email=email)

    # Assert
    assert isinstance(driver, Driver)
    assert driver.name == name
    assert driver.second_name == second_name
    assert driver.phone_number == phone_number
    assert driver.email == email
    assert driver.partner_id == partner_id


def test_start_report_interval(synchronizer):
    # Arrange
    day = datetime.date(2023, 4, 25)

    # Act
    result = synchronizer.start_report_interval(day)

    # Assert
    assert result == datetime.datetime(2023, 4, 25, 0, 0)


def test_end_report_interval(synchronizer):
    # Arrange
    day = datetime.date(2023, 4, 25)

    # Act
    result = synchronizer.end_report_interval(day)

    # Assert
    assert result == datetime.datetime(2023, 4, 25, 23, 59, 59)


def test_r_dup_with_dup(synchronizer):
    # Arrange
    text_with_dup = 'Some Text With DUP'

    # Act
    result = synchronizer.r_dup(text_with_dup)

    # Assert
    assert result == 'Some Text With'


def test_get_driver_by_name_with_exact_match(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123
    driver = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_name(name, second_name, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_name_with_multiple_matches(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123
    driver1 = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)
    driver2 = Driver.objects.create(name=name, second_name=second_name, partner_id=partner_id)

    # Act & Assert
    with pytest.raises(Driver.MultipleObjectsReturned):
        synchronizer.get_driver_by_name(name, second_name, partner_id)


def test_get_driver_by_name_with_no_matches(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    partner_id = 123

    # Act & Assert
    with pytest.raises(Driver.DoesNotExist):
        synchronizer.get_driver_by_name(name, second_name, partner_id)


def test_get_driver_by_phone_or_email_with_phone_number(synchronizer):
    # Arrange
    phone_number = '+1234567890'
    partner_id = 123
    driver = Driver.objects.create(phone_number=phone_number, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_phone_or_email(phone_number, None, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_phone_or_email_with_email(synchronizer):
    # Arrange
    email = 'john.doe@example.com'
    partner_id = 123
    driver = Driver.objects.create(email=email, partner_id=partner_id)

    # Act
    result = synchronizer.get_driver_by_phone_or_email(None, email, partner_id)

    # Assert
    assert result == driver


def test_get_driver_by_phone_or_email_with_multiple_matches(synchronizer):
    # Arrange
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    partner_id = 123
    driver1 = Driver.objects.create(phone_number=phone_number, partner_id=partner_id)
    driver2 = Driver.objects.create(email=email, partner_id=partner_id)

    # Act & Assert
    with pytest.raises(Driver.MultipleObjectsReturned):
        synchronizer.get_driver_by_phone_or_email(phone_number, email, partner_id)


def test_get_or_create_driver_with_multiple_attempts(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    partner_id = 123
    driver1 = Driver.objects.create(name=name, second_name=second_name, phone_number=phone_number, partner_id=partner_id)

    # Act
    driver = synchronizer.get_or_create_driver(name=name, second_name=second_name, phone_number=phone_number, email=email)

    # Assert
    assert isinstance(driver, Driver)
    assert driver == driver1


def test_get_or_create_driver_without_matches(synchronizer):
    # Arrange
    name = 'John'
    second_name = 'Doe'
    phone_number = '+1234567890'
    email = 'john.doe@example.com'
    partner_id = 123

    # Act
    driver = synchronizer.get_or_create_driver(name=name, second_name=second_name, phone_number=phone_number, email=email)

    # Assert
    assert isinstance(driver, Driver)
    assert driver.name == name
    assert driver.second_name == second_name
    assert driver.phone_number == phone_number
    assert driver.email == email
    assert driver.partner_id == partner_id


def test_synchronize(synchronizer, monkeypatch):
    # Arrange
    class MockDriver:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class MockVehicle:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    drivers = [
        {'fleet_name': 'Fleet1', 'driver_external_id': '12345', 'pay_cash': True, 'name': 'John', 'second_name': 'Doe',
         'phone_number': '+1234567890', 'email': 'john.doe@example.com'},
        {'fleet_name': 'Fleet2', 'driver_external_id': '54321', 'pay_cash': False, 'name': 'Jane', 'second_name': 'Smith',
         'phone_number': '+9876543210', 'email': 'jane.smith@example.com'}
    ]
    vehicles = [
        {'licence_plate': 'ABC123', 'vehicle_name': 'Car1', 'vin_code': 'XYZ789'},
        {'licence_plate': 'XYZ789', 'vehicle_name': 'Car2', 'vin_code': 'ABC123'}
    ]

    def mock_get_drivers_table():
        return drivers

    def mock_get_vehicles():
        return vehicles

    def mock_create_driver(**kwargs):
        return MockDriver(**kwargs)

    def mock_get_or_create_vehicle(**kwargs):
        return MockVehicle(**kwargs)

    monkeypatch.setattr(synchronizer, 'get_drivers_table', mock_get_drivers_table)
    monkeypatch.setattr(synchronizer, 'get_vehicles', mock_get_vehicles)
    monkeypatch.setattr(synchronizer, 'create_driver', mock_create_driver)
    monkeypatch.setattr(synchronizer, 'get_or_create_vehicle', mock_get_or_create_vehicle)

    # Act
    synchronizer.synchronize()

    # Assert
    assert len(MockDriver.__instances) == 2
    assert len(MockVehicle.__instances) == 2
    assert len(Fleets_drivers_vehicles_rate.objects.all()) == 2



