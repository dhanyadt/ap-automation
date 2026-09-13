from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from apps.audit.services import log_audit_event
from apps.goods_receipts.models import GoodsReceipt
from apps.invoices.models import Invoice
from .models import MatchRun


@dataclass(frozen=True)
class MatchingTolerance:
    quantity: Decimal = Decimal('0.01')
    price_percent: Decimal = Decimal('1.00')
    total: Decimal = Decimal('0.01')


DEFAULT_TOLERANCE = MatchingTolerance()


def _price_variance(actual, expected):
    return (actual - expected).quantize(Decimal('0.01'))


def _price_within_tolerance(actual, expected, tolerance):
    if expected == 0:
        return actual == 0
    return abs(actual - expected) <= abs(expected) * tolerance.price_percent / Decimal('100')


def run_matching(invoice: Invoice, actor=None, request=None, tolerance=DEFAULT_TOLERANCE) -> MatchRun:
    po = invoice.purchase_order
    if not po:
        raise ValueError('A purchase order is required for matching.')
    receipts = list(GoodsReceipt.objects.filter(purchase_order=po).prefetch_related('items'))
    accepted_by_po_item = {}
    received_by_po_item = {}
    for receipt in receipts:
        for item in receipt.items.all():
            accepted_by_po_item[item.po_item_id] = accepted_by_po_item.get(item.po_item_id, Decimal('0')) + item.accepted_quantity
            received_by_po_item[item.po_item_id] = received_by_po_item.get(item.po_item_id, Decimal('0')) + item.received_quantity

    discrepancies: list[dict[str, Any]] = []
    for invoice_item in invoice.items.all():
        po_item = po.items.filter(line_number=invoice_item.line_number).first()
        if not po_item:
            discrepancies.append({'line_number': invoice_item.line_number, 'type': 'MISSING_PO_LINE'})
            continue
        invoice_item.matched_po_item = po_item
        quantity_variance = invoice_item.quantity - po_item.quantity
        price_variance = _price_variance(invoice_item.unit_price, po_item.unit_price)
        line_discrepancies = []
        if not receipts and abs(quantity_variance) > tolerance.quantity:
            line_discrepancies.append({'type': 'QUANTITY_VARIANCE', 'variance': str(quantity_variance)})
        if not _price_within_tolerance(invoice_item.unit_price, po_item.unit_price, tolerance):
            line_discrepancies.append({'type': 'PRICE_VARIANCE', 'variance': str(price_variance)})
        if line_discrepancies:
            discrepancies.append({'line_number': invoice_item.line_number, 'details': line_discrepancies})
        if receipts:
            received = received_by_po_item.get(po_item.id, Decimal('0'))
            accepted = accepted_by_po_item.get(po_item.id, Decimal('0'))
            receipt_quantity = accepted_by_po_item.get(po_item.id, received)
            invoice_item.matched_grn_item = po_item.grn_items.order_by('-created_at').first()
            if invoice_item.quantity > receipt_quantity + tolerance.quantity:
                discrepancies.append({
                    'line_number': invoice_item.line_number,
                    'type': 'RECEIPT_QUANTITY_VARIANCE',
                    'ordered_quantity': str(po_item.quantity),
                    'received_quantity': str(received),
                    'accepted_quantity': str(accepted),
                    'invoiced_quantity': str(invoice_item.quantity),
                    'variance': str(invoice_item.quantity - receipt_quantity),
                })
        invoice_item.save(update_fields=['matched_po_item', 'matched_grn_item', 'updated_at'])

    for po_item in po.items.all():
        received = received_by_po_item.get(po_item.id, Decimal('0'))
        if received > po_item.quantity + tolerance.quantity:
            discrepancies.append({
                'line_number': po_item.line_number,
                'type': 'OVER_RECEIPT_VARIANCE',
                'ordered_quantity': str(po_item.quantity),
                'received_quantity': str(received),
                'variance': str(received - po_item.quantity),
            })

    total_variance = _price_variance(invoice.total_amount, po.total_amount)
    if abs(total_variance) > tolerance.total:
        discrepancies.append({'type': 'TOTAL_VARIANCE', 'variance': str(total_variance)})

    has_receipts = bool(receipts)
    match_type = MatchRun.MatchType.THREE_WAY if has_receipts else MatchRun.MatchType.TWO_WAY
    partial_invoice = has_receipts and any(
        invoice_item.quantity < po_item.quantity - tolerance.quantity
        for invoice_item in invoice.items.all()
        for po_item in [po.items.filter(line_number=invoice_item.line_number).first()]
        if po_item
    )
    status = (
        MatchRun.Status.PARTIAL_MATCH if not discrepancies and partial_invoice
        else MatchRun.Status.MATCHED if not discrepancies
        else MatchRun.Status.MISMATCH
    )
    match_run = MatchRun.objects.create(
        invoice=invoice,
        purchase_order=po,
        goods_receipt=receipts[0] if receipts else None,
        match_type=match_type,
        status=status,
        is_successful=not discrepancies,
        summary='Match completed successfully.' if not discrepancies else 'Match completed with discrepancies.',
        discrepancies=discrepancies,
    )
    invoice.matching_status = (
        Invoice.MatchingStatus.MATCHED_3WAY if match_type == MatchRun.MatchType.THREE_WAY and not discrepancies
        else Invoice.MatchingStatus.MATCHED_2WAY if match_type == MatchRun.MatchType.TWO_WAY and not discrepancies
        else Invoice.MatchingStatus.MISMATCH_EXCEPTION
    )
    invoice.processing_status = Invoice.ProcessingStatus.READY_FOR_APPROVAL if not discrepancies else Invoice.ProcessingStatus.EXCEPTION
    invoice.save(update_fields=['matching_status', 'processing_status', 'updated_at'])
    log_audit_event(
        action='MATCHING_COMPLETED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=actor,
        request=request,
        changes={'match_run_id': str(match_run.id), 'match_type': match_type, 'status': status},
    )
    return match_run
