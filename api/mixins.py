from datetime import timedelta

from django.utils import timezone

from app.models import SummaryReport, Driver
from .permissions import IsPartnerUser, IsManagerUser, IsInvestorUser


class PartnerFilterMixin:
    def get_queryset(self, model):
        queryset = model.objects.filter(partner__user=self.request.user)
        return queryset


class ManagerFilterMixin:
    def get_queryset(self, model):
        if isinstance(model, SummaryReport):
            manager_drivers = Driver.objects.filter(manager__user=self.request.user)
            full_names = [f"{driver.name} {driver.second_name}" for driver in manager_drivers]
            queryset = model.objects.filter(full_name__in=full_names)
            return queryset


class InvestorFilterMixin:
    def get_queryset(self, model):
        queryset = model.objects.filter(investor_car__user=self.request.user)
        return queryset


class CombinedPermissionsMixin:

    def get_permissions(self):
        permissions = [
            IsManagerUser().has_permission(self.request, self),
            IsPartnerUser().has_permission(self.request, self),
            IsInvestorUser().has_permission(self.request, self),
        ]

        for i, permission in enumerate(permissions):
            if permission:
                return [[IsManagerUser()], [IsPartnerUser()], [IsInvestorUser()]][i]