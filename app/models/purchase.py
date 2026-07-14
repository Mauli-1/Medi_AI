"""Purchase models: PurchaseOrder, PurchaseOrderItem, Purchase, PurchaseItem."""
from datetime import datetime, date
from ..extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id             = db.Column(db.Integer, primary_key=True)
    business_id    = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    branch_id      = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    po_number      = db.Column(db.String(30), unique=True, nullable=False, index=True)
    supplier_id    = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT'),
                               nullable=False, index=True)
    order_date     = db.Column(db.Date, nullable=False, default=date.today)
    expected_date  = db.Column(db.Date, nullable=True)

    STATUS_CHOICES = ['draft', 'sent', 'partial', 'received', 'cancelled']
    status         = db.Column(db.String(15), default='draft', nullable=False)

    total_amount   = db.Column(db.Numeric(12, 2), default=0.00)
    notes          = db.Column(db.Text)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                               nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    items          = db.relationship('PurchaseOrderItem', backref='purchase_order',
                                     lazy='select', cascade='all, delete-orphan')
    branch         = db.relationship('Branch', foreign_keys=[branch_id])
    creator        = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'

    def to_dict(self):
        return {
            'id':           self.id,
            'po_number':    self.po_number,
            'order_date':   self.order_date.isoformat() if self.order_date else None,
            'status':       self.status,
            'total_amount': float(self.total_amount),
            'supplier_name': self.supplier.name if self.supplier else '',
        }


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'

    id          = db.Column(db.Integer, primary_key=True)
    po_id       = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'),
                            nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    rate        = db.Column(db.Numeric(10, 2), default=0.00)

    # Relationships
    medicine    = db.relationship('Medicine', foreign_keys=[medicine_id])

    def __repr__(self):
        return f'<POItem po={self.po_id} med={self.medicine_id}>'


class Purchase(db.Model):
    __tablename__ = 'purchases'

    id              = db.Column(db.Integer, primary_key=True)
    business_id     = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                                nullable=False, index=True)
    branch_id       = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'),
                                nullable=False, index=True)
    bill_number     = db.Column(db.String(30), unique=True, nullable=False, index=True)
    po_id           = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='SET NULL'),
                                nullable=True)
    supplier_id     = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT'),
                                nullable=False, index=True)

    bill_date       = db.Column(db.Date, nullable=False, default=date.today)
    invoice_number  = db.Column(db.String(50))
    invoice_date    = db.Column(db.Date, nullable=True)

    # Amounts
    subtotal        = db.Column(db.Numeric(12, 2), default=0.00)
    discount_amount = db.Column(db.Numeric(12, 2), default=0.00)
    cgst_amount     = db.Column(db.Numeric(12, 2), default=0.00)
    sgst_amount     = db.Column(db.Numeric(12, 2), default=0.00)
    igst_amount     = db.Column(db.Numeric(12, 2), default=0.00)
    total_amount    = db.Column(db.Numeric(12, 2), default=0.00)
    paid_amount     = db.Column(db.Numeric(12, 2), default=0.00)
    due_amount      = db.Column(db.Numeric(12, 2), default=0.00)

    # Payment
    PAYMENT_MODES    = ['cash', 'bank_transfer', 'cheque', 'upi', 'credit']
    PAYMENT_STATUSES = ['unpaid', 'partial', 'paid']
    payment_mode    = db.Column(db.String(20), default='credit')
    payment_status  = db.Column(db.String(15), default='unpaid', nullable=False)

    # OCR
    ocr_bill_path   = db.Column(db.String(300))

    notes           = db.Column(db.Text)
    created_by      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                                nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    items           = db.relationship('PurchaseItem', backref='purchase',
                                      lazy='select', cascade='all, delete-orphan')
    branch          = db.relationship('Branch', foreign_keys=[branch_id])
    purchase_order  = db.relationship('PurchaseOrder', foreign_keys=[po_id])
    creator         = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<Purchase {self.bill_number}>'

    def to_dict(self):
        return {
            'id':             self.id,
            'bill_number':    self.bill_number,
            'bill_date':      self.bill_date.isoformat() if self.bill_date else None,
            'invoice_number': self.invoice_number,
            'total_amount':   float(self.total_amount),
            'paid_amount':    float(self.paid_amount),
            'due_amount':     float(self.due_amount),
            'payment_status': self.payment_status,
            'supplier_name':  self.supplier.name if self.supplier else '',
        }


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id              = db.Column(db.Integer, primary_key=True)
    purchase_id     = db.Column(db.Integer, db.ForeignKey('purchases.id', ondelete='CASCADE'),
                                nullable=False, index=True)
    medicine_id     = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'),
                                nullable=False)

    batch_number    = db.Column(db.String(50), nullable=False)
    mfg_date        = db.Column(db.Date, nullable=True)
    expiry_date     = db.Column(db.Date, nullable=False)

    quantity        = db.Column(db.Integer, nullable=False, default=1)
    free_quantity   = db.Column(db.Integer, default=0)
    purchase_rate   = db.Column(db.Numeric(10, 2), default=0.00)
    mrp             = db.Column(db.Numeric(10, 2), default=0.00)
    discount_pct    = db.Column(db.Numeric(5, 2), default=0.00)
    gst_rate        = db.Column(db.Numeric(5, 2), default=12.00)
    cgst_amount     = db.Column(db.Numeric(10, 2), default=0.00)
    sgst_amount     = db.Column(db.Numeric(10, 2), default=0.00)
    igst_amount     = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount    = db.Column(db.Numeric(10, 2), default=0.00)

    # Relationships
    medicine        = db.relationship('Medicine', foreign_keys=[medicine_id])

    def __repr__(self):
        return f'<PurchaseItem purchase={self.purchase_id} med={self.medicine_id}>'

    @property
    def taxable_amount(self):
        base = float(self.purchase_rate) * self.quantity
        disc = base * float(self.discount_pct) / 100
        return base - disc
