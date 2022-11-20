import os
import unittest

from app.models import Uklon
from app.models import UklonPaymentsOrder
from django.contrib.auth.models import User
from django.test import TestCase


@unittest.skip
class TestSeleniumTools(TestCase):
    """add enveronment UKLON_NAME=TestUserName and UKLON_PASSWORD=My_password"""

    def setUp(self):
        user = User.objects.create_user("TestUserName", "test@user.mail", "My_password")
        user.save()

    def tearDown(self) -> None:
        user = User.objects.get(username="TestUserName")
        user.delete()

    def test_start(self):
        u = Uklon(base_url="http://127.0.0.1:8000/fake_uklon/")
        u.login()
        u.download_payments_order()
        ur = u.save_report()
        self.assertIsInstance(ur[0], UklonPaymentsOrder)
        print(u.payments_order_file_name())
        os.remove(u.payments_order_file_name())
