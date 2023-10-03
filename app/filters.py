from django.contrib import admin

from app.models import CarEfficiency, Vehicle, DriverEfficiency, Driver, RentInformation, \
    TransactionsConversation, SummaryReport, Payments


class VehicleEfficiencyUserFilter(admin.SimpleListFilter):
    title = 'номером автомобіля'
    parameter_name = 'efficiency_vehicle_partner_user'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = CarEfficiency.objects.all()
        if user.groups.filter(name='Manager').exists():
            queryset = Vehicle.objects.filter(manager__user=user)
            vehicle_ids = set(queryset.values_list('id', flat=True))
            vehicle_labels = set(queryset.values_list('licence_plate', flat=True))
        else:
            if user.groups.filter(name='Partner').exists():
                queryset = CarEfficiency.objects.filter(partner__user=user)
            vehicle_ids = set(queryset.values_list('vehicle_id', flat=True))
            vehicle_labels = set(queryset.values_list('vehicle__licence_plate', flat=True))
        return zip(vehicle_ids, vehicle_labels)

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(vehicle__id=value)


class TransactionInvestorUserFilter(admin.SimpleListFilter):
    title = 'номером автомобіля'
    parameter_name = 'transaction_investor_user'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = TransactionsConversation.objects.all()
        if user.groups.filter(name='Investor').exists():
            queryset = Vehicle.objects.filter(investor_car__user=user)
            vehicle_ids = set(queryset.values_list('id', flat=True))
            vehicle_labels = set(queryset.values_list('licence_plate', flat=True))
        else:
            if user.groups.filter(name='Partner').exists():
                queryset = TransactionsConversation.objects.filter(investor__partner__user=user)
            vehicle_ids = set(queryset.values_list('vehicle_id', flat=True))
            vehicle_labels = set(queryset.values_list('vehicle__licence_plate', flat=True))
        return zip(vehicle_ids, vehicle_labels)

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(vehicle__id=value)


class VehicleManagerFilter(admin.SimpleListFilter):
    parameter_name = 'vehicle_manager_user'
    title = 'менеджером'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = Vehicle.objects.exclude(manager__isnull=False)
        if user.groups.filter(name='Partner').exists():
            queryset = queryset.filter(partner__user=user)

        manager_ids = set(queryset.values_list('manager_id', flat=True))
        manager_labels = set([f'{item.manager.first_name} {item.manager.last_name}' for item in queryset])
        return zip(manager_ids, manager_labels)

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(manager__id=value)


class DriverRelatedFilter(admin.SimpleListFilter):
    parameter_name = None
    model_class = None
    title = 'водієм'

    def lookups(self, request, model_admin):
        user = request.user
        queryset = self.model_class.objects.exclude(driver__isnull=False)
        if user.groups.filter(name='Manager').exists():
            queryset = Driver.objects.filter(manager__user=user)
            driver_ids = set(queryset.values_list('id', flat=True))
            driver_labels = set([f'{item.name} {item.second_name}' for item in queryset])
        else:
            if user.groups.filter(name='Partner').exists():
                queryset = self.model_class.objects.filter(partner__user=user, driver__isnull=False)
            driver_ids = set(queryset.values_list('driver_id', flat=True))
            driver_labels = set([f'{item.driver.name} {item.driver.second_name}' for item in queryset])
        return zip(driver_ids, driver_labels)

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(driver__id=value)


class DriverEfficiencyUserFilter(DriverRelatedFilter):
    parameter_name = 'driver_efficiency_user'
    model_class = DriverEfficiency


class RentInformationUserFilter(DriverRelatedFilter):
    parameter_name = 'rent_information_user'
    model_class = RentInformation


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
            queryset = self.model_class.objects.filter(full_name__in=full_names)
        else:
            if user.groups.filter(name='Partner').exists():
                queryset = self.model_class.objects.filter(partner__user=user)
        driver_labels = set([driver.full_name for driver in queryset])
        return [(full_name, full_name) for full_name in driver_labels]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(full_name=value)


class SummaryReportUserFilter(PaymentsRelatedFilter):
    parameter_name = 'summary_report_user'
    model_class = SummaryReport


class ReportUserFilter(PaymentsRelatedFilter):
    parameter_name = 'payment_report_user'
    model_class = Payments
