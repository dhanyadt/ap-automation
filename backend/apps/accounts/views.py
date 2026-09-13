from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from common.permissions import IsAdminUserRole
from .models import User
from .serializers import CustomTokenObtainPairSerializer, CurrentUserSerializer, UserSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint: Authenticates user credentials (email & password)
    and returns JWT access and refresh tokens along with user profile metadata.
    """
    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserView(APIView):
    """
    Protected endpoint: Returns currently authenticated user's profile and RBAC role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-only user management viewset.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUserRole]
    search_fields = ['email', 'first_name', 'last_name', 'department']
    filterset_fields = ['role', 'is_active', 'department']
