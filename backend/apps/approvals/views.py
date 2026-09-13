from django_filters import rest_framework as filters
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from common.permissions import IsApproverRole
from .models import ApprovalRequest
from .serializers import ApprovalDecisionSerializer, ApprovalRequestSerializer
from .services import ApprovalError, take_action


class ApprovalRequestFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=ApprovalRequest.Status.choices)
    invoice = filters.UUIDFilter(field_name='invoice_id')

    class Meta:
        model = ApprovalRequest
        fields = ['status', 'invoice']


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApprovalRequest.objects.select_related(
        'invoice', 'submitted_by',
    ).prefetch_related('actions', 'actions__actor').all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ApprovalRequestFilter
    search_fields = ['invoice__invoice_number', 'invoice__vendor__name']
    ordering_fields = ['created_at', 'status', 'current_step']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], permission_classes=[IsApproverRole])
    def approve(self, request, pk=None):
        return self._decide(request, pk, 'APPROVE')

    @action(detail=True, methods=['post'], permission_classes=[IsApproverRole])
    def reject(self, request, pk=None):
        return self._decide(request, pk, 'REJECT')

    @action(detail=True, methods=['post'], permission_classes=[IsApproverRole])
    def escalate(self, request, pk=None):
        return self._decide(request, pk, 'ESCALATE')

    def _decide(self, request, pk, action):
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            approval_request = take_action(
                pk,
                request.user,
                action,
                comments=serializer.validated_data['comments'],
                request=request,
            )
        except ApprovalRequest.DoesNotExist:
            raise ValidationError({'detail': 'Approval request does not exist.'})
        except ApprovalError as exc:
            raise PermissionDenied(str(exc))
        return Response(ApprovalRequestSerializer(approval_request).data, status=status.HTTP_200_OK)
