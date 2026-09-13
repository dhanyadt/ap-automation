from rest_framework import serializers

from .models import ValidationResult


class ValidationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationResult
        fields = ['id', 'invoice', 'rule_code', 'rule_name', 'severity', 'message', 'details', 'created_at']
        read_only_fields = fields
