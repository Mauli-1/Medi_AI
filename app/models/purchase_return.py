from datetime import datetime, date
from ..extensions import db


class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_returns'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    return_number = db.Column(db.String(25), unique=True, nullable=False, index=True)
    original_purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id', ondelete='RESTRICT'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=date.today)
    reason = db.Column(db.String(255))
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.Enum('pending', 'sent', 'credited'), default='pending')
    credit_note_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('PurchaseReturnItem', backref='purchase_return', lazy='select', cascade='all, delete-orphan')
    original_purchase = db.relationship('Purchase', foreign_keys=[original_purchase_id])

    def __repr__(self):
        return f'<PurchaseReturn {self.return_number}>'


class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_returns.id', ondelete='CASCADE'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id', ondelete='RESTRICT'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Numeric(10, 2), default=0)
    amount = db.Column(db.Numeric(10, 2), default=0)

    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])
    batch = db.relationship('MedicineBatch', foreign_keys=[batch_id])
