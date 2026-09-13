import pytest

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.approvals.models import ApprovalMatrixRule
from apps.approvals.services import take_action
from apps.invoices.models import Invoice
from apps.invoices.services import process_invoice
from apps.payments.models import Payment
from apps.payments.services import (
    PaymentError,
    create_payment_request,
    process_payment,
)
from tests.test_invoice_processing import make_invoice


@pytest.fixture
def payment_rule(db):
    return ApprovalMatrixRule.objects.create(
        name='Payment Test Approval',
        min_amount='0.00',
        max_amount='500000.00',
        required_role='APPROVER',
        step_order=1,
    )


@pytest.fixture
def finance_user(db):
    return User.objects.create_user(
        email='finance-payment-test@example.com',
        password='TestPassword123!',
        role=User.Role.FINANCE,
    )


def approve_invoice(invoice, ap_clerk_user, approver_user):
    process_invoice(invoice, actor=ap_clerk_user)
    request = invoice.approval_requests.get()
    take_action(request.id, approver_user, 'APPROVE')
    invoice.refresh_from_db()
    return invoice


@pytest.mark.django_db
def test_approved_invoice_creates_payment_request_and_audits(
    sample_vendor, sample_po, ap_clerk_user, approver_user, payment_rule
):
    invoice = approve_invoice(
        make_invoice(sample_vendor, sample_po, number='PAYMENT-001'),
        ap_clerk_user,
        approver_user,
    )

    payment = invoice.payments.get()
    assert payment.status == Payment.Status.REQUESTED
    assert invoice.payment_status == Invoice.PaymentStatus.REQUESTED
    assert invoice.processing_status == Invoice.ProcessingStatus.APPROVED
    actions = set(
        AuditLog.objects.filter(entity_id=str(payment.id)).values_list('action', flat=True)
    )
    assert {'PAYMENT_REQUESTED', 'PAYMENT_STATUS_CHANGED'} <= actions


@pytest.mark.django_db
def test_payment_processing_requires_finance_role(api_client, sample_vendor, sample_po, ap_clerk_user, approver_user, payment_rule):
    invoice = approve_invoice(
        make_invoice(sample_vendor, sample_po, number='PAYMENT-002'),
        ap_clerk_user,
        approver_user,
    )
    api_client.force_authenticate(user=approver_user)
    response = api_client.post(f'/api/v1/payments/{invoice.payments.get().id}/process/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_payment_happy_path_generates_deterministic_utr(
    sample_vendor, sample_po, ap_clerk_user, approver_user, finance_user, payment_rule
):
    invoice = approve_invoice(
        make_invoice(sample_vendor, sample_po, number='PAYMENT-003'),
        ap_clerk_user,
        approver_user,
    )
    payment = process_payment(invoice.payments.get().id, finance_user)
    assert payment.status == Payment.Status.PAID
    assert payment.reference_number.startswith('MOCKUTR')
    assert len(payment.reference_number) == 23
    assert invoice.payments.get().reference_number == payment.reference_number
    invoice.refresh_from_db()
    assert invoice.payment_status == Invoice.PaymentStatus.PAID
    assert invoice.processing_status == Invoice.ProcessingStatus.PAID


@pytest.mark.django_db
def test_duplicate_and_invalid_payment_requests_are_rejected(
    sample_vendor, sample_po, ap_clerk_user, approver_user, payment_rule
):
    invoice = make_invoice(sample_vendor, sample_po, number='PAYMENT-004')
    with pytest.raises(PaymentError, match='Only approved'):
        create_payment_request(invoice)

    invoice = approve_invoice(invoice, ap_clerk_user, approver_user)
    with pytest.raises(PaymentError, match='already exists'):
        create_payment_request(invoice)


@pytest.mark.django_db
def test_paid_payment_cannot_be_processed_twice(
    sample_vendor, sample_po, ap_clerk_user, approver_user, finance_user, payment_rule
):
    invoice = approve_invoice(
        make_invoice(sample_vendor, sample_po, number='PAYMENT-005'),
        ap_clerk_user,
        approver_user,
    )
    payment = process_payment(invoice.payments.get().id, finance_user)
    with pytest.raises(PaymentError, match='Only requested'):
        process_payment(payment.id, finance_user)
