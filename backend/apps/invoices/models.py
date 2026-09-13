import uuid
from decimal import Decimal
from django.db import models
from common.models import TimeStampedModel
from apps.vendors.models import Vendor
from apps.purchase_orders.models import PurchaseOrder, POItem
from apps.goods_receipts.models import GRNItem

def invoice_file_upload_path(instance, filename):
    """Generates an isolated, safe storage path using UUID."""
    ext = filename.split('.')[-1].lower() if '.' in filename else 'bin'
    return f"invoices/{instance.id}/{uuid.uuid4().hex}.{ext}"


class Invoice(TimeStampedModel):
    class ProcessingStatus(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        OCR_PROCESSING = 'OCR_PROCESSING', 'OCR In Progress'
        OCR_COMPLETED = 'OCR_COMPLETED', 'OCR Completed'
        VALIDATING = 'VALIDATING', 'Validating'
        READY_FOR_MATCHING = 'READY_FOR_MATCHING', 'Ready for PO Matching'
        EXCEPTION = 'EXCEPTION', 'Exception / Attention Required'
        READY_FOR_APPROVAL = 'READY_FOR_APPROVAL', 'Ready for Approval'
        APPROVED = 'APPROVED', 'Approved'
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class OCRStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Extracted'
        PARTIAL = 'PARTIAL', 'Partially Extracted'
        FAILED = 'FAILED', 'Failed'

    class ValidationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PASSED = 'PASSED', 'Passed'
        WARNING = 'WARNING', 'Warning'
        FAILED = 'FAILED', 'Failed'

    class MatchingStatus(models.TextChoices):
        NOT_APPLICABLE = 'NOT_APPLICABLE', 'Not Applicable'
        PENDING = 'PENDING', 'Pending'
        MATCHED_2WAY = 'MATCHED_2WAY', '2-Way Matched'
        MATCHED_3WAY = 'MATCHED_3WAY', '3-Way Matched'
        MISMATCH_EXCEPTION = 'MISMATCH_EXCEPTION', 'Mismatch Exception'

    class ApprovalStatus(models.TextChoices):
        NOT_SUBMITTED = 'NOT_SUBMITTED', 'Not Submitted'
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        ESCALATED = 'ESCALATED', 'Escalated'

    class PaymentStatus(models.TextChoices):
        NOT_REQUESTED = 'NOT_REQUESTED', 'Not Requested'
        REQUESTED = 'REQUESTED', 'Payment Requested'
        PROCESSING = 'PROCESSING', 'Processing'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=invoice_file_upload_path, blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True, default='')
    file_size = models.PositiveIntegerField(default=0, help_text='File size in bytes')
    content_type = models.CharField(max_length=100, default='application/pdf', blank=True)
    pages_count = models.PositiveIntegerField(default=1)

    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    vendor_name_extracted = models.CharField(max_length=255, blank=True, default='')
    vendor_gstin_extracted = models.CharField(max_length=20, blank=True, default='')

    invoice_number = models.CharField(max_length=100, db_index=True, blank=True, default='')
    fiscal_year = models.CharField(max_length=20, db_index=True, blank=True, default='', help_text='Fiscal year, e.g., FY2026-27')
    invoice_date = models.DateField(null=True, blank=True, db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    currency = models.CharField(max_length=3, default='INR')

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    # PO Relationship
    po_number = models.CharField(max_length=50, blank=True, default='', db_index=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')

    # Lifecycle Statuses
    processing_status = models.CharField(
        max_length=30,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.UPLOADED,
        db_index=True
    )
    ocr_status = models.CharField(
        max_length=20,
        choices=OCRStatus.choices,
        default=OCRStatus.PENDING,
        db_index=True
    )
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
        db_index=True
    )
    matching_status = models.CharField(
        max_length=30,
        choices=MatchingStatus.choices,
        default=MatchingStatus.PENDING,
        db_index=True
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.NOT_SUBMITTED,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_REQUESTED,
        db_index=True
    )

    # OCR Confidence Aggregate (0-100%)
    ocr_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Aggregated OCR extraction confidence percentage'
    )
    raw_ocr_text = models.TextField(blank=True, default='')
    raw_ocr_data = models.JSONField(default=dict, blank=True, help_text='Structured OCR output with per-field confidence')

    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_invoices'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['vendor', 'invoice_number', 'fiscal_year'],
                name='unique_vendor_invoice_fiscal_year',
                condition=models.Q(vendor__isnull=False) & ~models.Q(invoice_number='') & ~models.Q(fiscal_year='')
            )
        ]

    def __str__(self):
        vname = self.vendor.name if self.vendor else (self.vendor_name_extracted or 'Unknown Vendor')
        inv_no = self.invoice_number or 'Unassigned'
        return f"Invoice {inv_no} ({vname}) - ₹{self.total_amount}"


class InvoiceItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    line_number = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=255)
    hsn_sac_code = models.CharField(max_length=20, blank=True, default='')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=20, default='NOS')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    # Matching references
    matched_po_item = models.ForeignKey(POItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='matched_invoice_items')
    matched_grn_item = models.ForeignKey(GRNItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='matched_invoice_items')

    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('95.00'))

    class Meta:
        db_table = 'ap_invoice_items'
        ordering = ['line_number']

    def __str__(self):
        return f"InvItem #{self.line_number}: {self.description} ({self.quantity} @ ₹{self.unit_price})"
