from django.db.models import Q
from rest_framework import authentication

from app.models import SummaryReport, Driver, CarEfficiency, DriverEfficiency, Vehicle
from .permissions import IsPartnerUser, IsManagerUser, IsInvestorUser
from api.authentication import TokenAuthentication


class PartnerFilterMixin:
    def get_queryset(self, model):
        queryset = model.objects.filter(partner__user=self.request.user)
        return queryset


class ManagerFilterMixin:
    def get_queryset(self, model):
        user = self.request.user

        model_filter_map = {
            SummaryReport: Q(full_name__in=[f"{driver.name} {driver.second_name}" for driver in
                                            Driver.objects.filter(manager__user=user)]),
            CarEfficiency: Q(vehicle__manager__user=user),
            DriverEfficiency: Q(driver__manager__user=user),
            Vehicle: Q(manager__user=user),
        }

        filter_condition = model_filter_map.get(model)
        if filter_condition:
            queryset = model.objects.filter(filter_condition)
        else:
            queryset = model.objects.none()

        return queryset


class InvestorFilterMixin:
    def get_queryset(self, model):
        if isinstance(model(), Vehicle):
            queryset = model.objects.filter(investor_car__user=self.request.user)
        elif isinstance(model(), CarEfficiency):
            queryset = model.objects.filter(vehicle__investor_car__user=self.request.user)
        else:
            queryset = model.objects.none()
        return queryset


class CombinedPermissionsMixin:
    authentication_classes = [authentication.SessionAuthentication,
                              TokenAuthentication]

    def get_permissions(self):
        permissions = [
            IsManagerUser().has_permission(self.request, self),
            IsPartnerUser().has_permission(self.request, self),
            IsInvestorUser().has_permission(self.request, self),
        ]

        for i, permission in enumerate(permissions):
            if permission:
                return [[IsManagerUser()], [IsPartnerUser()], [IsInvestorUser()]][i]
