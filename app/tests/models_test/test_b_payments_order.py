import pytest
from app.models import BoltPaymentsOrder


@pytest.fixture()
def test_bolt_payments_order(db) -> BoltPaymentsOrder:
    return BoltPaymentsOrder.objects.create(
        report_from='2022-08-29+03:00',
        report_to='2022-09-04+03:00',
        report_file_name='Щотижневий звіт Bolt – 2022W35 – Kyiv Fleet 03_232 park Universal-auto.csv',
        driver_full_name="Анатолій Мухін",
        mobile_number="+380936503350",
        range_string="Тиждень 2022-08-29 - 2022-09-04",
        total_amount=float(7233.00),
        cancels_amount=float(0.00),
        autorization_payment=float(0.00),
        autorization_deduction=float(0.00),
        additional_fee=float(0.00),
        fee=float(-1808.25),
        total_amount_cach=float(-3930.00),
        discount_cash_trips=float(619.00),
        driver_bonus=float(0.00),
        compensation=float(0.00),
        refunds=float(0.00),
        tips=float(0.00),
        weekly_balance=float(1494.75))


def test_db(test_bolt_payments_order):
    assert test_bolt_payments_order.report_from == '2022-08-29+03:00'
    assert test_bolt_payments_order.report_to == '2022-09-04+03:00'
    assert test_bolt_payments_order.report_file_name == 'Щотижневий звіт Bolt – 2022W35 – Kyiv Fleet 03_232 park Universal-auto.csv'
    assert test_bolt_payments_order.driver_full_name == "Анатолій Мухін"
    assert test_bolt_payments_order.mobile_number == "+380936503350"
    assert test_bolt_payments_order.range_string == "Тиждень 2022-08-29 - 2022-09-04"
    assert test_bolt_payments_order.total_amount == float(7233.00)
    assert test_bolt_payments_order.cancels_amount == float(0.00)
    assert test_bolt_payments_order.autorization_payment == float(0.00)
    assert test_bolt_payments_order.autorization_deduction == float(0.00)
    assert test_bolt_payments_order.additional_fee == float(0.00)
    assert test_bolt_payments_order.fee == float(-1808.25)
    assert test_bolt_payments_order.total_amount_cach == float(-3930.00)
    assert test_bolt_payments_order.discount_cash_trips == float(619.00)
    assert test_bolt_payments_order.driver_bonus == float(0.00)
    assert test_bolt_payments_order.compensation == float(0.00)
    assert test_bolt_payments_order.refunds == float(0.00)
    assert test_bolt_payments_order.tips == float(0.00)
    assert test_bolt_payments_order.weekly_balance == float(1494.75)


def test_driver_id(test_bolt_payments_order):
    assert test_bolt_payments_order.mobile_number == "+380936503350"


def test_total_cach_less_drivers_amount(test_bolt_payments_order):
    assert test_bolt_payments_order.total_amount + (test_bolt_payments_order.fee) + test_bolt_payments_order.cancels_amount + test_bolt_payments_order.driver_bonus == 5424.75


def test_kassa(test_bolt_payments_order):
    assert test_bolt_payments_order.total_amount + (test_bolt_payments_order.fee) + test_bolt_payments_order.cancels_amount + test_bolt_payments_order.driver_bonus == 5424.75


def test_total_drivers_amount(test_bolt_payments_order, rate=0.65):
    assert round(((test_bolt_payments_order.total_amount + (test_bolt_payments_order.fee) + test_bolt_payments_order.cancels_amount + test_bolt_payments_order.driver_bonus) * rate + test_bolt_payments_order.total_amount_cach), 2) == -403.91


def test_total_owner_amount(test_bolt_payments_order, rate=0.65):
    # 771.45 its result test_total_drivers_amount with rate=0.65
    assert round(((test_bolt_payments_order.total_amount + (test_bolt_payments_order.fee) + test_bolt_payments_order.cancels_amount + test_bolt_payments_order.driver_bonus) * (1-rate) - 771.45), 2) == 1127.21


def test_field_length(test_bolt_payments_order):
    assert len(test_bolt_payments_order.report_file_name) <= 255
    assert len(test_bolt_payments_order.driver_full_name) <= 24
    assert len(test_bolt_payments_order.mobile_number) <= 24
    assert len(test_bolt_payments_order.range_string) <= 50


def test_type(test_bolt_payments_order):
    assert isinstance(test_bolt_payments_order.report_from, str)
    assert isinstance(test_bolt_payments_order.report_to, str)
    assert isinstance(test_bolt_payments_order.report_file_name, str)
    assert isinstance(test_bolt_payments_order.driver_full_name, str)
    assert isinstance(test_bolt_payments_order.mobile_number, str)
    assert isinstance(test_bolt_payments_order.range_string, str)
    assert isinstance(test_bolt_payments_order.total_amount, float)
    assert isinstance(test_bolt_payments_order.cancels_amount, float)
    assert isinstance(test_bolt_payments_order.autorization_payment, float)
    assert isinstance(test_bolt_payments_order.autorization_deduction, float)
    assert isinstance(test_bolt_payments_order.additional_fee, float)
    assert isinstance(test_bolt_payments_order.fee, float)
    assert isinstance(test_bolt_payments_order.total_amount_cach, float)
    assert isinstance(test_bolt_payments_order.discount_cash_trips, float)
    assert isinstance(test_bolt_payments_order.driver_bonus, float)
    assert isinstance(test_bolt_payments_order.compensation, float)
    assert isinstance(test_bolt_payments_order.refunds, float)
    assert isinstance(test_bolt_payments_order.tips, float)
    assert isinstance(test_bolt_payments_order.weekly_balance, float)

