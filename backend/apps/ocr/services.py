from datetime import date
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.services import log_audit_event
from common.utils import get_indian_fiscal_year
from apps.invoices.models import Invoice, InvoiceItem
from .models import OCRJob
from .providers import BaseOCRProvider, MockOCRProvider


def run_ocr(invoice: Invoice, provider: BaseOCRProvider | None = None, actor=None, request=None) -> OCRJob:
    provider = provider or MockOCRProvider()
    job = OCRJob.objects.create(invoice=invoice, provider_name=provider.__class__.__name__, status=OCRJob.Status.RUNNING)
    try:
        extraction = provider.extract(invoice)
    except (OSError, TypeError, ValueError) as exc:
        job.status = OCRJob.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        raise
    fields = extraction.fields
    job.extracted_fields = {
        **fields,
        'subtotal': str(fields['subtotal']),
        'tax_amount': str(fields['tax_amount']),
        'total_amount': str(fields['total_amount']),
        'items': [{key: str(value) if hasattr(value, 'as_tuple') else value for key, value in item.items()}
                  for item in extraction.items],
    }
    job.raw_text = extraction.raw_text
    job.average_confidence = extraction.average_confidence
    job.status = OCRJob.Status.COMPLETED
    job.save(update_fields=['extracted_fields', 'raw_text', 'average_confidence', 'status', 'updated_at'])

    invoice.vendor = invoice.vendor or invoice.purchase_order.vendor if invoice.purchase_order else invoice.vendor
    invoice.vendor_name_extracted = fields['vendor_name']
    invoice.vendor_gstin_extracted = fields['vendor_gstin']
    invoice.invoice_number = fields['invoice_number']
    invoice.invoice_date = date.fromisoformat(fields['invoice_date'])
    invoice.po_number = fields['po_number'] or invoice.po_number
    invoice.fiscal_year = invoice.fiscal_year or get_indian_fiscal_year(invoice.invoice_date)
    invoice.subtotal = fields['subtotal']
    invoice.tax_amount = fields['tax_amount']
    invoice.total_amount = fields['total_amount']
    invoice.ocr_confidence = extraction.average_confidence
    invoice.raw_ocr_text = extraction.raw_text
    invoice.raw_ocr_data = job.extracted_fields
    invoice.ocr_status = Invoice.OCRStatus.SUCCESS
    invoice.processing_status = Invoice.ProcessingStatus.OCR_COMPLETED
    try:
        with transaction.atomic():
            invoice.save(update_fields=[
                'vendor', 'vendor_name_extracted', 'vendor_gstin_extracted', 'invoice_number',
                'invoice_date', 'fiscal_year', 'po_number', 'subtotal', 'tax_amount', 'total_amount',
                'ocr_confidence', 'raw_ocr_text', 'raw_ocr_data', 'ocr_status',
                'processing_status', 'updated_at',
            ])
    except IntegrityError:
        # Preserve the extracted result so validation can report the duplicate cleanly.
        invoice.refresh_from_db()
        invoice.ocr_status = Invoice.OCRStatus.SUCCESS
        invoice.processing_status = Invoice.ProcessingStatus.OCR_COMPLETED
        Invoice.objects.filter(pk=invoice.pk).update(
            ocr_status=Invoice.OCRStatus.SUCCESS,
            processing_status=Invoice.ProcessingStatus.OCR_COMPLETED,
            ocr_confidence=extraction.average_confidence,
            raw_ocr_text=extraction.raw_text,
            raw_ocr_data=job.extracted_fields,
            updated_at=timezone.now(),
        )

    invoice.items.all().delete()
    InvoiceItem.objects.bulk_create([
        InvoiceItem(invoice=invoice, **item) for item in extraction.items
    ])
    log_audit_event(
        action='OCR_COMPLETED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=actor,
        request=request,
        changes={'ocr_job_id': str(job.id), 'confidence': str(extraction.average_confidence)},
    )
    return job
