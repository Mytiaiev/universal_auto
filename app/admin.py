from django.contrib import admin
from .models import *
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter


class FleetChildAdmin(PolymorphicChildModelAdmin):
    base_model = Fleet 
    show_in_index = False


@admin.register(UberFleet)
class UberFleetAdmin(FleetChildAdmin):
    base_model = UberFleet
    show_in_index = False


@admin.register(BoltFleet)
class BoltFleetAdmin(FleetChildAdmin):
    base_model = BoltFleet
    show_in_index = False


@admin.register(UklonFleet)
class UklonFleetAdmin(FleetChildAdmin):
    base_model = UklonFleet
    show_in_index = False

@admin.register(NewUklonFleet)
class UklonFleetAdmin(FleetChildAdmin):
    base_model = NewUklonFleet
    show_in_index = False


@admin.register(Fleet)
class FleetParentAdmin(PolymorphicParentModelAdmin):
    base_model = Fleet 
    child_models = (UberFleet, BoltFleet, UklonFleet, NewUklonFleet)
    list_filter = (PolymorphicChildModelFilter,)
    

admin.site.register(User)
admin.site.register(Driver)
admin.site.register(Client)
#admin.site.register(Partner)
admin.site.register(DriverManager)
admin.site.register(ServiceStationManager)
admin.site.register(SupportManager)
admin.site.register(Vehicle)
admin.site.register(Fleets_drivers_vehicles_rate)
