import pytest
from app.models import UklonPaymentsOrder


@pytest.fixture
def test_uklon_payments_order(db) -> UklonPaymentsOrder:
    return UklonPaymentsOrder.objects.create(
        report_from='2022-08-29+03:00',
        report_to='2022-09-05+03:00',
        report_file_name='Куцко - Income_8_29_2022 3_00_00 AM-9_5_2022 3_00_00 AM.csv',
        signal='324460',
        licence_plate='KA8443EA',
        total_rides=int(35),
        total_distance=int(435),
        total_amount_cach=float(3402),
        total_amount_cach_less=float(2612),
        total_amount=float(6014),
        total_amount_without_comission=float(1022.38),
        bonuses=float(0.0))


def test_db(test_uklon_payments_order):
    assert test_uklon_payments_order.report_from == '2022-08-29+03:00'
    assert test_uklon_payments_order.report_to == '2022-09-05+03:00'
    assert test_uklon_payments_order.report_file_name == 'Куцко - Income_8_29_2022 3_00_00 AM-9_5_2022 3_00_00 AM.csv'
    assert test_uklon_payments_order.signal == '324460'
    assert test_uklon_payments_order.licence_plate == 'KA8443EA'
    assert test_uklon_payments_order.total_rides == int(35)
    assert test_uklon_payments_order.total_distance == int(435)
    assert test_uklon_payments_order.total_amount_cach == float(3402)
    assert test_uklon_payments_order.total_amount_cach_less == float(2612)
    assert test_uklon_payments_order.total_amount == float(6014)
    assert test_uklon_payments_order.total_amount_without_comission == float(1022.38)
    assert test_uklon_payments_order.bonuses == float(0.0)


def test_filter_uklon_payments_order(test_uklon_payments_order):
    assert UklonPaymentsOrder.objects.filter(signal='324460').exists()


def test_kassa(test_uklon_payments_order):
    assert (test_uklon_payments_order.total_amount * 0.81) == 4871.34


def test_driver_id(test_uklon_payments_order):
    assert test_uklon_payments_order.signal == '324460'


def test_total_drivers_amount(test_uklon_payments_order, rate=0.35):
    assert -((test_uklon_payments_order.total_amount * 0.81) * rate) == -1704.969


def test_total_owner_amount(test_uklon_payments_order, rate=0.35):
    assert ((test_uklon_payments_order.total_amount * 0.81) * rate) == 1704.969


def test_field_length(test_uklon_payments_order):
    assert len(test_uklon_payments_order.report_file_name) <= 255
    assert len(test_uklon_payments_order.signal) <= 8
    assert len(test_uklon_payments_order.licence_plate) <= 8


def test_type(test_uklon_payments_order):
    assert isinstance(test_uklon_payments_order.report_from, str)
    assert isinstance(test_uklon_payments_order.report_to, str)
    assert isinstance(test_uklon_payments_order.report_file_name, str)
    assert isinstance(test_uklon_payments_order.signal, str)
    assert isinstance(test_uklon_payments_order.licence_plate, str)
    assert isinstance(test_uklon_payments_order.total_rides, int)
    assert isinstance(test_uklon_payments_order.total_distance, int)
    assert isinstance(test_uklon_payments_order.total_amount_cach, float)
    assert isinstance(test_uklon_payments_order.total_amount_cach_less, float)
    assert isinstance(test_uklon_payments_order.total_amount, float)
    assert isinstance(test_uklon_payments_order.total_amount_without_comission, float)
    assert isinstance(test_uklon_payments_order.bonuses, float)
