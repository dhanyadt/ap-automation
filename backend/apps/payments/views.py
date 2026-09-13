from django_filters import rest_framework as filters
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.invoices.models import Invoice
from common.permissions import IsFinanceRole
from .models import Payment
from .serializers import PaymentRequestSerializer, PaymentSerializer
from .services import PaymentError, create_payment_request, process_payment, payment_advice


class PaymentFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Payment.Status.choices)
    invoice = filters.UUIDFilter(field_name='invoice_id')
    vendor = filters.UUIDFilter(field_name='vendor_id')

    class Meta:
        model = Payment
        fields = ['status', 'invoice', 'vendor']


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related('invoice', 'vendor', 'initiated_by').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PaymentFilter
    search_fields = ['reference_number', 'invoice__invoice_number', 'vendor__name']
    ordering_fields = ['created_at', 'paid_at', 'amount', 'status']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'], permission_classes=[IsFinanceRole], url_path='request')
    def request_payment(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice = Invoice.objects.get(pk=serializer.validated_data['invoice'])
            payment = create_payment_request(
                invoice,
                initiated_by=request.user,
                payment_method=serializer.validated_data['payment_method'],
                request=request,
            )
        except Invoice.DoesNotExist:
            raise NotFound('Invoice does not exist.')
        except PaymentError as exc:
            raise ValidationError({'detail': str(exc)})
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsFinanceRole])
    def process(self, request, pk=None):
        try:
            payment = process_payment(pk, actor=request.user, request=request)
        except Payment.DoesNotExist:
            raise NotFound('Payment does not exist.')
        except PaymentError as exc:
            raise ValidationError({'detail': str(exc)})
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsFinanceRole])
    def advice(self, request, pk=None):
        try:
            payment = self.get_object()
        except Payment.DoesNotExist:
            raise NotFound('Payment does not exist.')
        return Response(payment_advice(payment), status=status.HTTP_200_OK)
