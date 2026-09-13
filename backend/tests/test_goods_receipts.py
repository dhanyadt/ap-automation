import pytest
from apps.audit.models import AuditLog

@pytest.mark.django_db
class TestGoodsReceipts:
    def test_create_grn(self, clerk_client, sample_po):
        po_item = sample_po.items.first()
        payload = {
            'grn_number': 'GRN-2026-TEST-001',
            'purchase_order': str(sample_po.id),
            'received_date': '2026-05-10',
            'delivery_challan_number': 'DC-998877',
            'received_by': 'Ramesh Storekeeper',
            'items': [
                {
                    'po_item': str(po_item.id),
                    'received_quantity': '2.00',
                    'accepted_quantity': '2.00',
                    'rejected_quantity': '0.00',
                    'remarks': 'Delivered in mint condition'
                }
            ]
        }
        response = clerk_client.post('/api/v1/goods-receipts/', payload, format='json')
        assert response.status_code == 201
        data = response.data
        assert data['grn_number'] == 'GRN-2026-TEST-001'
        assert data['po_number'] == sample_po.po_number
        assert len(data['items']) == 1

        # Audit verification
        audit = AuditLog.objects.filter(entity_type='GOODS_RECEIPT', entity_id=data['id']).first()
        assert audit is not None
        assert audit.action == 'GRN_CREATED'

    def test_grn_invalid_quantities(self, clerk_client, sample_po):
        po_item = sample_po.items.first()
        payload = {
            'grn_number': 'GRN-INVALID-QTY',
            'purchase_order': str(sample_po.id),
            'received_date': '2026-05-10',
            'items': [
                {
                    'po_item': str(po_item.id),
                    'received_quantity': '2.00',
                    'accepted_quantity': '3.00',  # Accepted > Received!
                    'rejected_quantity': '0.00'
                }
            ]
        }
        response = clerk_client.post('/api/v1/goods-receipts/', payload, format='json')
        assert response.status_code == 400
