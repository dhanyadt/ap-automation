from rest_framework.permissions import BasePermission

class IsAdminUserRole(BasePermission):
    """Allows access only to users with ADMIN role or is_superuser."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role == 'ADMIN' or request.user.is_superuser
        ))

class IsAPClerkRole(BasePermission):
    """Allows access to AP_CLERK or ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in ('AP_CLERK', 'ADMIN') or request.user.is_superuser
        ))

class IsApproverRole(BasePermission):
    """Allows access to APPROVER, FINANCE, CFO, or ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in ('APPROVER', 'FINANCE', 'CFO', 'ADMIN') or request.user.is_superuser
        ))

class IsFinanceRole(BasePermission):
    """Allows access to FINANCE, CFO, or ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in ('FINANCE', 'CFO', 'ADMIN') or request.user.is_superuser
        ))

class IsCFORole(BasePermission):
    """Allows access only to CFO or ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in ('CFO', 'ADMIN') or request.user.is_superuser
        ))

class IsVendorRole(BasePermission):
    """Allows access to VENDOR or ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in ('VENDOR', 'ADMIN') or request.user.is_superuser
        ))
