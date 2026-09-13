from django.db import transaction
from django.db.models import Q

from apps.audit.services import log_audit_event
from apps.invoices.models import Invoice
from .models import ApprovalAction, ApprovalMatrixRule, ApprovalRequest


class ApprovalError(Exception):
    """Raised when an approval workflow operation is not valid."""


def _matching_rules(invoice: Invoice):
    return ApprovalMatrixRule.objects.filter(
        min_amount__lte=invoice.total_amount,
    ).filter(
        Q(max_amount__isnull=True) | Q(max_amount__gte=invoice.total_amount),
    ).order_by('step_order', 'id')


def current_rule(approval_request: ApprovalRequest) -> ApprovalMatrixRule | None:
    invoice = approval_request.invoice
    return _matching_rules(invoice).filter(step_order=approval_request.current_step).first()


@transaction.atomic
def create_approval_request(invoice: Invoice, submitted_by=None, request=None) -> ApprovalRequest | None:
    caller_invoice = invoice
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.validation_status != Invoice.ValidationStatus.PASSED:
        raise ApprovalError('Invoice must pass validation before approval routing.')
    if invoice.matching_status not in (
        Invoice.MatchingStatus.MATCHED_2WAY,
        Invoice.MatchingStatus.MATCHED_3WAY,
    ):
        raise ApprovalError('Invoice must pass matching before approval routing.')

    active = invoice.approval_requests.filter(
        status__in=[ApprovalRequest.Status.PENDING, ApprovalRequest.Status.ESCALATED],
    ).first()
    if active:
        return active

    rules = list(_matching_rules(invoice))
    if not rules:
        return None

    approval_request = ApprovalRequest.objects.create(
        invoice=invoice,
        status=ApprovalRequest.Status.PENDING,
        current_step=rules[0].step_order,
        total_steps=len({rule.step_order for rule in rules}),
        submitted_by=submitted_by,
    )
    invoice.approval_status = Invoice.ApprovalStatus.PENDING
    invoice.processing_status = Invoice.ProcessingStatus.READY_FOR_APPROVAL
    invoice.save(update_fields=['approval_status', 'processing_status', 'updated_at'])
    caller_invoice.approval_status = invoice.approval_status
    caller_invoice.processing_status = invoice.processing_status
    log_audit_event(
        action='APPROVAL_REQUEST_CREATED',
        entity_type='APPROVAL_REQUEST',
        entity_id=approval_request.id,
        actor=submitted_by,
        request=request,
        changes={
            'invoice_id': str(invoice.id),
            'amount': str(invoice.total_amount),
            'required_role': rules[0].required_role,
            'step_order': rules[0].step_order,
        },
    )
    log_audit_event(
        action='INVOICE_WORKFLOW_STATUS_CHANGED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=submitted_by,
        request=request,
        changes={'approval_status': invoice.approval_status, 'processing_status': invoice.processing_status},
    )
    return approval_request


def _authorize_actor(approval_request: ApprovalRequest, actor):
    rule = current_rule(approval_request)
    if not rule:
        raise ApprovalError('No approval matrix rule is configured for this invoice step.')
    if approval_request.submitted_by_id == actor.id:
        raise ApprovalError('The invoice submitter cannot approve their own invoice.')
    if actor.is_superuser or actor.role == 'ADMIN':
        return rule
    if actor.role != rule.required_role:
        raise ApprovalError(f'Only the {rule.get_required_role_display()} role may act on this request.')
    return rule


@transaction.atomic
def take_action(approval_request_id, actor, action, comments='', request=None) -> ApprovalRequest:
    approval_request = ApprovalRequest.objects.select_for_update().select_related('invoice').get(
        id=approval_request_id,
    )
    if approval_request.status != ApprovalRequest.Status.PENDING:
        raise ApprovalError('This approval request has already been resolved or escalated.')
    rule = _authorize_actor(approval_request, actor)
    action = action.upper()
    if action not in ApprovalAction.Action.values:
        raise ApprovalError('Unsupported approval action.')

    ApprovalAction.objects.create(
        approval_request=approval_request,
        step_order=approval_request.current_step,
        actor=actor,
        role_acted_as=actor.role,
        action=action,
        comments=comments,
    )
    invoice = approval_request.invoice
    if action == ApprovalAction.Action.APPROVE:
        next_step = (
            _matching_rules(invoice)
            .filter(step_order__gt=approval_request.current_step)
            .values_list('step_order', flat=True)
            .first()
        )
        if next_step is not None:
            approval_request.current_step = next_step
        else:
            approval_request.status = ApprovalRequest.Status.APPROVED
            invoice.approval_status = Invoice.ApprovalStatus.APPROVED
            invoice.processing_status = Invoice.ProcessingStatus.APPROVED
    elif action == ApprovalAction.Action.REJECT:
        approval_request.status = ApprovalRequest.Status.REJECTED
        invoice.approval_status = Invoice.ApprovalStatus.REJECTED
        invoice.processing_status = Invoice.ProcessingStatus.EXCEPTION
    else:
        approval_request.status = ApprovalRequest.Status.ESCALATED
        invoice.approval_status = Invoice.ApprovalStatus.ESCALATED
        invoice.processing_status = Invoice.ProcessingStatus.EXCEPTION

    approval_request.save(update_fields=['status', 'current_step', 'updated_at'])
    invoice.save(update_fields=['approval_status', 'processing_status', 'updated_at'])
    if action == ApprovalAction.Action.APPROVE and approval_request.status == ApprovalRequest.Status.APPROVED:
        from apps.payments.services import create_payment_request
        create_payment_request(invoice, initiated_by=actor, request=request)
    audit_action = {
        ApprovalAction.Action.APPROVE: 'INVOICE_APPROVED',
        ApprovalAction.Action.REJECT: 'INVOICE_REJECTED',
        ApprovalAction.Action.ESCALATE: 'INVOICE_ESCALATED',
    }[action]
    log_audit_event(
        action=audit_action,
        entity_type='APPROVAL_REQUEST',
        entity_id=approval_request.id,
        actor=actor,
        request=request,
        changes={'action': action, 'comments': comments, 'step_order': rule.step_order},
    )
    log_audit_event(
        action='INVOICE_WORKFLOW_STATUS_CHANGED',
        entity_type='INVOICE',
        entity_id=invoice.id,
        actor=actor,
        request=request,
        changes={'approval_status': invoice.approval_status, 'processing_status': invoice.processing_status},
    )
    return approval_request
