from django.test import SimpleTestCase
from taxi_service.forms import MainOrderForm, SubscriberForm


class TestForms(SimpleTestCase):

    def test_order_form_valid_data(self):
        form = MainOrderForm(data={'from_address': 'my address', 'phone_number': '80951565555'})

        self.assertTrue(form.is_valid())

    def test_order_form_empty_data(self):
        form = MainOrderForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_order_form_invalid_data(self):
        form = MainOrderForm(data={'from_address': 'my address', 'phone_number': '80565555'})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)

    def test_sub_form_valid_data(self):
        form = SubscriberForm(data={'email': 'test@test.com'})

        self.assertTrue(form.is_valid())

    def test_sub_form_empty_data(self):
        form = SubscriberForm(data={})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)

    def test_sub_form_invalid_data(self):
        form = SubscriberForm(data={'email': 'test.com'})

        self.assertFalse(form.is_valid())

