import pytest

@pytest.mark.django_db
class TestRoleBasedAccessControl:
    def test_admin_can_access_user_list(self, admin_client):
        response = admin_client.get('/api/v1/users/')
        assert response.status_code == 200

    def test_ap_clerk_forbidden_from_user_list(self, clerk_client):
        response = clerk_client.get('/api/v1/users/')
        assert response.status_code == 403

    def test_ap_clerk_can_create_vendor(self, clerk_client):
        response = clerk_client.post('/api/v1/vendors/', {
            'name': 'Infosys Limited',
            'code': 'VEND-INFY-001',
            'gstin': '29AAACI4383F1Z2',
            'pan': 'AAACI4383F',
            'email': 'finance@infosys.com',
            'city': 'Bengaluru',
            'state': 'Karnataka',
        })
        assert response.status_code == 201

    def test_approver_forbidden_from_creating_vendor(self, approver_client):
        response = approver_client.post('/api/v1/vendors/', {
            'name': 'Unauthorized Vendor Test',
            'code': 'VEND-UNAUTH',
        })
        assert response.status_code == 403

    def test_approver_can_read_vendors(self, approver_client, sample_vendor):
        response = approver_client.get('/api/v1/vendors/')
        assert response.status_code == 200
        assert response.data['count'] >= 1
