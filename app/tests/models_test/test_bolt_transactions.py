from django.db import transaction, models, IntegrityError
from django.test import TestCase
from app.models import BoltTransactions


class BoltTransactionsTests(TestCase):

    @transaction.atomic
    def create_spam(self):
        spam = BoltTransactions.objects.create(driver_name='Юрій Філіппов',
                                               driver_number='+380502428878',
                                               trip_date='2022-09-12',
                                               payment_confirmed='19:03',
                                               boarding='Івана Дяченка вулиця 13, Киев 02088',
                                               payment_method='Готівка',
                                               requsted_time='18:06',
                                               fare=283.00,
                                               payment_authorization=0.00,
                                               service_tax=0.00,
                                               cancel_payment=0.00,
                                               tips=0.00,
                                               order_status='Завершено',
                                               car='Renault Mégane',
                                               license_plate='KA6047EI')
        spam.save()
        return True

    def test_integrity_error(self):
        # first one should work fine
        self.assertTrue(self.create_spam())
        # second time violates unique constraint
        self.assertRaises(IntegrityError, self.create_spam)
        # have we recovered?
        self.assertEquals(len(BoltTransactions.objects.all()), 1)

