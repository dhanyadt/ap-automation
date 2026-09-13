import pytest
from apps.audit.models import AuditLog

@pytest.mark.django_db
class TestVendors:
    def test_create_vendor(self, clerk_client):
        response = clerk_client.post('/api/v1/vendors/', {
            'name': 'Wipro Limited',
            'code': 'VEND-WIPRO-001',
            'gstin': '29AAACW3827F1Z8',
            'pan': 'AAACW3827F',
            'email': 'vendor@wipro.com',
            'phone': '+91 80 2844 0011',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'payment_terms_days': 45
        })
        assert response.status_code == 201
        data = response.data
        assert data['code'] == 'VEND-WIPRO-001'
        assert data['name'] == 'Wipro Limited'
        assert data['payment_terms_days'] == 45

        # Verify audit record created
        audit = AuditLog.objects.filter(entity_type='VENDOR', entity_id=data['id']).first()
        assert audit is not None
        assert audit.action == 'VENDOR_CREATED'

    def test_bank_account_masking(self, clerk_client, sample_vendor):
        # Retrieve vendor detail
        response = clerk_client.get(f'/api/v1/vendors/{sample_vendor.id}/')
        assert response.status_code == 200
        bank_accounts = response.data['bank_accounts']
        assert len(bank_accounts) == 1
        
        account = bank_accounts[0]
        # Raw account number MUST NOT be in response
        assert 'account_number' not in account or account.get('account_number') is None
        # Masked account number MUST be visible and formatted properly
        assert account['masked_account_number'] == 'XXXXXXXX9012'

    def test_add_bank_account(self, clerk_client, sample_vendor):
        response = clerk_client.post(f'/api/v1/vendors/{sample_vendor.id}/bank-accounts/', {
            'bank_name': 'HDFC Bank',
            'account_number': '98765432109876',
            'ifsc_code': 'HDFC0000001',
            'is_primary': True
        })
        assert response.status_code == 201
        data = response.data['data']
        assert data['bank_name'] == 'HDFC Bank'
        assert data['masked_account_number'] == 'XXXXXXXXXX9876'
        assert 'account_number' not in data

    def test_activate_deactivate_vendor(self, clerk_client, sample_vendor):
        # Deactivate
        deact_res = clerk_client.post(f'/api/v1/vendors/{sample_vendor.id}/deactivate/')
        assert deact_res.status_code == 200
        assert deact_res.data['data']['status'] == 'INACTIVE'

        # Activate
        act_res = clerk_client.post(f'/api/v1/vendors/{sample_vendor.id}/activate/')
        assert act_res.status_code == 200
        assert act_res.data['data']['status'] == 'ACTIVE'
