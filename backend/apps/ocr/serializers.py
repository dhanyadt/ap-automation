from rest_framework import serializers

from .models import OCRJob


class OCRJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRJob
        fields = [
            'id', 'invoice', 'provider_name', 'status', 'average_confidence',
            'extracted_fields', 'raw_text', 'processing_time_ms', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields
