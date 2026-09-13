from rest_framework import serializers
from .models import Vendor, VendorBankAccount

class VendorBankAccountSerializer(serializers.ModelSerializer):
    # Masked account number exposed publicly; raw account number is write-only
    account_number = serializers.CharField(write_only=True, required=False)
    masked_account_number = serializers.CharField(read_only=True)

    class Meta:
        model = VendorBankAccount
        fields = [
            'id',
            'vendor',
            'bank_name',
            'account_number',
            'masked_account_number',
            'ifsc_code',
            'branch_name',
            'is_primary',
            'is_verified',
            'created_at',
        ]
        read_only_fields = ['id', 'vendor', 'masked_account_number', 'created_at']

    def create(self, validated_data):
        return super().create(validated_data)


class VendorSerializer(serializers.ModelSerializer):
    bank_accounts = VendorBankAccountSerializer(many=True, read_only=True)
    purchase_orders_count = serializers.IntegerField(source='purchase_orders.count', read_only=True)
    invoices_count = serializers.IntegerField(source='invoices.count', read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'id',
            'name',
            'code',
            'gstin',
            'pan',
            'email',
            'phone',
            'address_line1',
            'city',
            'state',
            'pincode',
            'status',
            'msme_registered',
            'payment_terms_days',
            'bank_accounts',
            'purchase_orders_count',
            'invoices_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'purchase_orders_count', 'invoices_count']

    def validate_code(self, value):
        instance = getattr(self, 'instance', None)
        qs = Vendor.objects.filter(code__iexact=value)
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError("A vendor with this code already exists.")
        return value.upper().strip()

    def validate_gstin(self, value):
        if value:
            cleaned = value.strip().upper()
            if len(cleaned) != 15:
                raise serializers.ValidationError("Indian GSTIN must be exactly 15 characters long.")
            return cleaned
        return value
