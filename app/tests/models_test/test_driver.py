import pytest
from app.models import Driver


# Check write data to Driver model
@pytest.mark.django_db
@pytest.mark.parametrize('full_name', ['Олександр Холін', 'Анатолій Мухін',
                              'Сергій Желамський', 'Олег Філіппов',
                              'Юрій Філіппов', 'Володимир Золотніков'])
def test_drivers_create(full_name):

    driver = Driver.objects.create(full_name=full_name)
    assert driver.full_name == full_name
    assert Driver.objects.count() == 1


# Checks get_driver_external_id() from Driver model:
@pytest.mark.django_db
@pytest.mark.parametrize("full_name, vendor, id",
                         [('Олександр Холін', 'Uber', '775f8943-b0ca-4079-90d3-c81d6563d0f1'),
                          ('Олександр Холін', 'Bolt', '+380661891408'),
                          ('Олександр Холін', 'Uklon', '372353')])
def test_get_driver_external_id(full_name, vendor, id):
    if Driver.objects.filter(full_name=full_name).exists():
        driver = Driver.objects.get(full_name=full_name)
        driver.get_driver_external_id(vendor) == id


# Checks get_rate() from Driver model:
@pytest.mark.django_db
@pytest.mark.parametrize("full_name, vendor, rate",
                         [('Олександр Холін', 'Uber', '0.50'),
                          ('Олександр Холін', 'Bolt', '0.50'),
                          ('Олександр Холін', 'Uklon', '0.50')])
def test_get_rate(full_name, vendor, rate):
    if Driver.objects.filter(full_name=full_name).exists():
        driver = Driver.objects.get(full_name=full_name)
        driver.get_rate(vendor) == rate
        

@pytest.mark.usefixtures('populate_db')
class TestDriverMethods:

    @pytest.mark.django_db
    def test_get_kassa(self, populate_db):
        assert populate_db.driver.get_kassa(vendor='Uber', week_number='2022-11-18') == 4500
