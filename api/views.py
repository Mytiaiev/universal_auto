from collections import defaultdict

from django.db.models import Sum, F, OuterRef, Subquery, DecimalField, Avg, Value, CharField, ExpressionWrapper
from django.db.models.functions import Concat
from rest_framework import generics
from rest_framework.response import Response

from api.mixins import CombinedPermissionsMixin, PartnerFilterMixin, ManagerFilterMixin, InvestorFilterMixin
from api.serializers import SummaryReportSerializer, CarEfficiencySerializer, CarDetailSerializer, \
    DriverEfficiencyRentSerializer
from app.models import SummaryReport, CarEfficiency, Vehicle, DriverEfficiency, RentInformation


# Create your views here.

class SummaryReportListView(CombinedPermissionsMixin,
                            PartnerFilterMixin,
                            ManagerFilterMixin,
                            generics.ListAPIView):
    serializer_class = SummaryReportSerializer

    def get_queryset(self):
        start = self.kwargs['start']
        end = self.kwargs['end']
        queryset = []
        partner_queryset = PartnerFilterMixin.get_queryset(self, SummaryReport)
        if partner_queryset:
            queryset = partner_queryset
        manager_queryset = ManagerFilterMixin.get_queryset(self, SummaryReport)
        if manager_queryset:
            queryset = manager_queryset
        filtered_qs = queryset.filter(report_from__range=(start, end))
        kasa = filtered_qs.aggregate(kasa_sum=Sum('total_amount_without_fee'))['kasa_sum'] or 0
        queryset = filtered_qs.values('full_name').annotate(
            total_kasa=Sum('total_amount_without_fee'),
            total_cash=Sum('total_amount_cash')
        )
        queryset = queryset.exclude(total_kasa=0)

        return [{'kasa': kasa, 'drivers': queryset}]


class CarEfficiencyListView(CombinedPermissionsMixin,
                            generics.ListAPIView):
    serializer_class = CarEfficiencySerializer

    def get_queryset(self):
        start = self.kwargs['start']
        end = self.kwargs['end']
        queryset = []
        partner_queryset = PartnerFilterMixin.get_queryset(self, CarEfficiency)
        if partner_queryset:
            queryset = partner_queryset
        manager_queryset = ManagerFilterMixin.get_queryset(self, CarEfficiency)
        if manager_queryset:
            queryset = manager_queryset
        filtered_qs = queryset.filter(report_from__range=(start, end))

        return filtered_qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Create a dictionary to group data by 'report_from' date
        grouped_data = {}
        total_mileage = queryset.aggregate(total_mileage=Sum('mileage'))['total_mileage']
        for item in queryset:
            report_from = item.report_from.strftime('%Y-%m-%d')
            item_data = {
                "licence_plate": item.licence_plate,
                "mileage": str(item.mileage),
                "efficiency": str(item.efficiency)
            }

            if report_from not in grouped_data:
                grouped_data[report_from] = []

            grouped_data[report_from].append(item_data)

        # Serialize the grouped data
        serialized_data = []

        for report_from, records in grouped_data.items():
            serialized_data.append({report_from: records})

        response_data = {
            "efficiency": serialized_data,
            "total_mileage": total_mileage
        }
        return Response(response_data)


class DriverEfficiencyListView(CombinedPermissionsMixin,
                               generics.ListAPIView):
    serializer_class = DriverEfficiencyRentSerializer

    def get_queryset(self):
        start = self.kwargs['start']
        end = self.kwargs['end']
        queryset = []
        partner_queryset = PartnerFilterMixin.get_queryset(self, DriverEfficiency)
        if partner_queryset:
            queryset = partner_queryset
        manager_queryset = ManagerFilterMixin.get_queryset(self, DriverEfficiency)
        if manager_queryset:
            queryset = manager_queryset
        filtered_qs = queryset.filter(report_from__range=(start, end)).exclude(total_orders=0)
        rent_amount_subquery = RentInformation.objects.filter(
            report_from__range=(start, end)
        ).values('driver_id').annotate(
            rent_amount=Sum('rent_distance')
        )
        qs = filtered_qs.values('driver_id').annotate(
            total_kasa=Sum('total_kasa'),
            full_name=Concat(F("driver__user_ptr__name"),
                             Value(" "),
                             F("driver__user_ptr__second_name"), output_field=CharField()),
            orders=Sum('total_orders'),
            average_price=Avg('average_price'),
            accept_percent=Avg('accept_percent'),
            road_time=Sum('road_time'),
            efficiency=Avg('efficiency'),
            mileage=Sum('mileage'),
            rent_amount=Subquery(rent_amount_subquery.filter(
                driver_id=OuterRef('driver_id')).values('rent_amount'), output_field=DecimalField())
        )
        total_rent = qs.aggregate(total_rent=Sum('rent_amount'))['total_rent'] or 0
        return [{'total_rent': total_rent, 'drivers_efficiency': qs}]


class CarsInformationListView(CombinedPermissionsMixin,
                                generics.ListAPIView):
    serializer_class = CarDetailSerializer

    def get_queryset(self):
        queryset = []
        partner_queryset = PartnerFilterMixin.get_queryset(self, Vehicle)
        if partner_queryset:
            queryset = partner_queryset
        manager_queryset = ManagerFilterMixin.get_queryset(self, Vehicle)
        if manager_queryset:
            queryset = manager_queryset
        investor_queryset = InvestorFilterMixin.get_queryset(self, Vehicle)
        if investor_queryset:
            queryset = investor_queryset

        return queryset