from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    SummaryReportListView,
    CarEfficiencyListView,
    CarsInformationListView,
    DriverEfficiencyListView,
    InvestorCarsEarningsView,
)

urlpatterns = [
    path("token-auth/", obtain_auth_token),
    path("reports/<str:period>/", SummaryReportListView.as_view()),
    path(
        "car_efficiencies/<str:period>/<int:vehicle>", CarEfficiencyListView.as_view()
    ),
    path("vehicles_info/", CarsInformationListView.as_view()),
    path("investor_info/<str:period>/", InvestorCarsEarningsView.as_view()),
    path("drivers_info/<str:period>/", DriverEfficiencyListView.as_view()),
]
