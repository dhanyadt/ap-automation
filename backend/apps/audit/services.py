import logging
from typing import Optional, Dict, Any
from django.http import HttpRequest
from apps.accounts.models import User
from .models import AuditLog

logger = logging.getLogger(__name__)

def get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """Extracts client IP address safely from HttpRequest."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def log_audit_event(
    action: str,
    entity_type: str,
    entity_id: Any,
    actor: Optional[User] = None,
    request: Optional[HttpRequest] = None,
    changes: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Append-only audit log recorder.
    Logs actions performed on critical entities across the AP lifecycle.
    """
    try:
        user = actor
        if not user and request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

        ip_address = get_client_ip(request)

        audit_entry = AuditLog.objects.create(
            actor=user,
            action=action.upper(),
            entity_type=entity_type.upper(),
            entity_id=str(entity_id),
            changes=changes or {},
            ip_address=ip_address
        )
        return audit_entry
    except Exception as e:
        logger.error(f"Failed to write audit log for {action} on {entity_type} {entity_id}: {e}", exc_info=True)
        return None
