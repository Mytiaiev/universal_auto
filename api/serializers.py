from rest_framework import serializers


class AggregateReportSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    total_kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_card = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cash = serializers.DecimalField(max_digits=10, decimal_places=2)


class CarDetailSerializer(serializers.Serializer):
    licence_plate = serializers.CharField()
    price = serializers.IntegerField()
    kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    spending = serializers.DecimalField(max_digits=10, decimal_places=2)
    progress_percentage = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        fields = ("licence_plate", "price", "kasa", "spending", "progress_percentage")


class DriverEfficiencySerializer(serializers.Serializer):
    full_name = serializers.CharField()
    total_kasa = serializers.DecimalField(max_digits=10, decimal_places=2)
    orders = serializers.IntegerField()
    accept_percent = serializers.IntegerField()
    road_time = serializers.DurationField()
    efficiency = serializers.DecimalField(max_digits=10, decimal_places=2)
    mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    rent_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        fields = (
            "full_name",
            "total_kasa",
            "total_orders",
            "accept_percent",
            "average_price",
            "road_time",
            "efficiency",
            "mileage",
            "rent_amount",
        )


class DriverEfficiencyRentSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    drivers_efficiency = DriverEfficiencySerializer(many=True)


class VehiclesEfficiencySerializer(serializers.Serializer):
    efficiency = serializers.ListField(child=serializers.FloatField())
    mileage = serializers.ListField(child=serializers.FloatField())


class CarEfficiencySerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.DateField())
    vehicles = VehiclesEfficiencySerializer(many=True)
    total_mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_efficiency = serializers.DecimalField(max_digits=10, decimal_places=2)
    kasa = serializers.DecimalField(max_digits=10, decimal_places=2)


class SummaryReportSerializer(serializers.Serializer):
    drivers = AggregateReportSerializer(many=True)
    total_rent = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    start = serializers.CharField()
    end = serializers.CharField()


class CarEarningsSerializer(serializers.Serializer):
    licence_plate = serializers.CharField()
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    mileage = serializers.DecimalField(max_digits=10, decimal_places=2)


class TotalEarningsSerializer(serializers.Serializer):
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_spending = serializers.DecimalField(max_digits=10, decimal_places=2)


class InvestorCarsSerializer(serializers.Serializer):
    car_earnings = CarEarningsSerializer(many=True)
    totals = TotalEarningsSerializer()
    start = serializers.CharField()
    end = serializers.CharField()
