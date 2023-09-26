from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view

# Create your views here.
from rest_framework.response import Response

from api.mixins import PartnerPermissionsMixin
from api.serializers import SummaryReportSerializer
from app.models import SummaryReport


@api_view(['GET'])
def api_home(request, *args, **kwargs):

    instance = SummaryReport.objects.all().order_by('?').first()
    data = {}
    if instance:
        data = SummaryReportSerializer(instance).data
    return Response(data)


class SummaryReportListView(PartnerPermissionsMixin, generics.ListAPIView):
    serializer_class = SummaryReportSerializer

    def get_queryset(self):
        start = self.kwargs['start']
        end = self.kwargs['end']
        queryset = super().get_queryset()
        queryset = queryset.filter(report_from__range=(start, end))

        return queryset
