from django.contrib import admin
from .models import *
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from django.utils.safestring import mark_safe

# class FleetChildAdmin(PolymorphicChildModelAdmin):
#     base_model = Fleet
#     show_in_index = False
#
#
# @admin.register(UberFleet)
# class UberFleetAdmin(FleetChildAdmin):
#     base_model = UberFleet
#     show_in_index = False
#
#
# @admin.register(BoltFleet)
# class BoltFleetAdmin(FleetChildAdmin):
#     base_model = BoltFleet
#     show_in_index = False
#
#
# @admin.register(UklonFleet)
# class UklonFleetAdmin(FleetChildAdmin):
#     base_model = UklonFleet
#     show_in_index = False
#
# @admin.register(NewUklonFleet)
# class UklonFleetAdmin(FleetChildAdmin):
#     base_model = NewUklonFleet
#     show_in_index = False
#
#
# @admin.register(Fleet)
# class FleetParentAdmin(PolymorphicParentModelAdmin):
#     base_model = Fleet
#     child_models = (UberFleet, BoltFleet, UklonFleet, NewUklonFleet)
#     list_filter = (PolymorphicChildModelFilter,)


class DriverManagerInline(admin.TabularInline):
    model = DriverManager.driver_id.through
    extra = 0

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        if parent_model is Driver:
            self.verbose_name = 'Менеджер'
            self.verbose_name_plural = 'Менеджери'
        if parent_model is DriverManager:
            self.verbose_name = 'Водій'
            self.verbose_name_plural = 'Водії'


class SupportManagerClientInline(admin.TabularInline):
    model = SupportManager.client_id.through
    extra = 0

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        if parent_model is Client:
            self.verbose_name = 'Менеджер служби підтримки'
            self.verbose_name_plural = 'Менеджери служби підтримки'
        if parent_model is SupportManager:
            self.verbose_name = 'Клієнт'
            self.verbose_name_plural = 'Клієнти'


class SupportManagerDriverInline(admin.TabularInline):
    model = SupportManager.driver_id.through
    extra = 0

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        if parent_model is Driver:
            self.verbose_name = 'Менеджер служби підтримки'
            self.verbose_name_plural = 'Менеджери служби підтримки'
        if parent_model is SupportManager:
            self.verbose_name = 'Водій'
            self.verbose_name_plural = 'Водії'


class ServiceStationManagerVehicleInline(admin.TabularInline):
    model = ServiceStationManager.car_id.through
    extra = 0

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        if parent_model is Vehicle:
            self.verbose_name = 'Менеджер сервісного центру'
            self.verbose_name_plural = 'Менеджери сервісного центру'
        if parent_model is ServiceStationManager:
            self.verbose_name = 'Автомобіль'
            self.verbose_name_plural = 'Автомобілі'


class ServiceStationManagerFleetInline(admin.TabularInline):
    model = ServiceStationManager.fleet_id.through
    extra = 0

    def __init__(self, parent_model, admin_site):
        super().__init__(parent_model, admin_site)
        if parent_model is Fleet:
            self.verbose_name = 'Менеджер сервісного центру'
            self.verbose_name_plural = 'Менеджери сервісного центру'
        if parent_model is ServiceStationManager:
            self.verbose_name = 'Автопарк'
            self.verbose_name_plural = 'Автопарки'


class Fleets_drivers_vehicles_rateInline(admin.TabularInline):
    model = Fleets_drivers_vehicles_rate
    extra = 0
    verbose_name = 'Fleets Drivers Vehicles Rate'
    verbose_name_plural = 'Fleets Drivers Vehicles Rate'

    fieldsets = [
        (None, {'fields': ['fleet', 'driver', 'vehicle', 'driver_external_id', 'rate']}),
    ]


@admin.register(Fleet)
class FleetAdmin(admin.ModelAdmin):
    inlines = [
        Fleets_drivers_vehicles_rateInline,
        ServiceStationManagerFleetInline
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'driver_status', 'created_at')
    list_display_links = ('name', 'second_name')
    list_filter = ['created_at']
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number', 'driver_status', 'chat_id']}),
    ]

    inlines = [
        Fleets_drivers_vehicles_rateInline,
        DriverManagerInline,
        SupportManagerDriverInline,
    ]


@admin.register(DriverRateLevels)
class DriverRateLevelsAdmin(admin.ModelAdmin):
    list_display = [f.name for f in DriverRateLevels._meta.fields]
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['fleet', 'threshold_value', 'rate_delta']}),
    ]

@admin.register(DriverManager)
class DriverManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number', 'chat_id']}),
    ]

    inlines = [
        DriverManagerInline,
    ]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'licence_plate', 'vin_code', 'type', 'gps_imei', 'car_status', 'created_at')
    list_display_links = ('name', 'model', 'licence_plate', 'vin_code')
    search_fields = ('name', 'model', 'licence_plate', 'vin_code', 'gps_imei',)
    ordering = ('name',)
    exclude = ('deleted_at',)
    list_per_page = 25

    inlines = [
        Fleets_drivers_vehicles_rateInline,
    ]


