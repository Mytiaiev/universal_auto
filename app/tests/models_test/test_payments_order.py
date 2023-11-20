import pytest
from app.models import PaymentsOrder


@pytest.fixture
def test_payments_order(db) -> PaymentsOrder:
    return PaymentsOrder.objects.create(
        transaction_uuid='6a49c49a-eaee-5f24-aa4e-2a30eb81bfb6',
        driver_uuid='cd725b41-9e47-4fd0-8a1f-3514ddf6238a',
        driver_name='Олександр',
        driver_second_name='Холін',
        trip_uuid='e54f97da-73a4-464f-8a32-af6f948165d9',
        trip_description='',
        organization_name='',
        organization_nickname='',
        transaction_time='2022-08-29+03:00',
        your_earnings=float(55.59),
        paid_to_you=float(59),
        cash=float(0),
        fare=float(0),
        tax=float(0),
        fare2=float(0),
        service_tax=float(0),
        wait_time=float(0),
        out_of_city=float(0),
        tips=float(0),
        transfered_to_bank=float(0),
        ajustment_payment=float(0),
        cancel_payment=float(0))


def test_db(test_payments_order):
    assert test_payments_order.transaction_uuid == '6a49c49a-eaee-5f24-aa4e-2a30eb81bfb6'
    assert test_payments_order.driver_uuid == 'cd725b41-9e47-4fd0-8a1f-3514ddf6238a'
    assert test_payments_order.driver_name == 'Олександр'
    assert test_payments_order.driver_second_name == 'Холін'
    assert test_payments_order.trip_uuid == 'e54f97da-73a4-464f-8a32-af6f948165d9'
    assert test_payments_order.trip_description == ''
    assert test_payments_order.organization_name == ''
    assert test_payments_order.organization_nickname == ''
    assert test_payments_order.transaction_time == '2022-08-29+03:00'
    assert test_payments_order.your_earnings == float(55.59)
    assert test_payments_order.paid_to_you == float(59)
    assert test_payments_order.cash == float(0)
    assert test_payments_order.fare == float(0)
    assert test_payments_order.tax == float(0)
    assert test_payments_order.fare2 == float(0)
    assert test_payments_order.service_tax == float(0)
    assert test_payments_order.wait_time == float(0)
    assert test_payments_order.out_of_city == float(0)
    assert test_payments_order.tips == float(0)
    assert test_payments_order.transfered_to_bank == float(0)
    assert test_payments_order.ajustment_payment == float(0)
    assert test_payments_order.cancel_payment == float(0)


def test_field_length(test_payments_order):
    assert len(test_payments_order.driver_name) <= 30
    assert len(test_payments_order.driver_second_name) <= 30
    assert len(test_payments_order.trip_uuid) <= 255
    assert len(test_payments_order.trip_description) <= 50
    assert len(test_payments_order.organization_name) <= 50
    assert len(test_payments_order.organization_nickname) <= 50


def test_type(test_payments_order):
    assert (test_payments_order.transaction_uuid, str)
    assert (test_payments_order.driver_uuid, str)
    assert (test_payments_order.driver_name, str)
    assert (test_payments_order.driver_second_name, str)
    assert (test_payments_order.trip_uuid, str)
    assert (test_payments_order.trip_description, str)
    assert (test_payments_order.organization_name, str)
    assert (test_payments_order.organization_nickname, str)
    assert (test_payments_order.transaction_time, str)
    assert (test_payments_order.your_earnings, float)
    assert (test_payments_order.paid_to_you, float)
    assert (test_payments_order.cash, float)
    assert (test_payments_order.fare, float)
    assert (test_payments_order.tax, float)
    assert (test_payments_order.fare, float)
    assert (test_payments_order.service_tax, float)
    assert (test_payments_order.wait_time, float)
    assert (test_payments_order.out_of_city, float)
    assert (test_payments_order.tips, float)
    assert (test_payments_order.transfered_to_bank, float)
    assert (test_payments_order.ajustment_payment, float)
    assert (test_payments_order.cancel_payment, float)
