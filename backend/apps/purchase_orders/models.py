import uuid
from decimal import Decimal
from django.db import models
from common.models import TimeStampedModel
from apps.vendors.models import Vendor

class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ISSUED = 'ISSUED', 'Issued'
        PARTIALLY_RECEIVED = 'PARTIALLY_RECEIVED', 'Partially Received'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True, db_index=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ISSUED, db_index=True)
    currency = models.CharField(max_length=3, default='INR')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    issue_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_purchase_orders'
        ordering = ['-issue_date']

    def __str__(self):
        return f"PO {self.po_number} - {self.vendor.name} (₹{self.total_amount})"


class POItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    line_number = models.PositiveIntegerField(default=1)
    item_code = models.CharField(max_length=50, blank=True, default='')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=20, default='NOS')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'), help_text='GST % (e.g. 18.00 for 18%)')
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = 'ap_po_items'
        ordering = ['line_number']

    def __str__(self):
        return f"{self.po.po_number} #{self.line_number}: {self.description}"
