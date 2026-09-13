import uuid
from django.db import models
from common.models import TimeStampedModel
from apps.invoices.models import Invoice

class ERPSyncLog(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Sync'
        SUCCESS = 'SUCCESS', 'Successfully Synced'
        FAILED = 'FAILED', 'Sync Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='erp_syncs')
    target_system = models.CharField(max_length=50, default='GenericERP')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    erp_document_number = models.CharField(max_length=100, blank=True, default='')
    payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'ap_erp_sync_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"ERP Sync for {self.invoice.invoice_number} ({self.status})"
