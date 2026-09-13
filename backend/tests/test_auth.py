import pytest
from rest_framework_simplejwt.tokens import AccessToken

@pytest.mark.django_db
class TestAuthentication:
    def test_login_success(self, api_client, ap_clerk_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'clerk_test@apautomation.com',
            'password': 'TestPassword123!'
        })
        assert response.status_code == 200
        data = response.data
        assert 'access' in data
        assert 'refresh' in data
        assert 'user' in data
        assert data['user']['email'] == ap_clerk_user.email
        assert data['user']['role'] == 'AP_CLERK'
        assert data['user']['department'] == 'Accounts Payable'

        # Verify claims inside JWT token
        token = AccessToken(data['access'])
        assert token['email'] == ap_clerk_user.email
        assert token['role'] == 'AP_CLERK'
        assert token['department'] == 'Accounts Payable'

    def test_login_invalid_password(self, api_client, ap_clerk_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'clerk_test@apautomation.com',
            'password': 'WrongPassword!'
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post('/api/v1/auth/login/', {
            'email': 'nonexistent@apautomation.com',
            'password': 'SomePassword123!'
        })
        assert response.status_code == 401

    def test_token_refresh(self, api_client, ap_clerk_user):
        login_res = api_client.post('/api/v1/auth/login/', {
            'email': 'clerk_test@apautomation.com',
            'password': 'TestPassword123!'
        })
        refresh_token = login_res.data['refresh']

        refresh_res = api_client.post('/api/v1/auth/refresh/', {
            'refresh': refresh_token
        })
        assert refresh_res.status_code == 200
        assert 'access' in refresh_res.data

    def test_current_user_me_authenticated(self, clerk_client, ap_clerk_user):
        response = clerk_client.get('/api/v1/auth/me/')
        assert response.status_code == 200
        data = response.data['data']
        assert data['email'] == ap_clerk_user.email
        assert data['role'] == 'AP_CLERK'
        assert data['full_name'] == ap_clerk_user.get_full_name()

    def test_current_user_me_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/auth/me/')
        assert response.status_code == 401
