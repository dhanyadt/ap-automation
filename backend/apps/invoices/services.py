from django.db import transaction

from apps.audit.services import log_audit_event
from apps.matching.services import run_matching
from apps.ocr.services import run_ocr
from apps.validations.services import validate_invoice
from .models import Invoice


@transaction.atomic
def process_invoice(invoice: Invoice, actor=None, request=None) -> dict:
    log_audit_event(
        action='INVOICE_PROCESSING_STARTED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=actor,
        request=request,
    )
    run_ocr(invoice, actor=actor, request=request)
    invoice.refresh_from_db()
    validation_results = validate_invoice(invoice, actor=actor, request=request)
    match_run = None
    if invoice.validation_status == Invoice.ValidationStatus.PASSED and invoice.purchase_order:
        match_run = run_matching(invoice, actor=actor, request=request)
    return {
        'invoice': invoice,
        'validation_results': validation_results,
        'match_run': match_run,
    }
