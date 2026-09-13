from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from common.permissions import IsAPClerkRole
from apps.audit.services import log_audit_event
from .models import PurchaseOrder, POItem
from .serializers import PurchaseOrderSerializer, POItemSerializer

class PurchaseOrderFilter(filters.FilterSet):
    vendor = filters.UUIDFilter(field_name='vendor__id')
    status = filters.ChoiceFilter(choices=PurchaseOrder.Status.choices)
    from_date = filters.DateFilter(field_name='issue_date', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='issue_date', lookup_expr='lte')
    po_number = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'status', 'po_number', 'from_date', 'to_date']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    Purchase Order management endpoint with line item handling and audit records.
    """
    queryset = PurchaseOrder.objects.select_related('vendor').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer
    filterset_class = PurchaseOrderFilter
    search_fields = ['po_number', 'vendor__name', 'vendor__code']
    ordering_fields = ['issue_date', 'total_amount', 'status', 'created_at']
    ordering = ['-issue_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAPClerkRole()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        po = serializer.save()
        log_audit_event(
            action='PO_CREATED',
            entity_type='PURCHASE_ORDER',
            entity_id=po.id,
            request=self.request,
            changes={
                'po_number': po.po_number,
                'vendor': po.vendor.name,
                'total_amount': str(po.total_amount),
                'items_count': po.items.count()
            }
        )

    def perform_update(self, serializer):
        po = serializer.save()
        log_audit_event(
            action='PO_UPDATED',
            entity_type='PURCHASE_ORDER',
            entity_id=po.id,
            request=self.request,
            changes={
                'po_number': po.po_number,
                'status': po.status,
                'total_amount': str(po.total_amount)
            }
        )
