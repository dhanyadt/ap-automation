import uuid
from decimal import Decimal
from django.db import models
from common.models import TimeStampedModel
from apps.accounts.models import User
from apps.invoices.models import Invoice

class ApprovalMatrixRule(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    min_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    max_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text='Null represents infinity (no upper bound)')
    required_role = models.CharField(max_length=20, choices=User.Role.choices)
    step_order = models.PositiveIntegerField(default=1, help_text='Order of approval stage (1, 2, 3...)')
    is_parallel = models.BooleanField(default=False, help_text='True if multiple approvers of this role can act concurrently at this stage')
    description = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'ap_approval_matrix_rules'
        ordering = ['min_amount', 'step_order']

    def __str__(self):
        max_str = f"₹{self.max_amount}" if self.max_amount else "Above"
        return f"Rule: ₹{self.min_amount} - {max_str} -> Stage {self.step_order} ({self.get_required_role_display()})"


class ApprovalRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        ESCALATED = 'ESCALATED', 'Escalated'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='approval_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    current_step = models.PositiveIntegerField(default=1)
    total_steps = models.PositiveIntegerField(default=1)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_approvals')

    class Meta:
        db_table = 'ap_approval_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval Req for {self.invoice.invoice_number} (Step {self.current_step}/{self.total_steps}: {self.status})"


class ApprovalAction(TimeStampedModel):
    class Action(models.TextChoices):
        APPROVE = 'APPROVE', 'Approve'
        REJECT = 'REJECT', 'Reject'
        ESCALATE = 'ESCALATE', 'Escalate'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='actions')
    step_order = models.PositiveIntegerField(default=1)
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='performed_approval_actions')
    role_acted_as = models.CharField(max_length=20, choices=User.Role.choices)
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    comments = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'ap_approval_actions'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.actor.email} {self.action} at Step {self.step_order}"
