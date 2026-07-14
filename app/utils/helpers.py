"""General-purpose helper functions."""
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


def format_inr(amount) -> str:
    """Format a numeric value as Indian Rupees with comma grouping.

    Example: 1234567.50  ->  '₹12,34,567.50'
    """
    if amount is None:
        return '₹0.00'
    try:
        amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        return '₹0.00'

    negative = amount < 0
    amount = abs(amount)

    # Split integer and decimal parts
    str_amount = str(amount)
    if '.' in str_amount:
        integer_part, decimal_part = str_amount.split('.')
    else:
        integer_part, decimal_part = str_amount, '00'

    # Indian number grouping: last 3 digits, then groups of 2
    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        formatted = ','.join(groups) + ',' + last_three

    result = f'₹{formatted}.{decimal_part}'
    return f'-{result}' if negative else result


def calculate_gst(amount, rate: float, supply_type: str = 'intra') -> dict:
    """Calculate GST breakdown for a given amount and rate.

    Args:
        amount:      Base taxable amount (pre-GST).
        rate:        GST rate as a percentage (e.g. 18 for 18%).
        supply_type: 'intra' (CGST+SGST) or 'inter' (IGST).

    Returns:
        dict with keys: base, gst_rate, cgst, sgst, igst, total_gst, total.
    """
    base = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    gst_rate = Decimal(str(rate))
    gst_amount = (base * gst_rate / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if supply_type == 'intra':
        half = (gst_amount / Decimal('2')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {
            'base':       float(base),
            'gst_rate':   float(gst_rate),
            'cgst':       float(half),
            'sgst':       float(half),
            'igst':       0.0,
            'total_gst':  float(gst_amount),
            'total':      float(base + gst_amount),
        }
    else:
        return {
            'base':       float(base),
            'gst_rate':   float(gst_rate),
            'cgst':       0.0,
            'sgst':       0.0,
            'igst':       float(gst_amount),
            'total_gst':  float(gst_amount),
            'total':      float(base + gst_amount),
        }


def get_financial_year(ref_date: date = None) -> str:
    """Return financial year string for a given date.

    India FY: April 1 – March 31.
    Example: date(2024, 8, 10) -> '2024-25'
    """
    if ref_date is None:
        ref_date = date.today()
    if ref_date.month >= 4:
        return f'{ref_date.year}-{str(ref_date.year + 1)[-2:]}'
    else:
        return f'{ref_date.year - 1}-{str(ref_date.year)[-2:]}'


def allowed_file(filename: str, allowed_set: set) -> bool:
    """Return True if the filename has an allowed extension.

    Args:
        filename:    Original filename from the upload.
        allowed_set: Set of lowercase extensions without the dot.
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_set


def generate_code(prefix: str, number: int, pad: int = 6) -> str:
    """Generate a formatted code string.

    Example: generate_code('INV', 42) -> 'INV000042'
             generate_code('PO', 7, pad=4) -> 'PO0007'
    """
    return f'{prefix}{str(number).zfill(pad)}'


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """Truncate a string to max_length, appending suffix if truncated."""
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def days_until_expiry(expiry_date) -> int:
    """Return number of days until the expiry date from today.

    Negative value means already expired.
    """
    if expiry_date is None:
        return 9999
    if isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()
    delta = expiry_date - date.today()
    return delta.days


def get_current_financial_year_dates() -> tuple:
    """Return (start_date, end_date) for the current Indian financial year."""
    today = date.today()
    if today.month >= 4:
        start = date(today.year, 4, 1)
        end   = date(today.year + 1, 3, 31)
    else:
        start = date(today.year - 1, 4, 1)
        end   = date(today.year, 3, 31)
    return start, end


def get_state_from_gstin(gstin):
    """Return 2-digit state code from GSTIN."""
    if gstin and len(gstin) >= 2:
        return gstin[:2]
    return '27'
