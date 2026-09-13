from datetime import date
from rest_framework.response import Response

def api_response(data=None, message='Success', success=True, status=200):
    """
    Unified standard API response format:
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    return Response({
        'success': success,
        'message': message,
        'data': data
    }, status=status)

def mask_bank_account(account_number: str) -> str:
    """
    Masks a bank account number showing only the last 4 digits.
    Example: '123456789012' -> 'XXXXXXXX9012'
    """
    if not account_number:
        return ''
    clean = str(account_number).strip()
    if len(clean) <= 4:
        return clean
    return 'X' * (len(clean) - 4) + clean[-4:]

def get_indian_fiscal_year(dt: date = None) -> str:
    """
    Returns the Indian Financial Year (April 1 to March 31) string.
    Example: 2026-05-15 -> 'FY2026-27'
    Example: 2027-01-10 -> 'FY2026-27'
    """
    if dt is None:
        dt = date.today()
    
    year = dt.year
    if dt.month >= 4:
        return f"FY{year}-{str(year + 1)[-2:]}"
    else:
        return f"FY{year - 1}-{str(year)[-2:]}"
