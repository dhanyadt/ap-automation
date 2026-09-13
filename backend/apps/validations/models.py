import uuid
from django.db import models
from common.models import TimeStampedModel
from apps.invoices.models import Invoice

class ValidationResult(TimeStampedModel):
    class Severity(models.TextChoices):
        PASSED = 'PASSED', 'Passed'
        WARNING = 'WARNING', 'Warning'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='validation_results')
    rule_code = models.CharField(max_length=100, db_index=True)
    rule_name = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.PASSED, db_index=True)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'ap_validation_results'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.rule_code} [{self.severity}]: {self.message[:60]}"
