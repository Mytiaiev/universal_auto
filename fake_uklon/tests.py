from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase

from fake_uklon.views import Export
import pendulum

class UserAusenticateTest(TestCase):
    def setUp(self):
        user = User.objects.create_user("TestUserName", "test@user.mail", "My_password")
        user.save()
        self.c = Client()
        self.factory = RequestFactory()

    def tearDown(self) -> None:
        user = User.objects.get(username="TestUserName")
        user.delete()

    def test_user_authenticate_ok(self):
        """input correct login and password"""
        response = self.c.post(
            "/fake_uklon/login/",
            {"login": "TestUserName", "loginPassword": "My_password"},
        )
        self.assertEqual(response.status_code, 200, "Error status code")
        content = str(response.content)
        self.assertIn("Hello, ", content, "Error logining")

    def test_user_authenticate_err(self):
        """input wrong password"""
        response = self.c.post(
            "/fake_uklon/login/",
            {"login": "TestUserName", "loginPassword": "My_wrong_password"},
        )
        self.assertEqual(response.status_code, 200, "Error status code")
        content = str(response.content)
        self.assertIn("Wrong login or password", content, "Error logining")

    def test_get_login_page(self):
        response = self.c.get("/fake_uklon/login/")
        self.assertEqual(response.status_code, 200, "Error status code")
        content = str(response.content)
        self.assertIn('name="login"', content, "Error load loging page")
        self.assertIn('name="loginPassword"', content, "Error load loging page")

    def test_get_report_html(self):
        request = self.factory.get(
            "/fake_uklon/partner/export/fares?page=1&pageSize=20&startDate=1663534800&endDate=1664139600"
        )
        user = User.objects.get(username="TestUserName")
        request.user = user
        response = Export.as_view()(request)
        self.assertEqual(response.status_code, 200, "Error status code")
        self.assertEqual(
            response.headers["Content-Type"],
            "text/html; charset=utf-8",
            "Error. Return not html",
        )

    def test_get_report_csv(self):
        request = self.factory.get(
            "/fake_uklon/partner/export/fares?page=1&pageSize=20&startDate=1663534800&endDate=1664139600&format=csv"
        )
        user = User.objects.get(username="TestUserName")
        request.user = user
        response = Export.as_view()(request)
        self.assertEqual(response.status_code, 200, "Error status code")
        self.assertEqual(
            response.headers["Content-Type"], "text/csv", "Error. Return not csv"
        )

    def test_difference_report(self):
        start1 = round(pendulum.datetime(2022, 8, 29, tz="Europe/Kiev").timestamp())
        end1 = round(pendulum.datetime(2022, 9, 5, tz="Europe/Kiev").timestamp())
        start2 = round(pendulum.datetime(2022, 9, 12, tz="Europe/Kiev").timestamp())
        end2 = round(pendulum.datetime(2022, 9, 19, tz="Europe/Kiev").timestamp())

        request1 = self.factory.get(
            f"/fake_uklon/partner/export/fares?page=1&pageSize=20&startDate={start1}&endDate={end1}&format=csv"
        )
        request2 = self.factory.get(
            f"/fake_uklon/partner/export/fares?page=1&pageSize=20&startDate={start2}&endDate={end2}&format=csv"
        )

        user = User.objects.get(username="TestUserName")
        request1.user = user
        request2.user = user
        response1 = Export.as_view()(request1)
        response2 = Export.as_view()(request2)

        self.assertNotEqual(response1.content, response2.content, "Error. Content is equal!")
