import pytest
from app.models import UberPaymentsOrder


@pytest.fixture
def test_uber_payments_order(db) -> UberPaymentsOrder:
    return UberPaymentsOrder.objects.create(
        report_from='2022-08-29+03:00',
        report_to='2022-09-04+03:00',
        report_file_name='20220829-20220904-payments_driver-___.csv',
        driver_uuid='775f8943-b0ca-4079-90d3-c81d6563d0f1',
        first_name='Олександр',
        last_name='Холін',
        total_amount=float(1643.83),
        total_clean_amout=float(1643.83),
        total_amount_cach=float(-417.64),
        transfered_to_bank=float(0.0),
        returns=float(-417.64),
        tips=float(0.0))


def test_db(test_uber_payments_order):
    assert test_uber_payments_order.report_from == '2022-08-29+03:00'
    assert test_uber_payments_order.report_to == '2022-09-04+03:00'
    assert test_uber_payments_order.report_file_name == '20220829-20220904-payments_driver-___.csv'
    assert test_uber_payments_order.driver_uuid == '775f8943-b0ca-4079-90d3-c81d6563d0f1'
    assert test_uber_payments_order.first_name == 'Олександр'
    assert test_uber_payments_order.last_name == 'Холін'
    assert test_uber_payments_order.total_amount == float(1643.83)
    assert test_uber_payments_order.total_clean_amout == float(1643.83)
    assert test_uber_payments_order.total_amount_cach == float(-417.64)
    assert test_uber_payments_order.transfered_to_bank == float(0.0)
    assert test_uber_payments_order.returns == float(-417.64)
    assert test_uber_payments_order.tips == float(0.0)


def test_driver_id(test_uber_payments_order):
    assert test_uber_payments_order.driver_uuid == '775f8943-b0ca-4079-90d3-c81d6563d0f1'


def test_total_drivers_amount(test_uber_payments_order, rate=0.65):
    assert round(((test_uber_payments_order.total_amount*rate)+test_uber_payments_order.total_amount_cach), 2) == 650.85


def test_kassa(test_uber_payments_order):
    assert test_uber_payments_order.total_amount == 1643.83


def test_total_owner_amount(test_uber_payments_order, rate=0.65):
    assert round((test_uber_payments_order.total_amount * (1-rate) - float(650.85)), 2) == -75.51


def test_field_length(test_uber_payments_order):
    assert len(test_uber_payments_order.report_file_name) <= 255
    assert len(test_uber_payments_order.first_name) <= 24
    assert len(test_uber_payments_order.last_name) <= 24


def test_type(test_uber_payments_order):
    assert isinstance(test_uber_payments_order.report_from, str)
    assert isinstance(test_uber_payments_order.report_to, str)
    assert isinstance(test_uber_payments_order.report_file_name, str)
    assert isinstance(test_uber_payments_order.driver_uuid, str)
    assert isinstance(test_uber_payments_order.first_name, str)
    assert isinstance(test_uber_payments_order.last_name, str)
    assert isinstance(test_uber_payments_order.total_amount, float)
    assert isinstance(test_uber_payments_order.total_clean_amout, float)
    assert isinstance(test_uber_payments_order.total_amount_cach, float)
    assert isinstance(test_uber_payments_order.transfered_to_bank, float)
    assert isinstance(test_uber_payments_order.returns, float)
    assert isinstance(test_uber_payments_order.tips, float)
