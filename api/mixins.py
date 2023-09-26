from datetime import timedelta

from django.utils import timezone

from app.models import SummaryReport
from .permissions import IsPartnerUser


class PartnerPermissionsMixin:
    def get_queryset(self):
        queryset = SummaryReport.objects.filter(partner__user=self.request.user)
        return queryset

    def get_permissions(self):
        # Ensure that only partners have access to the view
        return [IsPartnerUser()]
