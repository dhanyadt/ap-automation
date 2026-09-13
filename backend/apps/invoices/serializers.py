import os
from decimal import Decimal
from rest_framework import serializers
from django.conf import settings
from common.utils import get_indian_fiscal_year
from apps.vendors.models import Vendor
from apps.purchase_orders.models import PurchaseOrder
from apps.ocr.serializers import OCRJobSerializer
from apps.validations.serializers import ValidationResultSerializer
from apps.matching.serializers import MatchRunSerializer
from .models import Invoice, InvoiceItem

class InvoiceItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'line_number',
            'description',
            'hsn_sac_code',
            'quantity',
            'unit_of_measure',
            'unit_price',
            'tax_rate',
            'tax_amount',
            'line_total',
            'matched_po_item',
            'matched_grn_item',
            'confidence_score',
        ]
        read_only_fields = ['id', 'tax_amount', 'line_total', 'matched_po_item', 'matched_grn_item', 'confidence_score']

    def validate(self, attrs):
        qty = attrs.get('quantity')
        price = attrs.get('unit_price')
        tax_rate = attrs.get('tax_rate', Decimal('18.00'))

        if qty is not None and price is not None:
            subtotal = (Decimal(str(qty)) * Decimal(str(price))).quantize(Decimal('0.01'))
            tax = ((subtotal * Decimal(str(tax_rate))) / Decimal('100.00')).quantize(Decimal('0.01'))
            attrs['tax_amount'] = tax
            attrs['line_total'] = subtotal + tax
        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)
    original_filename = serializers.CharField(required=False, allow_blank=True)
    items = InvoiceItemSerializer(many=True, required=False)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_code = serializers.CharField(source='vendor.code', read_only=True)
    file_url = serializers.SerializerMethodField()
    ocr_jobs = OCRJobSerializer(many=True, read_only=True)
    validation_results = ValidationResultSerializer(many=True, read_only=True)
    match_runs = MatchRunSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'original_filename',
            'file',
            'file_url',
            'file_size',
            'content_type',
            'pages_count',
            'vendor',
            'vendor_name',
            'vendor_code',
            'vendor_name_extracted',
            'vendor_gstin_extracted',
            'invoice_number',
            'fiscal_year',
            'invoice_date',
            'due_date',
            'currency',
            'subtotal',
            'tax_amount',
            'total_amount',
            'po_number',
            'purchase_order',
            'processing_status',
            'ocr_status',
            'validation_status',
            'matching_status',
            'approval_status',
            'payment_status',
            'ocr_confidence',
            'notes',
            'items',
            'ocr_jobs',
            'validation_results',
            'match_runs',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_url',
            'created_at',
            'updated_at',
            'processing_status',
            'ocr_status',
            'validation_status',
            'matching_status',
            'approval_status',
            'payment_status',
            'ocr_confidence',
            'vendor_name_extracted',
            'vendor_gstin_extracted',
        ]

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate(self, attrs):
        vendor = attrs.get('vendor') or getattr(self.instance, 'vendor', None)
        invoice_number = attrs.get('invoice_number') or getattr(self.instance, 'invoice_number', '')
        fiscal_year = attrs.get('fiscal_year') or getattr(self.instance, 'fiscal_year', '')

        # Auto-compute fiscal year from invoice_date if absent
        if not fiscal_year:
            inv_date = attrs.get('invoice_date') or getattr(self.instance, 'invoice_date', None)
            fiscal_year = get_indian_fiscal_year(inv_date)
            attrs['fiscal_year'] = fiscal_year

        # Business rule check: vendor + invoice_number + fiscal_year
        if vendor and invoice_number and fiscal_year:
            qs = Invoice.objects.filter(
                vendor=vendor,
                invoice_number__iexact=invoice_number.strip(),
                fiscal_year=fiscal_year
            )
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError({
                    'invoice_number': f"Invoice '{invoice_number}' already exists for vendor '{vendor.name}' in {fiscal_year}."
                })
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance


class InvoiceUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    vendor = serializers.UUIDField(required=False, allow_null=True)
    po_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')

    def validate_file(self, file_obj):
        # 1. Size Validation
        max_bytes = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 15 * 1024 * 1024)
        if file_obj.size > max_bytes:
            raise serializers.ValidationError(f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

        # 2. Extension Validation
        ext = os.path.splitext(file_obj.name)[1].lower()
        allowed_extensions = getattr(settings, 'ALLOWED_INVOICE_EXTENSIONS', ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif'])
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_extensions)}")

        # 3. Content-Type Validation
        allowed_types = getattr(settings, 'ALLOWED_INVOICE_CONTENT_TYPES', [
            'application/pdf', 'image/jpeg', 'image/png', 'image/tiff'
        ])
        content_type = getattr(file_obj, 'content_type', '')
        if content_type and content_type not in allowed_types:
            raise serializers.ValidationError(f"Unsupported MIME type '{content_type}'.")

        return file_obj
