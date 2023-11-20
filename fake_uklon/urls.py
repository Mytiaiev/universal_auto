from django.urls import path

from fake_uklon.views import Export, Login

urlpatterns = [
    path("login/", Login.as_view()),
    path("partner/export/fares/", Export.as_view(), name="report"),
]
