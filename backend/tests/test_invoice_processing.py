from decimal import Decimal

import pytest
from apps.audit.models import AuditLog
from apps.goods_receipts.models import GoodsReceipt, GRNItem
from apps.invoices.models import Invoice, InvoiceItem
from apps.invoices.services import process_invoice
from apps.matching.models import MatchRun
from apps.matching.services import run_matching
from apps.ocr.services import run_ocr
from apps.validations.services import validate_invoice


def make_invoice(sample_vendor, sample_po, number='INV-TEST-001', quantity=Decimal('2.00'),
                 unit_price=Decimal('5000.00'), total=Decimal('11800.00')):
    invoice = Invoice.objects.create(
        vendor=sample_vendor,
        purchase_order=sample_po,
        po_number=sample_po.po_number,
        invoice_number=number,
        fiscal_year='FY2026-27',
        invoice_date='2026-04-15',
        subtotal=Decimal('10000.00'),
        tax_amount=Decimal('1800.00'),
        total_amount=total,
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        line_number=1,
        description='Dell Latitude Enterprise Laptop',
        quantity=quantity,
        unit_price=unit_price,
        tax_rate=Decimal('18.00'),
        tax_amount=(quantity * unit_price * Decimal('0.18')).quantize(Decimal('0.01')),
        line_total=total,
    )
    return invoice


@pytest.mark.django_db
def test_successful_ocr_extraction(sample_vendor, sample_po):
    invoice = make_invoice(sample_vendor, sample_po)
    job = run_ocr(invoice)
    invoice.refresh_from_db()

    assert job.status == 'COMPLETED'
    assert job.extracted_fields['invoice_number'] == 'INV-TEST-001'
    assert invoice.ocr_status == Invoice.OCRStatus.SUCCESS
    assert invoice.items.count() == 1
    assert invoice.items.first().line_total == Decimal('11800.00')


@pytest.mark.django_db
def test_missing_mandatory_field(sample_vendor):
    invoice = Invoice.objects.create(
        vendor=sample_vendor,
        fiscal_year='FY2026-27',
        vendor_gstin_extracted=sample_vendor.gstin,
    )
    results = validate_invoice(invoice)
    result = next(item for item in results if item.rule_code == 'INVOICE_NUMBER')

    assert result.severity == 'FAILED'
    assert invoice.validation_status == Invoice.ValidationStatus.FAILED


@pytest.mark.django_db
def test_duplicate_invoice_detection(clerk_client, sample_vendor):
    payload = {
        'vendor': str(sample_vendor.id),
        'invoice_number': 'DUP-001',
        'fiscal_year': 'FY2026-27',
        'invoice_date': '2026-04-15',
    }
    assert clerk_client.post('/api/v1/invoices/', payload, format='json').status_code == 201
    duplicate = clerk_client.post('/api/v1/invoices/', payload, format='json')

    assert duplicate.status_code == 400
    assert 'invoice_number' in duplicate.data['error']['details']


@pytest.mark.django_db
def test_invoice_arithmetic_failure(sample_vendor):
    invoice = Invoice.objects.create(
        vendor=sample_vendor, invoice_number='BAD-TOTAL', fiscal_year='FY2026-27',
        invoice_date='2026-04-15', vendor_gstin_extracted=sample_vendor.gstin,
        subtotal=Decimal('100.00'), tax_amount=Decimal('18.00'), total_amount=Decimal('125.00'),
    )
    results = validate_invoice(invoice)

    assert next(item for item in results if item.rule_code == 'INVOICE_TOTAL').severity == 'FAILED'


@pytest.mark.django_db
def test_successful_two_way_match(sample_vendor, sample_po):
    invoice = make_invoice(sample_vendor, sample_po)
    result = run_matching(invoice)

    assert result.match_type == MatchRun.MatchType.TWO_WAY
    assert result.is_successful is True
    assert result.discrepancies == []


@pytest.mark.django_db
def test_two_way_price_variance(sample_vendor, sample_po):
    invoice = make_invoice(sample_vendor, sample_po, number='PRICE-VAR', unit_price=Decimal('5500.00'),
                           total=Decimal('12980.00'))
    result = run_matching(invoice)

    assert result.is_successful is False
    assert any(item.get('type') == 'PRICE_VARIANCE' for discrepancy in result.discrepancies
               for item in discrepancy.get('details', []))


@pytest.mark.django_db
def test_successful_three_way_match(sample_vendor, sample_po):
    grn = GoodsReceipt.objects.create(
        grn_number='GRN-001', purchase_order=sample_po, received_date='2026-04-20',
    )
    GRNItem.objects.create(
        goods_receipt=grn, po_item=sample_po.items.first(), received_quantity=Decimal('2.00'),
        accepted_quantity=Decimal('2.00'), rejected_quantity=Decimal('0.00'),
    )
    invoice = make_invoice(sample_vendor, sample_po, number='THREE-WAY')
    result = run_matching(invoice)

    assert result.match_type == MatchRun.MatchType.THREE_WAY
    assert result.is_successful is True


@pytest.mark.django_db
def test_partial_grn_quantity_discrepancy(sample_vendor, sample_po):
    grn = GoodsReceipt.objects.create(
        grn_number='GRN-PARTIAL', purchase_order=sample_po, received_date='2026-04-20',
    )
    GRNItem.objects.create(
        goods_receipt=grn, po_item=sample_po.items.first(), received_quantity=Decimal('1.00'),
        accepted_quantity=Decimal('1.00'), rejected_quantity=Decimal('0.00'),
    )
    invoice = make_invoice(sample_vendor, sample_po, number='PARTIAL-GRN')
    result = run_matching(invoice)

    assert result.is_successful is False
    assert any(item.get('type') == 'RECEIPT_QUANTITY_VARIANCE' for item in result.discrepancies)


@pytest.mark.django_db
def test_invoice_cannot_directly_set_approved_or_paid(clerk_client, sample_vendor):
    response = clerk_client.post('/api/v1/invoices/', {
        'vendor': str(sample_vendor.id),
        'invoice_number': 'CLIENT-STATUS',
        'fiscal_year': 'FY2026-27',
        'processing_status': 'APPROVED',
        'approval_status': 'APPROVED',
        'payment_status': 'PAID',
    }, format='json')

    assert response.status_code == 201
    assert response.data['processing_status'] == Invoice.ProcessingStatus.UPLOADED
    assert response.data['approval_status'] == Invoice.ApprovalStatus.NOT_SUBMITTED
    assert response.data['payment_status'] == Invoice.PaymentStatus.NOT_REQUESTED


@pytest.mark.django_db
def test_processing_creates_audit_records(sample_vendor, sample_po):
    invoice = make_invoice(sample_vendor, sample_po, number='AUDIT-PROCESS')
    process_invoice(invoice)

    actions = set(AuditLog.objects.filter(entity_id=str(invoice.id)).values_list('action', flat=True))
    assert {'OCR_COMPLETED', 'VALIDATION_COMPLETED', 'MATCHING_COMPLETED'} <= actions
