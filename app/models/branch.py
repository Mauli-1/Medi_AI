"""Branch model — a single physical outlet of the pharmacy business."""
from datetime import datetime
from ..extensions import db


class Branch(db.Model):
    __tablename__ = 'branches'

    id              = db.Column(db.Integer, primary_key=True)
    business_id     = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                                nullable=False)

    name            = db.Column(db.String(200), nullable=False)
    code            = db.Column(db.String(20), unique=True, nullable=False)
    is_headquarters = db.Column(db.Boolean, default=False)
    is_active       = db.Column(db.Boolean, default=True)

    # Contact
    phone           = db.Column(db.String(15))
    email           = db.Column(db.String(120))

    # Address
    address_line1   = db.Column(db.String(200))
    address_line2   = db.Column(db.String(200))
    city            = db.Column(db.String(100))
    state           = db.Column(db.String(50))
    pincode         = db.Column(db.String(10))

    # Regulatory (branch-specific)
    drug_license_no = db.Column(db.String(50))
    gstin           = db.Column(db.String(15))

    # Manager / in-charge
    manager_name    = db.Column(db.String(100))
    manager_phone   = db.Column(db.String(15))

    # Operational
    opening_time    = db.Column(db.Time)
    closing_time    = db.Column(db.Time)

    # Timestamps
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = db.relationship('User', backref='branch', lazy='dynamic')

    def __repr__(self):
        return f'<Branch {self.code}: {self.name}>'

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'code':        self.code,
            'city':        self.city,
            'is_active':   self.is_active,
        }
