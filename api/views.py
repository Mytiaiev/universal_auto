from collections import defaultdict
from datetime import timedelta

from _decimal import Decimal
from django.db.models import Sum, F, OuterRef, Subquery, DecimalField, Avg, Value, CharField, ExpressionWrapper, Case, \
    When
from django.db.models.functions import Concat, Round, Coalesce
from rest_framework import generics
from rest_framework.response import Response

from api.mixins import CombinedPermissionsMixin, PartnerFilterMixin, ManagerFilterMixin, InvestorFilterMixin
from api.serializers import SummaryReportSerializer, CarEfficiencySerializer, CarDetailSerializer, \
    DriverEfficiencyRentSerializer, InvestorCarsSerializer
from app.models import SummaryReport, CarEfficiency, Vehicle, DriverEfficiency, RentInformation
from taxi_service.utils import get_dates


# Create your views here.

class SummaryReportListView(CombinedPermissionsMixin,
                            ManagerFilterMixin,
                            generics.ListAPIView):
    serializer_class = SummaryReportSerializer

    def get_queryset(self):
        if self.kwargs['period'] in ('yesterday', 'current_week', 'current_month', 'current_quarter',
                                     'last_week', 'last_month', 'last_quarter'):
            start, end = get_dates(self.kwargs['period'])
            format_start = start.strftime("%d.%m.%Y")
            format_end = end.strftime("%d.%m.%Y")
        else:
            start, end = self.kwargs['period'].split('&')
            format_start = ".".join(start.split("-")[::-1])
            format_end = ".".join(end.split("-")[::-1])

        queryset = ManagerFilterMixin.get_queryset(self, SummaryReport)
        filtered_qs = queryset.filter(report_from__range=(start, end))
        rent_amount_subquery = RentInformation.objects.filter(
            report_from__range=(start, end)
        ).values('driver_id').annotate(
            rent_amount=Sum('rent_distance')
        )
        queryset = filtered_qs.values('driver_id').annotate(
            full_name=Concat(F("driver__user_ptr__name"),
                             Value(" "),
                             F("driver__user_ptr__second_name"), output_field=CharField()),
            total_kasa=Sum('total_amount_without_fee'),
            total_cash=Sum('total_amount_cash'),
            rent_amount=Subquery(rent_amount_subquery.filter(
                driver_id=OuterRef('driver_id')).values('rent_amount'), output_field=DecimalField())
        )
        total_rent = queryset.aggregate(total_rent=Sum('rent_amount'))['total_rent'] or 0
        queryset = queryset.exclude(total_kasa=0).order_by('full_name')

        return [{'total_rent': total_rent, 'start': format_start, 'end': format_end, 'drivers': queryset}]


class InvestorCarsEarningsView(CombinedPermissionsMixin,
                               generics.ListAPIView):
    serializer_class = InvestorCarsSerializer

    def get_queryset(self):
        if self.kwargs['period'] in ('yesterday', 'current_week', 'current_month', 'current_quarter',
                                     'last_week', 'last_month', 'last_quarter'):
            start, end = get_dates(self.kwargs['period'])
            format_start = start.strftime("%d.%m.%Y")
            format_end = end.strftime("%d.%m.%Y")
        else:
            start, end = self.kwargs['period'].split('&')
            format_start = ".".join(start.split("-")[::-1])
            format_end = ".".join(end.split("-")[::-1])

        queryset = CarEfficiency.objects.none()
        investor_queryset = InvestorFilterMixin.get_queryset(self, CarEfficiency)
        if investor_queryset:
            queryset = investor_queryset
        filtered_qs = queryset.filter(report_from__range=(start, end))
        qs = filtered_qs.values('vehicle__licence_plate').annotate(
            licence_plate=F('vehicle__licence_plate'),
            earnings=Sum(F('total_kasa') * F('vehicle__investor_percentage')),
            mileage=Sum('mileage'))
        total_qs = filtered_qs.aggregate(
            total_earnings=Coalesce(Sum(F('total_kasa') * F('vehicle__investor_percentage')), Decimal(0)),
            total_mileage=Coalesce(Sum('mileage'), Decimal(0)),
            total_spending=Coalesce(Sum('total_spending'), Decimal(0)))
        return [{'start': format_start, 'end': format_end, 'car_earnings': qs, 'totals': total_qs}]


