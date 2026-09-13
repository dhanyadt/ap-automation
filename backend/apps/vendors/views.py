from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from common.permissions import IsAPClerkRole
from common.utils import api_response
from apps.audit.services import log_audit_event
from .models import Vendor, VendorBankAccount
from .serializers import VendorSerializer, VendorBankAccountSerializer

class VendorFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Vendor.Status.choices)
    msme_registered = filters.BooleanFilter()
    city = filters.CharFilter(lookup_expr='icontains')
    state = filters.CharFilter(lookup_expr='icontains')
    gstin = filters.CharFilter(lookup_expr='iexact')
    code = filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = Vendor
        fields = ['status', 'msme_registered', 'city', 'state', 'gstin', 'code']


class VendorViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Vendor Master records with audit tracking and bank account management.
    """
    queryset = Vendor.objects.prefetch_related('bank_accounts', 'purchase_orders', 'invoices').all()
    serializer_class = VendorSerializer
    filterset_class = VendorFilter
    search_fields = ['name', 'code', 'gstin', 'email', 'city']
    ordering_fields = ['name', 'code', 'created_at', 'status']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate', 'deactivate']:
            return [IsAPClerkRole()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        vendor = serializer.save()
        log_audit_event(
            action='VENDOR_CREATED',
            entity_type='VENDOR',
            entity_id=vendor.id,
            request=self.request,
            changes={'name': vendor.name, 'code': vendor.code, 'gstin': vendor.gstin}
        )

    def perform_update(self, serializer):
        vendor = serializer.save()
        log_audit_event(
            action='VENDOR_UPDATED',
            entity_type='VENDOR',
            entity_id=vendor.id,
            request=self.request,
            changes={'name': vendor.name, 'code': vendor.code, 'status': vendor.status}
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAPClerkRole])
    def activate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = Vendor.Status.ACTIVE
        vendor.save(update_fields=['status', 'updated_at'])
        log_audit_event(
            action='VENDOR_ACTIVATED',
            entity_type='VENDOR',
            entity_id=vendor.id,
            request=request
        )
        return api_response(data=VendorSerializer(vendor).data, message=f"Vendor {vendor.name} activated successfully.")

    @action(detail=True, methods=['post'], permission_classes=[IsAPClerkRole])
    def deactivate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = Vendor.Status.INACTIVE
        vendor.save(update_fields=['status', 'updated_at'])
        log_audit_event(
            action='VENDOR_DEACTIVATED',
            entity_type='VENDOR',
            entity_id=vendor.id,
            request=request
        )
        return api_response(data=VendorSerializer(vendor).data, message=f"Vendor {vendor.name} deactivated successfully.")

    @action(detail=True, methods=['get', 'post'], url_path='bank-accounts', permission_classes=[IsAPClerkRole])
    def bank_accounts(self, request, pk=None):
        vendor = self.get_object()
        if request.method == 'GET':
            accounts = vendor.bank_accounts.all()
            return Response({
                'success': True,
                'data': VendorBankAccountSerializer(accounts, many=True).data
            })
        
        serializer = VendorBankAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # If this is marked primary, unmark existing primary accounts
        if serializer.validated_data.get('is_primary', False):
            vendor.bank_accounts.filter(is_primary=True).update(is_primary=False)
            
        bank_account = serializer.save(vendor=vendor)
        log_audit_event(
            action='BANK_ACCOUNT_ADDED',
            entity_type='VENDOR_BANK_ACCOUNT',
            entity_id=bank_account.id,
            request=request,
            changes={'bank_name': bank_account.bank_name, 'ifsc': bank_account.ifsc_code}
        )
        return Response({
            'success': True,
            'message': 'Bank account added successfully.',
            'data': VendorBankAccountSerializer(bank_account).data
        }, status=status.HTTP_201_CREATED)
