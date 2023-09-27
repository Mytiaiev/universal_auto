from rest_framework import serializers


class AggregateReportSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    total_kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cash = serializers.DecimalField(max_digits=10, decimal_places=2)


class CarEfficiencyDataSerializer(serializers.Serializer):
    report_from = serializers.DateField()
    licence_plate = serializers.CharField()
    mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    efficiency = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        fields = ("report_from", "licence_plate", "mileage", "efficiency")


class CarDetailSerializer(serializers.Serializer):
    licence_plate = serializers.CharField()
    price = serializers.IntegerField()
    kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    spending = serializers.DecimalField(max_digits=10, decimal_places=2)
    progress_percentage = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        fields = ('licence_plate', 'price', 'kasa', 'spending', 'progress_percentage')


class DriverEfficiencySerializer(serializers.Serializer):
    full_name = serializers.CharField()
    total_kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders = serializers.IntegerField()
    accept_percent = serializers.IntegerField()
    road_time = serializers.DurationField()
    efficiency = serializers.DecimalField(max_digits=10, decimal_places=2)
    mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    rent_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        fields = ('full_name', 'total_kasa', 'total_orders',
                  'accept_percent', 'average_price', 'road_time',
                  'efficiency', 'mileage', 'rent_amount')


class DriverEfficiencyRentSerializer(serializers.Serializer):
    total_rent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    drivers_efficiency = DriverEfficiencySerializer(many=True)


class CarEfficiencySerializer(serializers.Serializer):
    efficiency = CarEfficiencyDataSerializer(many=True)
    total_mileage = serializers.DecimalField(max_digits=10, decimal_places=2)


class SummaryReportSerializer(serializers.Serializer):
    drivers = AggregateReportSerializer(many=True)
    kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
