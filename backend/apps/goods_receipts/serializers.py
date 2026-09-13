from decimal import Decimal
from rest_framework import serializers
from apps.purchase_orders.models import PurchaseOrder, POItem
from .models import GoodsReceipt, GRNItem

class GRNItemSerializer(serializers.ModelSerializer):
    po_item_description = serializers.CharField(source='po_item.description', read_only=True)
    po_item_code = serializers.CharField(source='po_item.item_code', read_only=True)
    po_ordered_quantity = serializers.DecimalField(source='po_item.quantity', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = GRNItem
        fields = [
            'id',
            'po_item',
            'po_item_description',
            'po_item_code',
            'po_ordered_quantity',
            'received_quantity',
            'accepted_quantity',
            'rejected_quantity',
            'remarks',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        recv = Decimal(str(attrs.get('received_quantity', 0)))
        acc = Decimal(str(attrs.get('accepted_quantity', recv)))
        rej = Decimal(str(attrs.get('rejected_quantity', 0)))

        if recv < Decimal('0'):
            raise serializers.ValidationError("Received quantity cannot be negative.")
        if acc < Decimal('0') or rej < Decimal('0'):
            raise serializers.ValidationError("Accepted and rejected quantities cannot be negative.")
        if (acc + rej) > recv:
            raise serializers.ValidationError("Accepted + rejected quantities cannot exceed received quantity.")

        po_item = attrs.get('po_item')
        if po_item and recv > (po_item.quantity * Decimal('1.20')): # Allow up to 20% over-delivery tolerance
            raise serializers.ValidationError(
                f"Received quantity ({recv}) significantly exceeds the PO quantity ({po_item.quantity}) beyond allowable tolerance."
            )

        return attrs


class GoodsReceiptSerializer(serializers.ModelSerializer):
    items = GRNItemSerializer(many=True, required=False)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    vendor_name = serializers.CharField(source='purchase_order.vendor.name', read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = [
            'id',
            'grn_number',
            'purchase_order',
            'po_number',
            'vendor_name',
            'status',
            'received_date',
            'delivery_challan_number',
            'received_by',
            'notes',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_grn_number(self, value):
        instance = getattr(self, 'instance', None)
        qs = GoodsReceipt.objects.filter(grn_number__iexact=value)
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError("A GRN with this number already exists.")
        return value.upper().strip()

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        grn = GoodsReceipt.objects.create(**validated_data)

        for item_data in items_data:
            GRNItem.objects.create(
                goods_receipt=grn,
                po_item=item_data['po_item'],
                received_quantity=item_data['received_quantity'],
                accepted_quantity=item_data.get('accepted_quantity', item_data['received_quantity']),
                rejected_quantity=item_data.get('rejected_quantity', 0),
                remarks=item_data.get('remarks', '')
            )
        return grn

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                GRNItem.objects.create(
                    goods_receipt=instance,
                    po_item=item_data['po_item'],
                    received_quantity=item_data['received_quantity'],
                    accepted_quantity=item_data.get('accepted_quantity', item_data['received_quantity']),
                    rejected_quantity=item_data.get('rejected_quantity', 0),
                    remarks=item_data.get('remarks', '')
                )
        return instance
