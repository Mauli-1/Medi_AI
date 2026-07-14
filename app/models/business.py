"""Business (pharmacy) model — stores the master pharmacy profile."""
from datetime import datetime
from ..extensions import db


class Business(db.Model):
    __tablename__ = 'businesses'

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(200), nullable=False)
    legal_name       = db.Column(db.String(200))
    short_name       = db.Column(db.String(50))

    # Contact
    email            = db.Column(db.String(120))
    phone            = db.Column(db.String(15))
    alt_phone        = db.Column(db.String(15))
    website          = db.Column(db.String(200))

    # Address
    address_line1    = db.Column(db.String(200))
    address_line2    = db.Column(db.String(200))
    city             = db.Column(db.String(100))
    state            = db.Column(db.String(50))
    pincode          = db.Column(db.String(10))
    country          = db.Column(db.String(50), default='India')

    # Regulatory
    gstin            = db.Column(db.String(15), unique=True)
    pan              = db.Column(db.String(10))
    drug_license_no  = db.Column(db.String(50))
    drug_license_no2 = db.Column(db.String(50))   # wholesale license if any
    fssai_no         = db.Column(db.String(20))

    # Banking
    bank_name        = db.Column(db.String(100))
    bank_branch      = db.Column(db.String(100))
    bank_account_no  = db.Column(db.String(20))
    bank_ifsc        = db.Column(db.String(11))
    upi_id           = db.Column(db.String(50))

    # Branding
    logo_filename    = db.Column(db.String(200))
    signature_filename = db.Column(db.String(200))
    tagline          = db.Column(db.String(200))

    # Operational settings
    currency         = db.Column(db.String(5), default='INR')
    timezone         = db.Column(db.String(50), default='Asia/Kolkata')
    date_format      = db.Column(db.String(20), default='DD-MM-YYYY')
    financial_year_start = db.Column(db.Integer, default=4)  # April

    # GST settings
    is_gst_registered  = db.Column(db.Boolean, default=True)
    default_gst_rate   = db.Column(db.Numeric(5, 2), default=12.0)
    default_supply_type = db.Column(db.String(10), default='intra')

    # Invoice settings
    invoice_prefix   = db.Column(db.String(10), default='INV')
    po_prefix        = db.Column(db.String(10), default='PO')
    gr_prefix        = db.Column(db.String(10), default='GRN')
    return_prefix    = db.Column(db.String(10), default='RET')
    invoice_terms    = db.Column(db.Text)
    invoice_footer   = db.Column(db.Text)

    # Features flags
    enable_loyalty      = db.Column(db.Boolean, default=False)
    enable_whatsapp     = db.Column(db.Boolean, default=False)
    enable_abha         = db.Column(db.Boolean, default=False)
    enable_eprescription = db.Column(db.Boolean, default=False)
    enable_barcode      = db.Column(db.Boolean, default=True)
    enable_sms          = db.Column(db.Boolean, default=False)

    # Setup wizard
    setup_complete   = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow, nullable=False)

    # Relationships
    branches = db.relationship('Branch', backref='business', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Business {self.name}>'

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'legal_name':  self.legal_name,
            'gstin':       self.gstin,
            'phone':       self.phone,
            'email':       self.email,
            'city':        self.city,
            'state':       self.state,
        }
