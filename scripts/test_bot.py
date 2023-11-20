import unittest


class TestBot(unittest.TestCase):
    def test_main(self):
        self.assertIsNotNone("/start")

    def test_main2(self):
        self.assertTrue('/start')

    def test_aut_handler(self):
        self.assertIsNotNone('Get autorizate')
    
    def test_reg_handler(self):
        self.assertIsNotNone('Get registration')

    def test_get_manager_today_report(self):
        self.assertTrue('Get all today statistic')

    def test_get_driver_today_report(self):
        self.assertTrue('Get today statistic')

    def test_report(self):
        self.assertIsNotNone("/report")

    def test_report_2(self):
        self.assertTrue('/report')

    def test_save_reports(self):
        self.assertIsNotNone("/save_reports")

    def test_save_reports_2(self):
        self.assertTrue('/save_reports')

    def test_status(self):
        self.assertTrue('/status')

    def test_status_2(self):
        self.assertIsNotNone('/status')

    def test_status_car(self):
        self.assertTrue('/status_car')

    def test_status_car_2(self):
        self.assertIsNotNone('/status_car')

    def test_send_report(self):
        self.assertTrue('/send_report')

    def test_send_report_2(self):
        self.assertIsNotNone('/send_report')

    def test_broken_car(self):
        self.assertTrue('/car_status')

    def test_broken_car_2(self):
        self.assertIsNotNone('/car_status')

    def test_get_information(self):
        self.assertTrue('/get_information')

    def test_get_information_2(self):
        self.assertIsNotNone('/get_information')

    def test_id(self):
        self.assertTrue('/id')

    def test_id_2(self):
        self.assertIsNotNone('/id')

    def test_driver_status(self):
        self.assertTrue('/driver_status')

    def test_driver_status_2(self):
        self.assertIsNotNone('/driver_status')

    def test_rating(self):
        self.assertTrue('/rating')

    def test_rating_2(self):
        self.assertIsNotNone('/rating')
