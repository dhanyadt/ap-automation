from rest_framework import serializers

from .models import ApprovalAction, ApprovalMatrixRule, ApprovalRequest
from .services import current_rule


class ApprovalMatrixRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalMatrixRule
        fields = [
            'id', 'name', 'min_amount', 'max_amount', 'required_role',
            'step_order', 'is_parallel', 'description',
        ]
        read_only_fields = fields


class ApprovalActionSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)

    class Meta:
        model = ApprovalAction
        fields = [
            'id', 'approval_request', 'step_order', 'actor', 'actor_email',
            'role_acted_as', 'action', 'comments', 'created_at',
        ]
        read_only_fields = fields


class ApprovalRequestSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_total = serializers.DecimalField(source='invoice.total_amount', max_digits=14, decimal_places=2, read_only=True)
    required_role = serializers.SerializerMethodField()
    actions = ApprovalActionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'invoice', 'invoice_number', 'invoice_total', 'status',
            'current_step', 'total_steps', 'submitted_by', 'required_role',
            'actions', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_required_role(self, obj):
        rule = current_rule(obj)
        return rule.required_role if rule else None


class ApprovalDecisionSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True, default='')
