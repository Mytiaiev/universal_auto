from django.contrib import admin

from app.models import CarEfficiency, Vehicle, DriverEfficiency, Driver, RentInformation, \
    TransactionsConversation, SummaryReport, Payments, FleetOrder


class VehicleEfficiencyUserFilter(admin.SimpleListFilter):
    title = 'номером автомобіля'
    parameter_name = 'efficiency_vehicle_partner_user'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = CarEfficiency.objects.all()
        vehicle_choices = []
        if user.groups.filter(name='Manager').exists():
            vehicles = Vehicle.objects.filter(manager__user=user)
            queryset = queryset.filter(vehicle__in=vehicles)
        if user.groups.filter(name='Partner').exists():
            queryset = queryset.filter(partner__user=user)
        if user.groups.filter(name='Investor').exists():
            vehicles = Vehicle.objects.filter(investor_car__user=user)
            queryset = queryset.filter(vehicle__in=vehicles)
        vehicle_choices.extend(queryset.values_list('vehicle_id', 'vehicle__licence_plate'))
        return sorted(set(vehicle_choices), key=lambda x: x[1])

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(vehicle__id=int(value))


class TransactionInvestorUserFilter(admin.SimpleListFilter):
    title = 'номером автомобіля'
    parameter_name = 'transaction_investor_user'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = TransactionsConversation.objects.all()
        vehicle_choices = []
        if user.groups.filter(name='Investor').exists():
            vehicles = Vehicle.objects.filter(investor_car__user=user)
            queryset.filter(vehicle__in=vehicles)
        if user.groups.filter(name='Partner').exists():
            queryset = TransactionsConversation.objects.filter(investor__partner__user=user)
        vehicle_choices.extend(queryset.values_list('vehicle_id', 'vehicle__licence_plate'))
        return sorted(set(vehicle_choices), key=lambda x: x[1])

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(vehicle__id=int(value))


class VehicleManagerFilter(admin.SimpleListFilter):
    parameter_name = 'vehicle_manager_user'
    title = 'менеджером'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = Vehicle.objects.exclude(manager__isnull=True)
        if not user.groups.filter(name__in=('Manager', 'Investor')).exists():
            if user.groups.filter(name='Partner').exists():
                queryset = queryset.filter(partner__user=user)
            manager_ids = queryset.values_list('manager_id', flat=True)
            manager_labels = [f'{item.manager.first_name} {item.manager.last_name}' for item in queryset]
            return set(zip(manager_ids, manager_labels))

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            if not request.user.groups.filter(name__in=('Manager', 'Investor')).exists():
                return queryset.filter(manager__id=value)


class DriverRelatedFilter(admin.SimpleListFilter):
    parameter_name = None
    model_class = None
    title = 'водієм'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = self.model_class.objects.exclude(driver__isnull=True)
        if user.groups.filter(name='Manager').exists():
            drivers = Driver.objects.filter(manager__user=user)
            queryset = queryset.filter(driver__in=drivers)
        if user.groups.filter(name='Partner').exists():
            queryset = queryset.filter(partner__user=user)
        driver_ids = queryset.values_list('driver_id', flat=True)
        driver_labels = [f'{item.driver.name} {item.driver.second_name}' for item in queryset]
        return set(zip(driver_ids, driver_labels))

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(driver__id=value)


class DriverEfficiencyUserFilter(DriverRelatedFilter):
    parameter_name = 'driver_efficiency_user'
    model_class = DriverEfficiency


class SummaryReportUserFilter(DriverRelatedFilter):
    parameter_name = 'summary_report_user'
    model_class = SummaryReport


class RentInformationUserFilter(DriverRelatedFilter):
    parameter_name = 'rent_information_user'
    model_class = RentInformation


class FleetOrderFilter(DriverRelatedFilter):
    parameter_name = 'fleet_order_user'
    model_class = FleetOrder


class PaymentsRelatedFilter(admin.SimpleListFilter):
    parameter_name = None
    model_class = None
    title = 'водієм'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = self.model_class.objects.all()
        if user.groups.filter(name='Manager').exists():
            drivers = Driver.objects.filter(manager__user=user)
            full_names = [f"{driver.name} {driver.second_name}" for driver in drivers]
            queryset = queryset.filter(full_name__in=full_names)
        if user.groups.filter(name='Partner').exists():
            queryset = queryset.filter(partner__user=user)

        driver_labels = set([driver.full_name for driver in queryset])
        return [(full_name, full_name) for full_name in driver_labels]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(full_name=value)





class ReportUserFilter(PaymentsRelatedFilter):
    parameter_name = 'payment_report_user'
    model_class = Payments
