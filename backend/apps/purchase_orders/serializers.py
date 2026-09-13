from decimal import Decimal
from rest_framework import serializers
from apps.vendors.models import Vendor
from .models import PurchaseOrder, POItem

class POItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)

    class Meta:
        model = POItem
        fields = [
            'id',
            'line_number',
            'item_code',
            'description',
            'quantity',
            'unit_of_measure',
            'unit_price',
            'tax_rate',
            'line_total',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        qty = attrs.get('quantity')
        price = attrs.get('unit_price')
        if qty is not None and price is not None:
            attrs['line_total'] = (Decimal(str(qty)) * Decimal(str(price))).quantize(Decimal('0.01'))
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = POItemSerializer(many=True, required=False)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_code = serializers.CharField(source='vendor.code', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id',
            'po_number',
            'vendor',
            'vendor_name',
            'vendor_code',
            'status',
            'currency',
            'subtotal',
            'tax_amount',
            'total_amount',
            'issue_date',
            'delivery_date',
            'notes',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_po_number(self, value):
        instance = getattr(self, 'instance', None)
        qs = PurchaseOrder.objects.filter(po_number__iexact=value)
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError("A purchase order with this number already exists.")
        return value.upper().strip()

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        po = PurchaseOrder.objects.create(**validated_data)
        
        calculated_subtotal = Decimal('0.00')
        calculated_tax = Decimal('0.00')

        for idx, item_data in enumerate(items_data, start=1):
            qty = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(item_data['unit_price']))
            tax_rate = Decimal(str(item_data.get('tax_rate', '18.00')))
            
            line_subtotal = (qty * unit_price).quantize(Decimal('0.01'))
            item_tax = ((line_subtotal * tax_rate) / Decimal('100.00')).quantize(Decimal('0.01'))
            line_total = line_subtotal + item_tax

            calculated_subtotal += line_subtotal
            calculated_tax += item_tax

            POItem.objects.create(
                po=po,
                line_number=item_data.get('line_number', idx),
                item_code=item_data.get('item_code', ''),
                description=item_data['description'],
                quantity=qty,
                unit_of_measure=item_data.get('unit_of_measure', 'NOS'),
                unit_price=unit_price,
                tax_rate=tax_rate,
                line_total=line_total,
            )

        # If subtotal / total were not manually specified, use computed values
        if po.subtotal == Decimal('0.00') and calculated_subtotal > Decimal('0.00'):
            po.subtotal = calculated_subtotal
            po.tax_amount = calculated_tax
            po.total_amount = calculated_subtotal + calculated_tax
            po.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

        return po

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            calculated_subtotal = Decimal('0.00')
            calculated_tax = Decimal('0.00')
            for idx, item_data in enumerate(items_data, start=1):
                qty = Decimal(str(item_data['quantity']))
                unit_price = Decimal(str(item_data['unit_price']))
                tax_rate = Decimal(str(item_data.get('tax_rate', '18.00')))
                line_subtotal = (qty * unit_price).quantize(Decimal('0.01'))
                item_tax = ((line_subtotal * tax_rate) / Decimal('100.00')).quantize(Decimal('0.01'))
                line_total = line_subtotal + item_tax

                calculated_subtotal += line_subtotal
                calculated_tax += item_tax

                POItem.objects.create(
                    po=instance,
                    line_number=item_data.get('line_number', idx),
                    item_code=item_data.get('item_code', ''),
                    description=item_data['description'],
                    quantity=qty,
                    unit_of_measure=item_data.get('unit_of_measure', 'NOS'),
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    line_total=line_total,
                )
            instance.subtotal = calculated_subtotal
            instance.tax_amount = calculated_tax
            instance.total_amount = calculated_subtotal + calculated_tax
            instance.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

        return instance
