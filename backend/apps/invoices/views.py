import os
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters import rest_framework as filters
from pypdf import PdfReader
from common.permissions import IsAPClerkRole
from common.utils import api_response, get_indian_fiscal_year
from .services import process_invoice
from apps.audit.services import log_audit_event
from apps.validations.serializers import ValidationResultSerializer
from apps.matching.serializers import MatchRunSerializer
from apps.approvals.serializers import ApprovalRequestSerializer
from apps.vendors.models import Vendor
from apps.purchase_orders.models import PurchaseOrder
from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceUploadSerializer, InvoiceItemSerializer

class InvoiceFilter(filters.FilterSet):
    vendor = filters.UUIDFilter(field_name='vendor__id')
    processing_status = filters.ChoiceFilter(choices=Invoice.ProcessingStatus.choices)
    ocr_status = filters.ChoiceFilter(choices=Invoice.OCRStatus.choices)
    validation_status = filters.ChoiceFilter(choices=Invoice.ValidationStatus.choices)
    matching_status = filters.ChoiceFilter(choices=Invoice.MatchingStatus.choices)
    approval_status = filters.ChoiceFilter(choices=Invoice.ApprovalStatus.choices)
    payment_status = filters.ChoiceFilter(choices=Invoice.PaymentStatus.choices)
    fiscal_year = filters.CharFilter(lookup_expr='iexact')
    invoice_number = filters.CharFilter(lookup_expr='icontains')
    from_date = filters.DateFilter(field_name='invoice_date', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='invoice_date', lookup_expr='lte')

    class Meta:
        model = Invoice
        fields = [
            'vendor',
            'processing_status',
            'ocr_status',
            'validation_status',
            'matching_status',
            'approval_status',
            'payment_status',
            'fiscal_year',
            'invoice_number',
            'from_date',
            'to_date',
        ]


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Core Invoice management endpoint supporting secure file upload, line items,
    and multi-stage lifecycle state tracking.
    """
    queryset = Invoice.objects.select_related('vendor', 'purchase_order').prefetch_related('items').all()
    serializer_class = InvoiceSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_class = InvoiceFilter
    search_fields = ['invoice_number', 'vendor__name', 'po_number', 'original_filename']
    ordering_fields = ['created_at', 'invoice_date', 'total_amount', 'processing_status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload', 'process']:
            return [IsAPClerkRole()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        invoice = serializer.save()
        log_audit_event(
            action='INVOICE_CREATED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            request=self.request,
            changes={
                'invoice_number': invoice.invoice_number,
                'vendor': invoice.vendor.name if invoice.vendor else None,
                'total_amount': str(invoice.total_amount)
            }
        )

    def perform_update(self, serializer):
        invoice = serializer.save()
        log_audit_event(
            action='INVOICE_UPDATED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            request=self.request,
            changes={
                'invoice_number': invoice.invoice_number,
                'processing_status': invoice.processing_status,
                'total_amount': str(invoice.total_amount)
            }
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAPClerkRole])
    def process(self, request, pk=None):
        invoice = self.get_object()
        result = process_invoice(invoice, actor=request.user, request=request)
        invoice.refresh_from_db()
        return Response({
            'success': True,
            'message': 'Invoice processing completed.',
            'data': {
                'invoice': InvoiceSerializer(invoice, context={'request': request}).data,
                'validation_results': ValidationResultSerializer(
                    invoice.validation_results.all(), many=True
                ).data,
                'match_run': (
                    MatchRunSerializer(result['match_run']).data
                    if result['match_run'] else None
                ),
                'approval_request': (
                    ApprovalRequestSerializer(result['approval_request']).data
                    if result['approval_request'] else None
                ),
            },
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Secure upload endpoint for invoice documents (PDF, JPG, PNG, TIFF).
        Validates file size, extension, MIME type, and registers the initial Invoice record.
        """
        upload_serializer = InvoiceUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        uploaded_file = upload_serializer.validated_data['file']
        vendor_id = upload_serializer.validated_data.get('vendor')
        po_number = upload_serializer.validated_data.get('po_number', '').strip()

        vendor = None
        if vendor_id:
            try:
                vendor = Vendor.objects.get(id=vendor_id)
            except Vendor.DoesNotExist:
                raise ValidationError({'vendor': 'Vendor does not exist.'})

        purchase_order = None
        if po_number:
            purchase_order = PurchaseOrder.objects.filter(po_number__iexact=po_number).first()
            if not vendor and purchase_order:
                vendor = purchase_order.vendor
            if vendor and purchase_order and purchase_order.vendor_id != vendor.id:
                raise ValidationError({'po_number': 'Purchase order does not belong to the selected vendor.'})

        # Detect pages count for PDFs safely
        pages_count = 1
        content_type = getattr(uploaded_file, 'content_type', 'application/pdf')
        if 'pdf' in content_type.lower() or uploaded_file.name.lower().endswith('.pdf'):
            try:
                reader = PdfReader(uploaded_file)
                pages_count = len(reader.pages)
                uploaded_file.seek(0)
            except Exception:
                pages_count = 1

        invoice = Invoice.objects.create(
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content_type=content_type,
            pages_count=pages_count,
            vendor=vendor,
            po_number=po_number,
            purchase_order=purchase_order,
            fiscal_year=get_indian_fiscal_year(),
            processing_status=Invoice.ProcessingStatus.UPLOADED,
            ocr_status=Invoice.OCRStatus.PENDING,
            validation_status=Invoice.ValidationStatus.PENDING,
            matching_status=Invoice.MatchingStatus.PENDING if purchase_order else Invoice.MatchingStatus.NOT_APPLICABLE,
            approval_status=Invoice.ApprovalStatus.NOT_SUBMITTED,
            payment_status=Invoice.PaymentStatus.NOT_REQUESTED,
        )

        log_audit_event(
            action='INVOICE_UPLOADED',
            entity_type='INVOICE',
            entity_id=invoice.id,
            request=request,
            changes={
                'filename': invoice.original_filename,
                'file_size': invoice.file_size,
                'pages_count': invoice.pages_count,
                'po_number': po_number
            }
        )

        response_serializer = InvoiceSerializer(invoice, context={'request': request})
        return Response({
            'success': True,
            'message': f"Invoice document '{invoice.original_filename}' uploaded successfully.",
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
