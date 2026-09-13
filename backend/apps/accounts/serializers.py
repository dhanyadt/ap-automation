from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that injects role, email, and department into the token payload
    and returns user details in the authentication response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims (non-sensitive)
        token['email'] = user.email
        token['role'] = user.role
        token['department'] = user.department or ''
        token['full_name'] = user.get_full_name() or user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include user profile data directly in the login response
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'department': self.user.department,
            'is_staff': self.user.is_staff,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'department',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class CurrentUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'phone_number',
            'department',
            'is_staff',
            'is_superuser',
            'date_joined',
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email
