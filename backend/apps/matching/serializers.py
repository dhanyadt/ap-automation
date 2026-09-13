from rest_framework import serializers

from .models import MatchRun


class MatchRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRun
        fields = [
            'id', 'invoice', 'purchase_order', 'goods_receipt', 'match_type',
            'status', 'is_successful', 'summary', 'discrepancies', 'created_at',
        ]
        read_only_fields = fields
