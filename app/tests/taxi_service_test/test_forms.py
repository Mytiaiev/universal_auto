#  -*- coding: utf-8 -*-
import pytest
from taxi_service.forms import SubscriberForm, MainOrderForm
from app.models import SubscribeUsers


@pytest.mark.parametrize(
    'phone_number, from_address, validity',
    [
        # valid
        ('80951234567', 'хрещатик 7', True),
        # short number
        ('854', 'бажана 10', False),
        # wrong number
        ('90504324444', 'оболонський пр-т, 15', False),
        # empty address
        ('80333334444', '', False),

    ]
)
def test_valid_order_form(phone_number, from_address, validity):
    form = MainOrderForm(data={'phone_number': phone_number, 'from_address': from_address})

    assert form.is_valid() is validity



@pytest.mark.parametrize(
    'email, validity',
    [
        # valid
        ('test@test.com', True),
        # email in db
        ('soft@test33.com', False),
        # wrong format
        ('testytest.com', False),
    ]
)
@pytest.mark.django_db
def test_valid_email_form(email, validity):
    sub = SubscribeUsers.objects.create(email='soft@test33.com')
    sub.save()
    form = SubscriberForm(data={'email': email})

    assert form.is_valid() is validity

