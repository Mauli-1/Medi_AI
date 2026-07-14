"""Supplier model."""
from datetime import datetime
from ..extensions import db


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id               = db.Column(db.Integer, primary_key=True)
    business_id      = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                                 nullable=False, index=True)

    # Identification
    supplier_code    = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name             = db.Column(db.String(200), nullable=False, index=True)
    contact_person   = db.Column(db.String(150))
    phone            = db.Column(db.String(15))
    email            = db.Column(db.String(120))

    # Regulatory
    gst_number       = db.Column(db.String(15))
    drug_license_no  = db.Column(db.String(50))

    # Address
    address          = db.Column(db.Text)
    city             = db.Column(db.String(100))
    state            = db.Column(db.String(50))

    # Financial
    payment_terms    = db.Column(db.Integer, default=30)   # days
    credit_limit     = db.Column(db.Numeric(12, 2), default=0.00)
    outstanding      = db.Column(db.Numeric(12, 2), default=0.00)

    # Performance
    performance_score = db.Column(db.Numeric(3, 1), default=5.0)

    # Status
    is_active        = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted       = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow, nullable=False)

    # Relationships
    purchase_orders  = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    purchases        = db.relationship('Purchase', backref='supplier', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.supplier_code}: {self.name}>'

    def to_dict(self):
        return {
            'id':             self.id,
            'supplier_code':  self.supplier_code,
            'name':           self.name,
            'contact_person': self.contact_person,
            'phone':          self.phone,
            'email':          self.email,
            'outstanding':    float(self.outstanding),
            'performance_score': float(self.performance_score),
            'is_active':      self.is_active,
        }
