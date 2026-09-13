import hashlib
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_audit_event
from apps.invoices.models import Invoice
from .models import Payment


class PaymentError(Exception):
    """Raised when a payment operation violates the payment workflow."""


@dataclass(frozen=True)
class GatewayResult:
    success: bool
    reference_number: str
    payload: dict
    error_message: str = ''


class BasePaymentGateway:
    def submit(self, payment: Payment) -> GatewayResult:
        raise NotImplementedError


class MockPaymentGateway(BasePaymentGateway):
    """Deterministic local payment rail used by the MVP."""

    def submit(self, payment: Payment) -> GatewayResult:
        seed = f'{payment.invoice_id}:{payment.amount}:{payment.payment_method}'
        reference = f'MOCKUTR{hashlib.sha256(seed.encode()).hexdigest()[:16].upper()}'
        return GatewayResult(
            success=True,
            reference_number=reference,
            payload={
                'provider': 'MockPaymentGateway',
                'payment_id': str(payment.id),
                'submitted_at': timezone.now().isoformat(),
                'reference_number': reference,
                'status': 'SETTLED',
            },
        )


def _audit_status_change(payment, old_status, actor=None, request=None):
    log_audit_event(
        action='PAYMENT_STATUS_CHANGED',
        entity_type='PAYMENT',
        entity_id=payment.id,
        actor=actor,
        request=request,
        changes={'from': old_status, 'to': payment.status},
    )


@transaction.atomic
def create_payment_request(invoice: Invoice, initiated_by=None, payment_method=None, request=None) -> Payment:
    invoice = Invoice.objects.select_for_update().select_related('vendor').get(pk=invoice.pk)
    if invoice.approval_status != Invoice.ApprovalStatus.APPROVED:
        raise PaymentError('Only approved invoices can be submitted for payment.')
    if not invoice.vendor:
        raise PaymentError('An approved invoice must have a vendor before payment.')

    existing = invoice.payments.filter(
        status__in=[
            Payment.Status.REQUESTED,
            Payment.Status.PROCESSING,
            Payment.Status.PAID,
        ],
    ).first()
    if existing:
        raise PaymentError('A payment already exists for this invoice.')

    payment = Payment.objects.create(
        invoice=invoice,
        vendor=invoice.vendor,
        amount=invoice.total_amount,
        currency=invoice.currency,
        payment_method=payment_method or Payment.Method.NEFT,
        status=Payment.Status.REQUESTED,
        initiated_by=initiated_by,
        advice_notes=f'Payment advice for invoice {invoice.invoice_number}.',
    )
    old_status = invoice.payment_status
    invoice.payment_status = Invoice.PaymentStatus.REQUESTED
    invoice.save(update_fields=['payment_status', 'processing_status', 'updated_at'])
    log_audit_event(
        action='PAYMENT_REQUESTED',
        entity_type='PAYMENT',
        entity_id=payment.id,
        actor=initiated_by,
        request=request,
        changes={
            'invoice_id': str(invoice.id),
            'amount': str(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.payment_method,
        },
    )
    _audit_status_change(payment, None, initiated_by, request)
    log_audit_event(
        action='INVOICE_WORKFLOW_STATUS_CHANGED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=initiated_by,
        request=request,
        changes={
            'payment_status': invoice.payment_status,
            'processing_status': invoice.processing_status,
            'previous_payment_status': old_status,
        },
    )
    return payment


@transaction.atomic
def process_payment(payment_id, actor, gateway=None, request=None) -> Payment:
    payment = Payment.objects.select_for_update().select_related('invoice', 'vendor').get(pk=payment_id)
    if payment.status != Payment.Status.REQUESTED:
        raise PaymentError('Only requested payments can be processed.')

    gateway = gateway or MockPaymentGateway()
    old_status = payment.status
    payment.status = Payment.Status.PROCESSING
    payment.save(update_fields=['status', 'updated_at'])
    _audit_status_change(payment, old_status, actor, request)
    log_audit_event(
        action='PAYMENT_PROCESSING',
        entity_type='PAYMENT',
        entity_id=payment.id,
        actor=actor,
        request=request,
    )

    result = gateway.submit(payment)
    invoice = payment.invoice
    if result.success:
        payment.status = Payment.Status.PAID
        payment.reference_number = result.reference_number
        payment.bank_response_payload = result.payload
        payment.paid_at = timezone.now()
        payment.save(update_fields=[
            'status', 'reference_number', 'bank_response_payload', 'paid_at', 'updated_at',
        ])
        _audit_status_change(payment, Payment.Status.PROCESSING, actor, request)
        invoice.payment_status = Invoice.PaymentStatus.PAID
        invoice.processing_status = Invoice.ProcessingStatus.PAID
        invoice.save(update_fields=['payment_status', 'processing_status', 'updated_at'])
        log_audit_event(
            action='PAYMENT_SUCCEEDED',
            entity_type='PAYMENT',
            entity_id=payment.id,
            actor=actor,
            request=request,
            changes={'reference_number': payment.reference_number, 'amount': str(payment.amount)},
        )
    else:
        payment.status = Payment.Status.FAILED
        payment.bank_response_payload = result.payload
        payment.advice_notes = result.error_message
        payment.save(update_fields=['status', 'bank_response_payload', 'advice_notes', 'updated_at'])
        _audit_status_change(payment, Payment.Status.PROCESSING, actor, request)
        invoice.payment_status = Invoice.PaymentStatus.FAILED
        invoice.processing_status = Invoice.ProcessingStatus.EXCEPTION
        invoice.save(update_fields=['payment_status', 'processing_status', 'updated_at'])
        log_audit_event(
            action='PAYMENT_FAILED',
            entity_type='PAYMENT',
            entity_id=payment.id,
            actor=actor,
            request=request,
            changes={'error': result.error_message},
        )
    return payment


def payment_advice(payment: Payment) -> dict:
    return {
        'payment_id': str(payment.id),
        'invoice_number': payment.invoice.invoice_number,
        'invoice_date': payment.invoice.invoice_date.isoformat() if payment.invoice.invoice_date else None,
        'vendor_name': payment.vendor.name,
        'vendor_code': payment.vendor.code,
        'amount': str(payment.amount),
        'currency': payment.currency,
        'payment_method': payment.payment_method,
        'status': payment.status,
        'utr': payment.reference_number or None,
        'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
        'advice_notes': payment.advice_notes,
    }
