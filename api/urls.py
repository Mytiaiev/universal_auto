
from django.urls import path

from .views import SummaryReportListView, api_home

urlpatterns = [
    path('', api_home, name='index'),
    path("reports/<str:start>/<str:end>/", SummaryReportListView.as_view())
]