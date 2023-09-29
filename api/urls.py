
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import SummaryReportListView, CarEfficiencyListView, CarsInformationListView, DriverEfficiencyListView

urlpatterns = [
    path("token-auth/", obtain_auth_token),
    path("reports/<str:start>/<str:end>/", SummaryReportListView.as_view()),
    path("car_efficiencies/<str:start>/<str:end>/", CarEfficiencyListView.as_view()),
    path("vehicles_info/", CarsInformationListView.as_view()),
    path("drivers_info/<str:start>/<str:end>/", DriverEfficiencyListView.as_view())
]
