from decimal import Decimal

from apps.audit.services import log_audit_event
from apps.invoices.models import Invoice
from .models import ValidationResult

MONEY_TOLERANCE = Decimal('0.01')


def validate_invoice(invoice: Invoice, actor=None, request=None) -> list[ValidationResult]:
    invoice.validation_results.all().delete()
    results = []

    def add(code, name, severity, message, details=None):
        results.append(ValidationResult.objects.create(
            invoice=invoice, rule_code=code, rule_name=name, severity=severity,
            message=message, details=details or {},
        ))

    required = {
        'INVOICE_NUMBER': bool(invoice.invoice_number),
        'INVOICE_DATE': invoice.invoice_date is not None,
        'VENDOR': invoice.vendor is not None,
    }
    for code, present in required.items():
        add(code, code.replace('_', ' ').title(),
            ValidationResult.Severity.PASSED if present else ValidationResult.Severity.FAILED,
            f"{code.replace('_', ' ').title()} is present." if present else f"{code.replace('_', ' ').title()} is required.")

    gstin_available = bool(invoice.vendor and invoice.vendor.gstin and invoice.vendor_gstin_extracted)
    gstin_ok = bool(gstin_available and
                    invoice.vendor.gstin.upper() == invoice.vendor_gstin_extracted.upper())
    gstin_severity = (
        ValidationResult.Severity.PASSED if gstin_ok
        else ValidationResult.Severity.FAILED if gstin_available
        else ValidationResult.Severity.WARNING
    )
    add('GSTIN_CONSISTENCY', 'Vendor GSTIN consistency', gstin_severity,
        'Extracted GSTIN matches the vendor master.' if gstin_ok
        else 'Extracted GSTIN does not match the vendor master.' if gstin_available
        else 'GSTIN could not be compared because vendor or extracted GSTIN is unavailable.',
        {'vendor_gstin': invoice.vendor.gstin if invoice.vendor else '', 'extracted_gstin': invoice.vendor_gstin_extracted})

    duplicate = bool(invoice.vendor and invoice.invoice_number and invoice.fiscal_year and
                     invoice.vendor.invoices.filter(
                         invoice_number__iexact=invoice.invoice_number,
                         fiscal_year=invoice.fiscal_year,
                     ).exclude(id=invoice.id).exists())
    add('DUPLICATE_INVOICE', 'Duplicate invoice', ValidationResult.Severity.FAILED if duplicate else ValidationResult.Severity.PASSED,
        'Duplicate invoice exists for this vendor and fiscal year.' if duplicate else 'No duplicate invoice found.')

    arithmetic_ok = abs(invoice.subtotal + invoice.tax_amount - invoice.total_amount) <= MONEY_TOLERANCE
    add('INVOICE_TOTAL', 'Invoice subtotal and tax arithmetic',
        ValidationResult.Severity.PASSED if arithmetic_ok else ValidationResult.Severity.FAILED,
        'Subtotal plus tax equals total.' if arithmetic_ok else 'Subtotal plus tax does not equal total.',
        {'expected_total': str(invoice.subtotal + invoice.tax_amount), 'actual_total': str(invoice.total_amount)})

    line_failures = []
    for item in invoice.items.all():
        expected_tax = (item.quantity * item.unit_price * item.tax_rate / Decimal('100')).quantize(MONEY_TOLERANCE)
        expected_total = (item.quantity * item.unit_price + expected_tax).quantize(MONEY_TOLERANCE)
        if abs(item.tax_amount - expected_tax) > MONEY_TOLERANCE or abs(item.line_total - expected_total) > MONEY_TOLERANCE:
            line_failures.append(item.line_number)
    add('LINE_ARITHMETIC', 'Line-item arithmetic',
        ValidationResult.Severity.FAILED if line_failures else ValidationResult.Severity.PASSED,
        f"Line-item arithmetic failed for lines: {line_failures}." if line_failures else 'All line items reconcile.',
        {'failed_lines': line_failures})

    po_valid = not invoice.po_number or bool(invoice.purchase_order and
                                              invoice.purchase_order.po_number.lower() == invoice.po_number.lower())
    add('PO_REFERENCE', 'Purchase order reference',
        ValidationResult.Severity.PASSED if po_valid and invoice.po_number else ValidationResult.Severity.WARNING if po_valid else ValidationResult.Severity.FAILED,
        'Purchase order reference is valid.' if po_valid and invoice.po_number else 'No purchase order reference supplied.' if po_valid else 'Purchase order reference is invalid.')

    failed = any(result.severity == ValidationResult.Severity.FAILED for result in results)
    invoice.validation_status = Invoice.ValidationStatus.FAILED if failed else Invoice.ValidationStatus.PASSED
    invoice.processing_status = Invoice.ProcessingStatus.EXCEPTION if failed else Invoice.ProcessingStatus.READY_FOR_MATCHING
    invoice.save(update_fields=['validation_status', 'processing_status', 'updated_at'])
    log_audit_event(
        action='VALIDATION_COMPLETED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=actor,
        request=request,
        changes={'failed_rules': [result.rule_code for result in results if result.severity == ValidationResult.Severity.FAILED]},
    )
    return results
