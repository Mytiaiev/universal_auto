import datetime
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auto.settings")
django.setup()

from django.test import TestCase

from scripts.driversrating import UberDriversRating, BoltDriversRating, UklonDriversRating
from app.models import UberPaymentsOrder, BoltPaymentsOrder, UklonPaymentsOrder
from app.libs.selenium_tools import SeleniumTools

class UklonDriversRatingTest(TestCase):

    st = SeleniumTools(session='', week_number='2022-10-03')

    @classmethod
    def setUpTestData(cls):
        for i in range(5):
            UklonPaymentsOrder.objects.create(
                report_from=cls.st.start_of_week(),
                report_to=cls.st.end_of_week(),
                report_file_name='Name',
                signal='123',
                licence_plate='555',
                total_rides=5,
                total_distance=10,
                total_amount_cach=0,
                total_amount_cach_less=0,
                total_amount=1000,
                total_amount_without_comission=0,
                bonuses=0,
            )

    def setUp(self):
        self.rating = UklonDriversRating(self.st.start_of_week(), self.st.end_of_week()).get_rating()

    def test_len(self):
        self.assertEqual(len(self.rating), 1)

    def test_max_rating(self):
        self.assertEqual(self.rating[0]['driver'], '555')

    def test_total_rides(self):
        self.assertEqual(self.rating[0]['trips'], 25)


class UberDriversRatingTest(TestCase):

    st = SeleniumTools(session='', week_number='2022-10-03')

    @classmethod
    def setUpTestData(cls):
        for i in range(10):
            UberPaymentsOrder.objects.create(
                report_from=cls.st.start_of_week(),
                report_to=cls.st.end_of_week(),
                driver_uuid=i,
                first_name=f'Name{i}',
                last_name=f'LastName{i}',
                total_amount=100*i,
                total_clean_amout=0,
                total_amount_cach=0,
                transfered_to_bank=0,
                returns=0,
                tips=0,
            )

    def setUp(self):
        self.rating = UberDriversRating(self.st.start_of_week(), self.st.end_of_week()).get_rating()

    def test_len(self):
        self.assertEqual(len(self.rating), 11)

    def test_max_rating(self):
        self.assertEqual(self.rating[0]['driver'], 'Name9 LastName9')


class BoltDriversRatingTest(TestCase):

    st = SeleniumTools(session='', week_number='2022-10-03')

    @classmethod
    def setUpTestData(cls):
        for i in range(5):
            BoltPaymentsOrder.objects.create(
                report_from=cls.st.start_of_week(),
                report_to=cls.st.end_of_week(),
                report_file_name='',
                driver_full_name=f'Name{i}',
                mobile_number='111111111',
                total_amount=100*i,
                cancels_amount=0,
                autorization_payment=0,
                autorization_deduction=0,
                additional_fee=0,
                fee=0,
                total_amount_cach=0,
                discount_cash_trips=0,
                driver_bonus=0,
                compensation=0,
                refunds=0,
                tips=0,
                weekly_balance=0,
            )

    def setUp(self):
        self.rating = BoltDriversRating(self.st.start_of_week(), self.st.end_of_week()).get_rating()

    def test_len(self):
        self.assertEqual(len(self.rating), 5)

    def test_max_rating(self):
        self.assertEqual(self.rating[0]['driver'], 'Name4')


