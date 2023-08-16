from rest_framework import serializers
from app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    comment = serializers.StringRelatedField(many=False)

    class Meta:
        model = Order
        fields = ('from_address', 'to_the_address',
                  'phone_number', 'car_delivery_price',
                  'sum', 'payment_method', 'order_time',
                  'status_order', 'distance_gps',
                  'distance_google', 'driver', 'comment',
                  'partner', 'created_at',
                  )

