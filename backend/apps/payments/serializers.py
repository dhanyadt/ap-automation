from rest_framework import serializers

from .models import Payment
from .services import payment_advice


class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    advice = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number', 'vendor', 'vendor_name', 'amount',
            'currency', 'payment_method', 'status', 'reference_number',
            'initiated_by', 'paid_at', 'bank_response_payload', 'advice_notes',
            'advice', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_advice(self, obj):
        return payment_advice(obj)


class PaymentRequestSerializer(serializers.Serializer):
    invoice = serializers.UUIDField()
    payment_method = serializers.ChoiceField(
        choices=Payment.Method.choices,
        required=False,
        default=Payment.Method.NEFT,
    )
