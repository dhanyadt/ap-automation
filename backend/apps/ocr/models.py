import uuid
from decimal import Decimal
from django.db import models
from common.models import TimeStampedModel
from apps.invoices.models import Invoice

class OCRJob(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='ocr_jobs')
    provider_name = models.CharField(max_length=50, default='MockOCRProvider')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    average_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    extracted_fields = models.JSONField(default=dict, blank=True)
    raw_text = models.TextField(blank=True, default='')
    processing_time_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_ocr_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"OCR Job {self.id} for {self.invoice.id} ({self.status})"
