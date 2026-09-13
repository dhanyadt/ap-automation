import uuid
from django.db import models
from common.models import TimeStampedModel
from apps.invoices.models import Invoice
from apps.purchase_orders.models import PurchaseOrder
from apps.goods_receipts.models import GoodsReceipt

class MatchRun(TimeStampedModel):
    class MatchType(models.TextChoices):
        TWO_WAY = '2_WAY', '2-Way Match (PO <-> Invoice)'
        THREE_WAY = '3_WAY', '3-Way Match (PO <-> GRN <-> Invoice)'

    class Status(models.TextChoices):
        MATCHED = 'MATCHED', 'Fully Matched'
        PARTIAL_MATCH = 'PARTIAL_MATCH', 'Partial Match within Tolerance'
        MISMATCH = 'MISMATCH', 'Mismatch / Exception'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='match_runs')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.SET_NULL, null=True, blank=True)
    match_type = models.CharField(max_length=20, choices=MatchType.choices, default=MatchType.THREE_WAY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.MISMATCH)
    is_successful = models.BooleanField(default=False)
    summary = models.TextField(blank=True, default='')
    discrepancies = models.JSONField(default=list, blank=True, help_text='List of variance details')

    class Meta:
        db_table = 'ap_match_runs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_match_type_display()} for Invoice {self.invoice.invoice_number}: {self.status}"
