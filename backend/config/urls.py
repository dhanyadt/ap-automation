from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.accounts.views import CustomTokenObtainPairView, CurrentUserView, UserViewSet
from apps.vendors.views import VendorViewSet
from apps.purchase_orders.views import PurchaseOrderViewSet
from apps.goods_receipts.views import GoodsReceiptViewSet
from apps.invoices.views import InvoiceViewSet
from apps.audit.views import AuditLogViewSet

def health_check(request):
    """Liveness & Readiness probe endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AP Automation Backend',
        'version': '1.0.0',
    })

# API v1 Router
router_v1 = DefaultRouter()
router_v1.register(r'users', UserViewSet, basename='user')
router_v1.register(r'vendors', VendorViewSet, basename='vendor')
router_v1.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router_v1.register(r'goods-receipts', GoodsReceiptViewSet, basename='goods-receipt')
router_v1.register(r'invoices', InvoiceViewSet, basename='invoice')
router_v1.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),

    # OpenAPI 3 Schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Auth Endpoints
    path('api/v1/auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('api/v1/auth/me/', CurrentUserView.as_view(), name='auth-me'),

    # Core Domain Resources
    path('api/v1/', include(router_v1.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