@admin.register(RawGPS)
class RawGPSAdmin(admin.ModelAdmin):
    list_display = ('imei', 'client_ip', 'client_port', 'data_', 'created_at', 'vehiclegps')
    list_display_links = ('imei', 'client_ip', 'client_port', 'data_')
    search_fields = ('imei',)
    list_filter = ('imei', 'client_ip', 'created_at')
    ordering = ('-created_at', 'imei')
    list_per_page = 25

    def data_(self, instance):
        return f'{instance.data[:100]}...'


@admin.register(VehicleGPS)
class VehicleGPSAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date_time', 'lat', 'lat_zone', 'lon', 'lon_zone', 'speed', 'course', 'height', 'created_at')
    search_fields = ('vehicle',)
    list_filter = ('vehicle', 'date_time', 'created_at')
    ordering = ('-date_time', 'vehicle')
    list_per_page = 25


@admin.register(PaymentsOrder)
class PaymentsOrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in PaymentsOrder._meta.fields]
    search_fields = ('driver_uuid', 'driver_name', 'driver_second_name')
    ordering = ('-transaction_time',)
    list_per_page = 25


@admin.register(UklonPaymentsOrder)
class UklonPaymentsOrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in UklonPaymentsOrder._meta.fields]
    search_fields = ('signal', 'licence_plate')
    ordering = ('-report_from', 'signal')
    list_per_page = 25


@admin.register(NewUklonPaymentsOrder)
class NewUklonPaymentsOrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in NewUklonPaymentsOrder._meta.fields]
    search_fields = ('signal', 'full_name')
    ordering = ('-report_from', 'signal')
    list_per_page = 25


@admin.register(BoltPaymentsOrder)
class BoltPaymentsOrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in BoltPaymentsOrder._meta.fields]
    search_fields = ('mobile_number', 'driver_full_name')
    ordering = ('-report_from', 'mobile_number')
    list_per_page = 25


@admin.register(UberPaymentsOrder)
class UberPaymentsOrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in UberPaymentsOrder._meta.fields]
    search_fields = ('driver_uuid', 'first_name', 'last_name')
    ordering = ('-report_from', 'driver_uuid')
    list_per_page = 25


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    list_filter = ['created_at']
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number']}),
    ]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    list_filter = ['created_at']
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number']}),
    ]

    inlines = [
        SupportManagerClientInline,
    ]


@admin.register(SupportManager)
class SupportManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number']}),
    ]

    inlines = [
        SupportManagerClientInline,
        SupportManagerDriverInline,
    ]


@admin.register(RepairReport)
class RepairReportAdmin(admin.ModelAdmin):
    list_display = [f.name for f in RepairReport._meta.fields]
    list_filter = ['numberplate', 'status_of_payment_repair']
    list_editable = ['status_of_payment_repair']
    search_fields = ['numberplate']
    list_per_page = 25


@admin.register(ServiceStation)
class ServiceStationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'description')
    list_display_links = ('name',)
    list_filter = ['owner']
    search_fields = ('name', 'owner')
    ordering = ('name', )
    list_per_page = 25


@admin.register(ServiceStationManager)
class ServiceStationManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'service_station', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number', 'service_station']}),
    ]

    inlines = [
        ServiceStationManagerVehicleInline,
        ServiceStationManagerFleetInline,
    ]


@admin.register(Report_of_driver_debt)
class ReportOfDriverDebtAdmin(admin.ModelAdmin):
    list_display = ('driver', 'image', 'created_at')
    list_filter = ('driver', 'created_at')
    search_fields = ('driver', 'created_at')

    fieldsets = [
        (None, {'fields': ['driver', 'image']}),
    ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'chat_id', 'processed')
    list_filter = ('chat_id', 'processed')
    list_editable = ['processed']

    fieldsets = [
        (None, {'fields': ['comment', 'chat_id']}),
    ]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('full_name_driver', 'event', 'status_event', 'created_at', 'updated_at')
    list_filter = ('full_name_driver', 'event', 'status_event')
    list_editable = ['status_event']

    fieldsets = [
        (None, {'fields': ['full_name_driver', 'event', 'chat_id']}),
    ]


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'second_name', 'email', 'phone_number', 'created_at')
    list_display_links = ('name', 'second_name')
    list_filter = ['created_at']
    search_fields = ('name', 'second_name')
    ordering = ('name', 'second_name')
    list_per_page = 25

    fieldsets = [
        (None, {'fields': ['name', 'second_name', 'email', 'phone_number', 'chat_id']}),
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Order._meta.fields]


@admin.register(Fleets_drivers_vehicles_rate)
class Fleets_drivers_vehicles_rateAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Fleets_drivers_vehicles_rate._meta.fields]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name',
                    'email', 'phone_number',
                    'license_expired', 'admin_front',
                    'admin_back', 'admin_photo', 'admin_car_document',
                    'admin_insurance', 'insurance_expired',
                    'status_bolt', 'status_uklon']

    fieldsets = [
        (None, {'fields': ['first_name', 'last_name',
                           'email', 'phone_number',
                           'license_expired', 'driver_license_front',
                           'driver_license_back', 'photo', 'car_documents',
                           'insurance', 'insurance_expired'
                           ]}),
    ]