class CarEfficiencyListView(CombinedPermissionsMixin,
                            generics.ListAPIView):
    serializer_class = CarEfficiencySerializer

    def get_queryset(self):
        if self.kwargs['period'] in ('yesterday', 'current_week', 'current_month', 'current_quarter',
                                     'last_week', 'last_month', 'last_quarter'):
            start, end = get_dates(self.kwargs['period'])
        else:
            start, end = self.kwargs['period'].split('&')

        queryset = ManagerFilterMixin.get_queryset(self, CarEfficiency)
        filtered_qs = queryset.filter(report_from__range=(start, end)).select_related("vehicle").order_by("report_from")
        return filtered_qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        aggregated_data = queryset.aggregate(
            total_kasa=Coalesce(Sum('total_kasa'), Decimal(0)),
            total_mileage=Coalesce(Sum('mileage'), Decimal(0)),
        )
        efficiency_dict = {}
        kasa = aggregated_data.get('total_kasa')
        total_mileage = aggregated_data.get('total_mileage')
        average = kasa/total_mileage if total_mileage else Decimal(0)
        dates = sorted(list(set(queryset.values_list("report_from", flat=True))))
        for vehicle in queryset.values_list("vehicle__licence_plate", flat=True):
            if vehicle not in efficiency_dict:
                efficiency_dict[vehicle] = {
                    "name": vehicle,
                    "mileage": list(queryset.filter(vehicle__licence_plate=vehicle).values_list("mileage", flat=True)),
                    "efficiency": list(
                        queryset.filter(vehicle__licence_plate=vehicle).values_list("efficiency", flat=True))
                }

        response_data = {
            "vehicles": list(efficiency_dict.values()),
            "dates": dates,
            "total_mileage": total_mileage,
            "kasa": kasa,
            "average_efficiency": average
        }
        return Response(response_data)


class DriverEfficiencyListView(CombinedPermissionsMixin,
                               generics.ListAPIView):
    serializer_class = DriverEfficiencyRentSerializer

    def get_queryset(self):
        if self.kwargs['period'] in ('yesterday', 'current_week', 'current_month', 'current_quarter',
                                     'last_week', 'last_month', 'last_quarter'):
            start, end = get_dates(self.kwargs['period'])
            format_start = start.strftime("%d.%m.%Y")
            format_end = end.strftime("%d.%m.%Y")

        else:
            start, end = self.kwargs['period'].split('&')
            format_start = ".".join(start.split("-")[::-1])
            format_end = ".".join(end.split("-")[::-1])

        queryset = ManagerFilterMixin.get_queryset(self, DriverEfficiency)
        filtered_qs = queryset.filter(report_from__range=(start, end)).exclude(total_orders=0)
        qs = filtered_qs.values('driver_id').annotate(
            total_kasa=Sum('total_kasa'),
            full_name=Concat(F("driver__user_ptr__name"),
                             Value(" "),
                             F("driver__user_ptr__second_name"), output_field=CharField()),
            orders=Sum('total_orders'),
            average_price=Avg('average_price'),
            accept_percent=Avg('accept_percent'),
            road_time=Coalesce(Sum('road_time'), timedelta()),
            efficiency=Avg('efficiency'),
            mileage=Sum('mileage'),

        )

        return [{'start': format_start, 'end': format_end, 'drivers_efficiency': qs}]


class CarsInformationListView(CombinedPermissionsMixin,
                              generics.ListAPIView):
    serializer_class = CarDetailSerializer

    def get_queryset(self):
        investor_queryset = InvestorFilterMixin.get_queryset(self, Vehicle)
        if investor_queryset:
            queryset = investor_queryset
            queryset = queryset.values('licence_plate').annotate(
                price=F('purchase_price'),
                kasa=ExpressionWrapper(Round(Sum('carefficiency__total_kasa') * F('investor_percentage'), 2),
                                       output_field=DecimalField(decimal_places=2, max_digits=10)),
                spending=Sum('carefficiency__total_spending')
            ).annotate(
                progress_percentage=ExpressionWrapper(
                    Case(
                        When(purchase_price__gt=0, then=Round((F('kasa') / F('purchase_price')) * 100)),
                        default=Value(0),
                        output_field=DecimalField(max_digits=5, decimal_places=2)
                    ),
                    output_field=DecimalField(max_digits=5, decimal_places=2)
                )
            )
        else:
            queryset = ManagerFilterMixin.get_queryset(self, Vehicle)
            queryset = queryset.values('licence_plate').annotate(
                price=F('purchase_price'),
                kasa=Sum('carefficiency__total_kasa'),
                spending=Sum('carefficiency__total_spending')
            ).annotate(
                progress_percentage=ExpressionWrapper(
                    Case(
                        When(purchase_price__gt=0,
                             then=Round(((F('kasa') - F('spending')) / F('purchase_price')) * 100)),
                        default=Value(0),
                        output_field=DecimalField(max_digits=4, decimal_places=1)
                    ),
                    output_field=DecimalField(max_digits=4, decimal_places=1)
                )
            )
        return queryset
