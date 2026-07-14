"""OCR service for extracting purchase bill data from images."""
import re
import os
from datetime import datetime


def _preprocess_image(image_path: str):
    """Load and preprocess image for better OCR accuracy."""
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        import io

        img = Image.open(image_path)

        # Convert to grayscale
        img = img.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Simple threshold (binarize) using point function
        img = img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')

        return img
    except ImportError:
        return None
    except Exception:
        return None


def _parse_ocr_text(text: str) -> dict:
    """Parse raw OCR text and extract structured purchase bill data."""
    result = {
        'supplier_name': '',
        'invoice_number': '',
        'date': '',
        'items': [],
    }

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # --- Supplier name: first non-empty line heuristic ---
    if lines:
        result['supplier_name'] = lines[0][:100]

    # --- Invoice number ---
    inv_pattern = re.compile(
        r'(?:invoice|inv|bill|receipt)[:\s#no.]*([A-Z0-9/-]{3,20})',
        re.IGNORECASE,
    )
    m = inv_pattern.search(text)
    if m:
        result['invoice_number'] = m.group(1).strip()

    # --- Date ---
    date_pattern = re.compile(
        r'(?:date|dt)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        re.IGNORECASE,
    )
    m = date_pattern.search(text)
    if m:
        result['date'] = m.group(1).strip()
    else:
        # Fallback: any date-like string
        m = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{2,4})\b', text)
        if m:
            result['date'] = m.group(1)

    # --- Line items ---
    # Pattern: item name | batch | expiry | qty | rate | mrp | gst%
    # Try to capture tabular rows: word/number sequences
    item_pattern = re.compile(
        r'([A-Za-z][A-Za-z0-9 /-]{3,40})\s+'           # medicine name
        r'([A-Z0-9/-]{3,20})\s+'                         # batch
        r'(\d{2}[/-]\d{2,4})\s+'                         # expiry (MM/YY or MM/YYYY)
        r'(\d+)\s+'                                       # qty
        r'(\d+(?:\.\d{1,2})?)\s+'                        # rate
        r'(\d+(?:\.\d{1,2})?)\s*'                        # mrp
        r'(?:(\d+(?:\.\d{1,2})?)%?)?',                   # gst%
        re.IGNORECASE,
    )
    for m in item_pattern.finditer(text):
        result['items'].append({
            'medicine_name': m.group(1).strip(),
            'batch':         m.group(2).strip(),
            'expiry':        m.group(3).strip(),
            'qty':           int(m.group(4)),
            'rate':          float(m.group(5)),
            'mrp':           float(m.group(6)),
            'gst_pct':       float(m.group(7)) if m.group(7) else 12.0,
        })

    return result


def _compute_confidence(parsed: dict) -> int:
    """Return a confidence score 0-100 based on what was successfully parsed."""
    score = 0
    if parsed.get('supplier_name'):
        score += 20
    if parsed.get('invoice_number'):
        score += 25
    if parsed.get('date'):
        score += 15
    items = parsed.get('items', [])
    if items:
        score += min(40, len(items) * 10)
    return min(score, 100)


def extract_purchase_bill(image_path: str) -> dict:
    """Extract purchase bill data from an image using OCR.

    Args:
        image_path: Absolute path to the bill image (JPEG/PNG/TIFF).

    Returns:
        dict with keys:
            success (bool)
            data (dict): supplier_name, invoice_number, date, items list
            confidence (int): 0-100
            needs_review (bool): True if confidence < 80
            error (str | None)
    """
    # --- Try real tesseract path ---
    try:
        import pytesseract

        img = _preprocess_image(image_path)

        if img is None:
            # Try loading without PIL preprocessing
            from PIL import Image
            img = Image.open(image_path)

        # Run OCR
        custom_config = r'--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(img, config=custom_config)

        parsed = _parse_ocr_text(raw_text)
        confidence = _compute_confidence(parsed)

        return {
            'success':      True,
            'data':         parsed,
            'confidence':   confidence,
            'needs_review': confidence < 80,
            'raw_text':     raw_text[:500],
            'error':        None,
        }

    except ImportError:
        # pytesseract or PIL not installed — return safe mock data
        mock_data = {
            'supplier_name':  'Scan failed – please fill manually',
            'invoice_number': '',
            'date':           datetime.today().strftime('%d/%m/%Y'),
            'items': [
                {
                    'medicine_name': '',
                    'batch':  '',
                    'expiry': '',
                    'qty':    1,
                    'rate':   0.0,
                    'mrp':    0.0,
                    'gst_pct': 12.0,
                }
            ],
        }
        return {
            'success':      False,
            'data':         mock_data,
            'confidence':   0,
            'needs_review': True,
            'raw_text':     '',
            'error':        'pytesseract/PIL not available — OCR disabled.',
        }

    except Exception as exc:
        mock_data = {
            'supplier_name':  '',
            'invoice_number': '',
            'date':           datetime.today().strftime('%d/%m/%Y'),
            'items':          [],
        }
        return {
            'success':      False,
            'data':         mock_data,
            'confidence':   0,
            'needs_review': True,
            'raw_text':     '',
            'error':        str(exc),
        }
