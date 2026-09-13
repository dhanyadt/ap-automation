import uuid
from decimal import Decimal
from django.db import models
from common.models import TimeStampedModel
from apps.accounts.models import User
from apps.invoices.models import Invoice
from apps.vendors.models import Vendor

class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        NEFT = 'NEFT', 'NEFT'
        RTGS = 'RTGS', 'RTGS'
        IMPS = 'IMPS', 'IMPS'
        ACH = 'ACH', 'ACH / Wire'

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Payment Requested'
        PROCESSING = 'PROCESSING', 'Processing with Bank'
        PAID = 'PAID', 'Payment Settled / Paid'
        FAILED = 'FAILED', 'Payment Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=20, choices=Method.choices, default=Method.NEFT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    reference_number = models.CharField(max_length=100, blank=True, default='', db_index=True, help_text='Bank UTR Number or Transaction Ref')
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_payments')
    paid_at = models.DateTimeField(null=True, blank=True)
    bank_response_payload = models.JSONField(default=dict, blank=True)
    advice_notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.reference_number or self.id} - ₹{self.amount} ({self.status})"
