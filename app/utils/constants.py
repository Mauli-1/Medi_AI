"""Application-wide constants."""

# ─── User Roles ───────────────────────────────────────────────────────────────
ROLES = [
    'super_admin',
    'admin',
    'pharmacist',
    'cashier',
    'inventory_manager',
    'accountant',
    'doctor',
    'viewer',
]

ROLE_DISPLAY = {
    'super_admin':       'Super Admin',
    'admin':             'Admin',
    'pharmacist':        'Pharmacist',
    'cashier':           'Cashier',
    'inventory_manager': 'Inventory Manager',
    'accountant':        'Accountant',
    'doctor':            'Doctor',
    'viewer':            'Viewer',
}

# ─── GST ──────────────────────────────────────────────────────────────────────
GST_RATES = [0, 5, 12, 18, 28]

GST_SUPPLY_TYPES = [
    ('intra', 'Intra-State (CGST + SGST)'),
    ('inter', 'Inter-State (IGST)'),
]

# ─── Drug Schedules ───────────────────────────────────────────────────────────
SCHEDULE_TYPES = [
    ('OTC',        'Over The Counter'),
    ('H',          'Schedule H'),
    ('H1',         'Schedule H1'),
    ('X',          'Schedule X'),
    ('G',          'Schedule G'),
    ('C',          'Schedule C'),
    ('C1',         'Schedule C1'),
    ('J',          'Schedule J'),
    ('NONE',       'Not Scheduled'),
]

# ─── Indian States & UTs ──────────────────────────────────────────────────────
INDIAN_STATES = {
    'AN': 'Andaman and Nicobar Islands',
    'AP': 'Andhra Pradesh',
    'AR': 'Arunachal Pradesh',
    'AS': 'Assam',
    'BR': 'Bihar',
    'CH': 'Chandigarh',
    'CT': 'Chhattisgarh',
    'DN': 'Dadra and Nagar Haveli and Daman and Diu',
    'DL': 'Delhi',
    'GA': 'Goa',
    'GJ': 'Gujarat',
    'HR': 'Haryana',
    'HP': 'Himachal Pradesh',
    'JK': 'Jammu and Kashmir',
    'JH': 'Jharkhand',
    'KA': 'Karnataka',
    'KL': 'Kerala',
    'LA': 'Ladakh',
    'LD': 'Lakshadweep',
    'MP': 'Madhya Pradesh',
    'MH': 'Maharashtra',
    'MN': 'Manipur',
    'ML': 'Meghalaya',
    'MZ': 'Mizoram',
    'NL': 'Nagaland',
    'OD': 'Odisha',
    'PY': 'Puducherry',
    'PB': 'Punjab',
    'RJ': 'Rajasthan',
    'SK': 'Sikkim',
    'TN': 'Tamil Nadu',
    'TS': 'Telangana',
    'TR': 'Tripura',
    'UP': 'Uttar Pradesh',
    'UK': 'Uttarakhand',
    'WB': 'West Bengal',
}

# GSTIN state codes (numeric) -> state abbreviation
GSTIN_STATE_CODES = {
    '01': 'JK', '02': 'HP', '03': 'PB', '04': 'CH', '05': 'UK',
    '06': 'HR', '07': 'DL', '08': 'RJ', '09': 'UP', '10': 'BR',
    '11': 'SK', '12': 'AR', '13': 'NL', '14': 'MN', '15': 'MZ',
    '16': 'TR', '17': 'ML', '18': 'AS', '19': 'WB', '20': 'JH',
    '21': 'OD', '22': 'CT', '23': 'MP', '24': 'GJ', '25': 'DN',
    '26': 'MH', '27': 'MH', '28': 'AP', '29': 'KA', '30': 'GA',
    '31': 'LD', '32': 'KL', '33': 'TN', '34': 'PY', '35': 'AN',
    '36': 'TS', '37': 'AP', '38': 'LA',
}

# ─── Payment Modes ────────────────────────────────────────────────────────────
PAYMENT_MODES = [
    ('cash',         'Cash'),
    ('upi',          'UPI'),
    ('card',         'Debit/Credit Card'),
    ('netbanking',   'Net Banking'),
    ('cheque',       'Cheque'),
    ('neft',         'NEFT/RTGS'),
    ('credit',       'Store Credit'),
    ('insurance',    'Insurance'),
    ('mixed',        'Mixed'),
]

# ─── Units of Measurement ─────────────────────────────────────────────────────
UOM_TYPES = [
    ('tablet',  'Tablet'),
    ('capsule', 'Capsule'),
    ('ml',      'mL'),
    ('mg',      'mg'),
    ('gm',      'gm'),
    ('kg',      'kg'),
    ('strip',   'Strip'),
    ('bottle',  'Bottle'),
    ('tube',    'Tube'),
    ('sachet',  'Sachet'),
    ('vial',    'Vial'),
    ('ampoule', 'Ampoule'),
    ('unit',    'Unit'),
    ('pair',    'Pair'),
    ('piece',   'Piece'),
]

# ─── Invoice Types ────────────────────────────────────────────────────────────
INVOICE_TYPES = [
    ('retail',    'Retail'),
    ('wholesale', 'Wholesale'),
    ('credit',    'Credit'),
    ('cash',      'Cash'),
]

# ─── Expiry Warning Thresholds (days) ────────────────────────────────────────
EXPIRY_WARNING_DAYS = 90
EXPIRY_CRITICAL_DAYS = 30

# ─── Low Stock Threshold (default units) ─────────────────────────────────────
LOW_STOCK_DEFAULT = 10

# ─── Allowed File Extensions ─────────────────────────────────────────────────
ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOC_EXT   = {'pdf', 'doc', 'docx', 'xlsx', 'xls', 'csv'}
