"""Domain-specific validators for Indian pharmacy compliance."""
import re
from .constants import GSTIN_STATE_CODES, INDIAN_STATES


def validate_gstin(gstin: str) -> tuple:
    """Validate a GSTIN (Goods and Services Tax Identification Number).

    Format: 2-digit state code + 10-char PAN + 1-digit entity number
            + 1 char 'Z' + 1 checksum char  (total 15 chars)

    Returns:
        (is_valid: bool, message: str)
    """
    if not gstin:
        return False, 'GSTIN is required.'

    gstin = gstin.strip().upper()

    if len(gstin) != 15:
        return False, f'GSTIN must be exactly 15 characters (got {len(gstin)}).'

    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    if not re.match(pattern, gstin):
        return False, 'GSTIN format is invalid.'

    state_code = gstin[:2]
    if state_code not in GSTIN_STATE_CODES:
        return False, f'Unknown state code "{state_code}" in GSTIN.'

    return True, 'Valid GSTIN.'


def validate_phone(phone: str) -> tuple:
    """Validate an Indian mobile number.

    Accepts: 10-digit number optionally prefixed with +91 or 0.

    Returns:
        (is_valid: bool, normalised_10_digit: str | None)
    """
    if not phone:
        return False, None

    digits = re.sub(r'[\s\-()]', '', phone)

    if digits.startswith('+91'):
        digits = digits[3:]
    elif digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]

    if not re.match(r'^[6-9]\d{9}$', digits):
        return False, None

    return True, digits


def validate_drug_license(license_no: str) -> tuple:
    """Validate an Indian Drug License number.

    Common formats:
      - Retail:     DL-XXXXXXXXXX  (e.g. DL-MH-01-2022-12345)
      - Wholesale:  WL-XXXXXXXXXX
      State boards use varied formats; this checks the common prefix pattern.

    Returns:
        (is_valid: bool, message: str)
    """
    if not license_no:
        return False, 'Drug license number is required.'

    license_no = license_no.strip().upper()

    # Minimum length sanity check
    if len(license_no) < 6:
        return False, 'Drug license number is too short.'

    # Accept DL/WL prefix patterns or purely alphanumeric state-specific formats
    pattern = r'^(DL|WL|20B|21B|20G|21G)[A-Z0-9\-\/]{4,}$'
    if re.match(pattern, license_no):
        return True, 'Valid drug license number.'

    # Some states issue purely numeric or state-prefix formats
    generic = r'^[A-Z]{2,4}[\/\-]?[A-Z0-9]{4,20}$'
    if re.match(generic, license_no):
        return True, 'Valid drug license number (state format).'

    return False, 'Drug license number format appears invalid.'


def get_state_from_gstin(gstin: str) -> str | None:
    """Extract and return the state name from a GSTIN.

    Returns the full state name string, or None if the GSTIN is invalid.
    """
    is_valid, _ = validate_gstin(gstin)
    if not is_valid:
        return None

    state_code = gstin[:2].upper()
    abbr = GSTIN_STATE_CODES.get(state_code)
    if abbr:
        return INDIAN_STATES.get(abbr)
    return None


def validate_pan(pan: str) -> tuple:
    """Validate a PAN (Permanent Account Number).

    Format: 5 alpha + 4 digits + 1 alpha (10 chars total).

    Returns:
        (is_valid: bool, message: str)
    """
    if not pan:
        return False, 'PAN is required.'

    pan = pan.strip().upper()
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pattern, pan):
        return False, 'PAN format is invalid (e.g. ABCDE1234F).'

    return True, 'Valid PAN.'


def validate_pincode(pincode: str) -> tuple:
    """Validate an Indian postal PIN code (6 digits, first digit 1-9).

    Returns:
        (is_valid: bool, message: str)
    """
    if not pincode:
        return False, 'PIN code is required.'

    pincode = pincode.strip()
    if re.match(r'^[1-9][0-9]{5}$', pincode):
        return True, 'Valid PIN code.'

    return False, 'PIN code must be a 6-digit number starting with 1–9.'


def validate_email(email: str) -> tuple:
    """Basic email format validation.

    Returns:
        (is_valid: bool, message: str)
    """
    if not email:
        return False, 'Email is required.'

    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email.strip()):
        return True, 'Valid email.'

    return False, 'Email format is invalid.'
