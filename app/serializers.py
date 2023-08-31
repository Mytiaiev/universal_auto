from rest_framework import serializers
from app.models import Order, Payments, RentInformation, SummaryReport, Driver, Vehicle, Manager, Comment, \
    CarEfficiency

return_value = ("-", "0", 0)


class ProcessNullValue:
    def process_null_value(self, value, zero=False, t_int=False):
        result = return_value[0]
        if zero:
            result = return_value[2] if t_int else return_value[1]
        return result if value is None else value


class OrderSerializer(serializers.ModelSerializer, ProcessNullValue):
    comment = serializers.StringRelatedField(many=False)
    partner = serializers.StringRelatedField(many=False)

    comment = serializers.SerializerMethodField()
    distance_gps = serializers.SerializerMethodField()
    order_time = serializers.SerializerMethodField()

    def get_comment(self, obj):
        return self.process_null_value(obj.comment)

    def get_distance_gps(self, obj):
        return self.process_null_value(obj.distance_gps, zero=True)

    def get_order_time(self, obj):
        return self.process_null_value(obj.order_time)

    class Meta:
        model = Order
        fields = ('from_address', 'to_the_address',
                  'phone_number', 'car_delivery_price',
                  'sum', 'payment_method', 'order_time',
                  'status_order', 'distance_gps',
                  'distance_google', 'driver', 'comment',
                  'partner', 'created_at',
                  )


class PaymentsSerializer(serializers.ModelSerializer, ProcessNullValue):
    partner = serializers.StringRelatedField(many=False)

    total_rides = serializers.SerializerMethodField()

    def get_total_rides(self, obj):
        return self.process_null_value(obj.total_rides, zero=True, t_int=True)

    class Meta:
        model = Payments
        fields = ('report_from', 'vendor_name',
                  'total_rides', 'total_distance',
                  'total_amount_cash', 'total_amount_on_card',
                  'total_amount', 'tips',
                  'bonuses', 'fares',
                  'fee', 'total_amount_without_fee',
                  'partner', 'created_at', )


class RentInformationSerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)

    class Meta:
        model = RentInformation
        fields = ('driver', 'rent_time',
                  'rent_distance', 'created_at',
                  'partner')


class SummaryReportSerializer(serializers.ModelSerializer, ProcessNullValue):
    partner = serializers.StringRelatedField(many=False)

    fares = serializers.SerializerMethodField()
    bonuses = serializers.SerializerMethodField()
    tips = serializers.SerializerMethodField()
    total_rides = serializers.SerializerMethodField()

    def get_fares(self, obj):
        return self.process_null_value(obj.fares, zero=True, t_int=True)

    def get_bonuses(self, obj):
        return self.process_null_value(obj.bonuses, zero=True, t_int=True)

    def get_tips(self, obj):
        return self.process_null_value(obj.tips, zero=True, t_int=True)

    def get_total_rides(self, obj):
        return self.process_null_value(obj.total_rides, zero=True, t_int=True)

    class Meta:
        model = SummaryReport
        fields = ('report_from',
                  'full_name', 'total_rides',
                  'total_distance', 'total_amount_cash',
                  'total_amount_on_card',
                  'total_amount', 'tips',
                  'bonuses', 'fares',
                  'fee', 'total_amount_without_fee',
                  'partner', 'created_at')


class DriverSerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)
    manager = serializers.StringRelatedField(many=False)
    vehicle = serializers.StringRelatedField(many=False)

    class Meta:
        model = Driver
        fields = ('name', 'second_name',
                  'vehicle', 'phone_number', 'chat_id',
                  'schema', 'plan', 'rental',
                  'driver_status', 'manager', 'email',
                  'partner', 'created_at')


class VehicleSerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)
    manager = serializers.StringRelatedField(many=False)

    class Meta:
        model = Vehicle
        fields = ('id', 'name',
                  'licence_plate', 'type', 'vin_code',
                  'gps_imei', 'car_status',
                  'manager', 'partner', 'created_at',
        )


class ManagerSerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)

    class Meta:
        model = Manager
        fields = ('id', 'name', 'second_name', 'email',
                  'phone_number', 'chat_id', 'partner',
                  'created_at')


class CommentSerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)

    class Meta:
        model = Comment
        fields = ('comment', 'chat_id',
                  'processed', 'partner',
                  'created_at')


class CarEfficiencySerializer(serializers.ModelSerializer):
    partner = serializers.StringRelatedField(many=False)

    class Meta:
        model = CarEfficiency
        fields = ('driver', 'total_kasa', 'licence_plate',
                  'efficiency', 'mileage', 'report_from',
                  'partner')







