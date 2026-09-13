from rest_framework import viewsets, permissions
from django_filters import rest_framework as filters
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogFilter(filters.FilterSet):
    entity_type = filters.CharFilter(lookup_expr='iexact')
    entity_id = filters.CharFilter(lookup_expr='exact')
    action = filters.CharFilter(lookup_expr='iexact')
    from_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ['entity_type', 'entity_id', 'action', 'actor']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for immutable audit records.
    """
    queryset = AuditLog.objects.select_related('actor').all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = AuditLogFilter
    search_fields = ['action', 'entity_type', 'entity_id', 'actor__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
