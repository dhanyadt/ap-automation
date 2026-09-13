import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Standardized REST Framework exception handler ensuring consistent JSON error responses:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human readable message",
            "details": ...
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'success': False,
            'error': {
                'code': getattr(exc, 'default_code', 'API_ERROR').upper(),
                'message': str(exc.detail) if hasattr(exc, 'detail') and isinstance(exc.detail, (str, list)) else 'An error occurred during request processing.',
                'details': response.data
            }
        }
        response.data = custom_data
        return response

    # Unhandled exceptions
    logger.exception("Unhandled server exception: %s", exc, exc_info=context.get('request'))
    return Response(
        {
            'success': False,
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected server error occurred.',
                'details': str(exc) if getattr(context.get('request'), 'user', None) and getattr(context.get('request').user, 'is_staff', False) else None
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
