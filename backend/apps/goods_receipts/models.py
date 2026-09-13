import uuid
from django.db import models
from common.models import TimeStampedModel
from apps.purchase_orders.models import PurchaseOrder, POItem

class GoodsReceipt(TimeStampedModel):
    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Goods Received'
        INSPECTED = 'INSPECTED', 'Inspected'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grn_number = models.CharField(max_length=50, unique=True, db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='goods_receipts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACCEPTED, db_index=True)
    received_date = models.DateField()
    delivery_challan_number = models.CharField(max_length=50, blank=True, default='')
    received_by = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_goods_receipts'
        ordering = ['-received_date']

    def __str__(self):
        return f"GRN {self.grn_number} for {self.purchase_order.po_number}"


class GRNItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(POItem, on_delete=models.PROTECT, related_name='grn_items')
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    accepted_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rejected_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'ap_grn_items'

    def __str__(self):
        return f"{self.goods_receipt.grn_number} - {self.po_item.description}: Recv {self.received_quantity}, Acc {self.accepted_quantity}"
