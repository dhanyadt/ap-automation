import pytest

from apps.approvals.models import ApprovalMatrixRule, ApprovalRequest
from apps.approvals.services import ApprovalError, create_approval_request, take_action
from apps.audit.models import AuditLog
from apps.invoices.models import Invoice
from apps.invoices.services import process_invoice
from tests.test_invoice_processing import make_invoice


@pytest.fixture
def approval_rule(db):
    return ApprovalMatrixRule.objects.create(
        name='Standard AP Approval',
        min_amount='0.00',
        max_amount='500000.00',
        required_role='APPROVER',
        step_order=1,
    )


@pytest.mark.django_db
def test_approval_request_creation_and_routing(sample_vendor, sample_po, ap_clerk_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-001')
    process_invoice(invoice, actor=ap_clerk_user)

    approval_request = invoice.approval_requests.get()
    assert approval_request.status == ApprovalRequest.Status.PENDING
    assert approval_request.submitted_by_id == ap_clerk_user.id
    assert approval_request.total_steps == 1
    assert approval_rule.required_role == 'APPROVER'
    assert invoice.approval_status == Invoice.ApprovalStatus.PENDING


@pytest.mark.django_db
def test_duplicate_active_approval_request_is_prevented(sample_vendor, sample_po, ap_clerk_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-002')
    process_invoice(invoice, actor=ap_clerk_user)

    first = create_approval_request(invoice, submitted_by=ap_clerk_user)
    second = create_approval_request(invoice, submitted_by=ap_clerk_user)
    assert first.id == second.id
    assert invoice.approval_requests.count() == 1


@pytest.mark.django_db
def test_successful_approval_transitions_invoice(sample_vendor, sample_po, ap_clerk_user, approver_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-003')
    process_invoice(invoice, actor=ap_clerk_user)
    approval_request = invoice.approval_requests.get()

    result = take_action(approval_request.id, approver_user, 'APPROVE', comments='Reviewed and approved')
    invoice.refresh_from_db()

    assert result.status == ApprovalRequest.Status.APPROVED
    assert invoice.approval_status == Invoice.ApprovalStatus.APPROVED
    assert invoice.processing_status == Invoice.ProcessingStatus.APPROVED
    assert result.actions.get().comments == 'Reviewed and approved'


@pytest.mark.django_db
def test_rejection_transitions_invoice_and_audits(sample_vendor, sample_po, ap_clerk_user, approver_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-004')
    process_invoice(invoice, actor=ap_clerk_user)
    approval_request = invoice.approval_requests.get()

    take_action(approval_request.id, approver_user, 'REJECT', comments='Missing business justification')
    approval_request.refresh_from_db()
    invoice.refresh_from_db()

    assert approval_request.status == ApprovalRequest.Status.REJECTED
    assert invoice.approval_status == Invoice.ApprovalStatus.REJECTED
    assert invoice.processing_status == Invoice.ProcessingStatus.EXCEPTION
    actions = set(AuditLog.objects.filter(entity_id=str(approval_request.id)).values_list('action', flat=True))
    assert 'INVOICE_REJECTED' in actions
    assert 'INVOICE_WORKFLOW_STATUS_CHANGED' in set(
        AuditLog.objects.filter(entity_id=str(invoice.id)).values_list('action', flat=True)
    )


@pytest.mark.django_db
def test_unauthorized_role_cannot_approve(sample_vendor, sample_po, ap_clerk_user, approver_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-005')
    process_invoice(invoice, actor=ap_clerk_user)
    approval_request = invoice.approval_requests.get()

    with pytest.raises(ApprovalError, match='submitter cannot approve'):
        take_action(approval_request.id, ap_clerk_user, 'APPROVE')

    with pytest.raises(ApprovalError, match='Only the'):
        from apps.accounts.models import User
        finance_user = User.objects.create_user(
            email='finance-approval-test@example.com',
            password='TestPassword123!',
            role=User.Role.FINANCE,
        )
        take_action(approval_request.id, finance_user, 'APPROVE')


@pytest.mark.django_db
def test_resolved_request_cannot_be_acted_on_again(sample_vendor, sample_po, ap_clerk_user, approver_user, approval_rule):
    invoice = make_invoice(sample_vendor, sample_po, number='APPROVAL-006')
    process_invoice(invoice, actor=ap_clerk_user)
    approval_request = invoice.approval_requests.get()
    take_action(approval_request.id, approver_user, 'APPROVE')

    with pytest.raises(ApprovalError, match='already been resolved'):
        take_action(approval_request.id, approver_user, 'REJECT')
