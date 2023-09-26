from rest_framework import serializers

from app.models import SummaryReport


class SummaryReportSerializer(serializers.ModelSerializer):
    kasa = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = SummaryReport
        fields = ['full_name',
                  'total_amount_without_fee',
                  'total_amount_cash',
                  'kasa']

    def get_kasa(self, obj):
        return obj.get_kasa()