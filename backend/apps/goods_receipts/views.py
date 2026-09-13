from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from common.permissions import IsAPClerkRole
from apps.audit.services import log_audit_event
from .models import GoodsReceipt, GRNItem
from .serializers import GoodsReceiptSerializer, GRNItemSerializer

class GoodsReceiptFilter(filters.FilterSet):
    purchase_order = filters.UUIDFilter(field_name='purchase_order__id')
    po_number = filters.CharFilter(field_name='purchase_order__po_number', lookup_expr='icontains')
    status = filters.ChoiceFilter(choices=GoodsReceipt.Status.choices)
    from_date = filters.DateFilter(field_name='received_date', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='received_date', lookup_expr='lte')
    grn_number = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = GoodsReceipt
        fields = ['purchase_order', 'po_number', 'status', 'grn_number', 'from_date', 'to_date']


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    """
    Goods Receipt Note (GRN) management endpoint for receiving goods against purchase orders.
    """
    queryset = GoodsReceipt.objects.select_related('purchase_order', 'purchase_order__vendor').prefetch_related('items', 'items__po_item').all()
    serializer_class = GoodsReceiptSerializer
    filterset_class = GoodsReceiptFilter
    search_fields = ['grn_number', 'purchase_order__po_number', 'delivery_challan_number']
    ordering_fields = ['received_date', 'created_at', 'status']
    ordering = ['-received_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAPClerkRole()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        grn = serializer.save()
        log_audit_event(
            action='GRN_CREATED',
            entity_type='GOODS_RECEIPT',
            entity_id=grn.id,
            request=self.request,
            changes={
                'grn_number': grn.grn_number,
                'po_number': grn.purchase_order.po_number,
                'items_count': grn.items.count()
            }
        )

    def perform_update(self, serializer):
        grn = serializer.save()
        log_audit_event(
            action='GRN_UPDATED',
            entity_type='GOODS_RECEIPT',
            entity_id=grn.id,
            request=self.request,
            changes={
                'grn_number': grn.grn_number,
                'status': grn.status
            }
        )
