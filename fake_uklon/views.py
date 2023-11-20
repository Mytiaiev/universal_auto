import logging
import os
import urllib


import pendulum
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views import View

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Login(View):
    @staticmethod
    def get(request):
        return render(request, "fake_uklon/login.html")

    @staticmethod
    def post(request):
        user_login = request.POST.get("login")
        password = request.POST.get("loginPassword")
        user = authenticate(username=user_login, password=password)

        if user is not None:
            login(request, user)
            warning = f"Hello, {user}"
            return render(
                request, "fake_uklon/warning.html", context={"warning": warning}
            )
        else:
            warning = "Wrong login or password"
            return render(
                request, "fake_uklon/warning.html", context={"warning": warning}
            )


class Export(LoginRequiredMixin, View):
    """Generate report"""

    TEST_DATA = "Signal||LicencePlate||TotalRides||TotalDistance||TotalAmountCach||TotalAmountCachLess||TotalAmount||TotalAmountWithoutComission||Bonuses\n"
    TEST_DATA_08_29 = """324460||KA8443EA||35||435||3402||2612||6014||1022.38||0
362612||KA4897EM||33||259||2247||1841||4088||694.96||0"""
    TEST_DATA_09_05 = """324460||KA8443EA||28||313||1372||3006||4378||744.26||0
372353||AA3108YA||26||224||1523||2004||3527||599.59||0
362612||KA4897EM||35||299||1365||3315||4680||795.60||0"""
    TEST_DATA_09_12 = """324460||KA8443EA||26||329||1679||2863||4542||772.14||0
372353||AA3108YA||17||159||444||2035||2479||421.43||0
362612||KA4897EM||42||355||2085||3465||5550||943.50||0"""
    TEST_DATA_09_19 = """368808||KA1644CT||25||345||2627||2013||4640||788.80||0
372353||AA3108YA||23||240||1070||2491||3561||605.37||0
362612||KA4897EM||16||147||1144||1025||2169||368.73||0"""

    redirect_field_name = "/fake_uklon/login/"
    # url = f"https://partner.uklon.com.ua/partner/export/fares?
    # page=1
    # &pageSize=20
    # &startDate={self.start_of_week_timestamp()}
    # &endDate={self.end_of_week_timestamp()}
    # &format=csv"

    @staticmethod
    def get(request):
        start_date = request.GET.get("startDate")
        end_date = request.GET.get("endDate")

        start = pendulum.from_timestamp(int(start_date), tz="Europe/Kiev")
        end = pendulum.from_timestamp(int(end_date), tz="Europe/Kiev")

        sd, sy, sm = start.strftime("%-d"), start.strftime("%Y"), start.strftime("%-m")
        ed, ey, em = end.strftime("%-d"), end.strftime("%Y"), end.strftime("%-m")
        if int(sd) == 29:
            test_data = Export.TEST_DATA_08_29
        elif int(sd) == 5:
            test_data = Export.TEST_DATA_09_05
        elif int(sd) == 12:
            test_data = Export.TEST_DATA_09_12
        else:
            test_data = Export.TEST_DATA_09_19

        if request.GET.get("format") == "csv":
            filename = f"Куцко - Income_{sm}_{sd}_{sy} 3_00_00 AM-{em}_{ed}_{ey} 3_00_00 AM.csv"
            response = HttpResponse(
                Export.TEST_DATA + test_data,
                content_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={urllib.parse.quote(filename)}"
                },
            )
            return response
        drivers = []
        for row in test_data.split("\n"):
            row = row.split("||")
            driver = {
                "signal": row[0],
                "licence_plate": row[1],
                "total_rides": row[2],
                "total_distance": row[3],
                "total_amount_cach": row[4],
                "total_amount_cach_less": row[5],
                "total_amount": row[6],
                "total_amount_without_comission": row[7],
                "bonuses": row[8],
                "profit": float(row[6]) - float(row[7]),
            }
            drivers.append(driver)
        return render(
            request,
            "fake_uklon/report.html",
            {
                "drivers": drivers,
                "start": start.format("DD.MM.YYYY hh:mm"),
                "end": end.format("DD.MM.YYYY hh:mm"),
            },
        )
