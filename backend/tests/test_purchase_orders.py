import pytest
from decimal import Decimal
from apps.audit.models import AuditLog

@pytest.mark.django_db
class TestPurchaseOrders:
    def test_create_po_with_items(self, clerk_client, sample_vendor):
        payload = {
            'po_number': 'PO-2026-TEST-002',
            'vendor': str(sample_vendor.id),
            'issue_date': '2026-05-01',
            'delivery_date': '2026-05-15',
            'items': [
                {
                    'line_number': 1,
                    'item_code': 'ITEM-MONITOR-01',
                    'description': '27-inch 4K IPS Monitor',
                    'quantity': '10.00',
                    'unit_price': '25000.00',
                    'tax_rate': '18.00',
                },
                {
                    'line_number': 2,
                    'item_code': 'ITEM-KB-02',
                    'description': 'Mechanical Keyboard',
                    'quantity': '10.00',
                    'unit_price': '5000.00',
                    'tax_rate': '18.00',
                }
            ]
        }
        response = clerk_client.post('/api/v1/purchase-orders/', payload, format='json')
        assert response.status_code == 201
        data = response.data
        assert data['po_number'] == 'PO-2026-TEST-002'
        assert data['vendor_name'] == sample_vendor.name
        
        # Subtotal: (10 * 25000) + (10 * 5000) = 250000 + 50000 = 300,000.00
        # Tax (18%): 54,000.00
        # Total: 354,000.00
        assert Decimal(data['subtotal']) == Decimal('300000.00')
        assert Decimal(data['tax_amount']) == Decimal('54000.00')
        assert Decimal(data['total_amount']) == Decimal('354000.00')
        assert len(data['items']) == 2

        # Verify audit record
        audit = AuditLog.objects.filter(entity_type='PURCHASE_ORDER', entity_id=data['id']).first()
        assert audit is not None
        assert audit.action == 'PO_CREATED'

    def test_retrieve_po_and_filtering(self, clerk_client, sample_po):
        # Retrieve by id
        res = clerk_client.get(f'/api/v1/purchase-orders/{sample_po.id}/')
        assert res.status_code == 200
        assert res.data['po_number'] == sample_po.po_number
        assert len(res.data['items']) == 1

        # Filter by po_number
        filter_res = clerk_client.get('/api/v1/purchase-orders/?po_number=PO-2026-001')
        assert filter_res.status_code == 200
        assert filter_res.data['count'] == 1
