from datetime import datetime
from ..extensions import db


class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    invoice_number = db.Column(db.String(25), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True, index=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='SET NULL'), nullable=True)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    subtotal = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_pct = db.Column(db.Numeric(5, 2), default=0)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    round_off = db.Column(db.Numeric(5, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    change_amount = db.Column(db.Numeric(10, 2), default=0)
    payment_mode = db.Column(db.Enum('cash', 'card', 'upi', 'credit', 'wallet'), default='cash')
    loyalty_points_used = db.Column(db.Integer, default=0)
    loyalty_points_earned = db.Column(db.Integer, default=0)
    is_gstin_bill = db.Column(db.Boolean, default=False)
    customer_gstin = db.Column(db.String(15))
    status = db.Column(db.Enum('draft', 'confirmed', 'cancelled'), default='confirmed')
    is_return = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    interaction_override_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    interaction_override_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('SaleItem', backref='sale', lazy='select', cascade='all, delete-orphan')
    prescription = db.relationship('Prescription', foreign_keys=[prescription_id])
    cashier = db.relationship('User', foreign_keys=[cashier_id])
    branch = db.relationship('Branch', foreign_keys=[branch_id])

    def __repr__(self):
        return f'<Sale {self.invoice_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat(),
            'total_amount': float(self.total_amount),
            'payment_mode': self.payment_mode,
            'status': self.status,
        }


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='RESTRICT'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    mrp = db.Column(db.Numeric(10, 2))
    selling_rate = db.Column(db.Numeric(10, 2))
    discount_pct = db.Column(db.Numeric(5, 2), default=0)
    gst_rate = db.Column(db.Numeric(5, 2), default=12)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), default=0)

    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])
    batch = db.relationship('MedicineBatch', foreign_keys=[batch_id])

    def __repr__(self):
        return f'<SaleItem sale={self.sale_id} med={self.medicine_id}>'


class SalesReturn(db.Model):
    __tablename__ = 'sales_returns'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    return_number = db.Column(db.String(25), unique=True, nullable=False, index=True)
    original_sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='RESTRICT'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(255))
    total_refund = db.Column(db.Numeric(12, 2), default=0)
    refund_mode = db.Column(db.Enum('cash', 'card', 'upi', 'credit_note'), default='cash')
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.Enum('pending', 'approved', 'processed'), default='processed')

    items = db.relationship('SalesReturnItem', backref='sales_return', lazy='select', cascade='all, delete-orphan')
    original_sale = db.relationship('Sale', foreign_keys=[original_sale_id])

    def __repr__(self):
        return f'<SalesReturn {self.return_number}>'


class SalesReturnItem(db.Model):
    __tablename__ = 'sales_return_items'

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('sales_returns.id', ondelete='CASCADE'), nullable=False)
    sale_item_id = db.Column(db.Integer, db.ForeignKey('sale_items.id', ondelete='RESTRICT'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='RESTRICT'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    refund_amount = db.Column(db.Numeric(10, 2), default=0)

    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])
    sale_item = db.relationship('SaleItem', foreign_keys=[sale_item_id])
