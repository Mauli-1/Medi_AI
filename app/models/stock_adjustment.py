"""StockAdjustment and StockAdjustmentItem models."""
from datetime import datetime
from ..extensions import db


class StockAdjustment(db.Model):
    __tablename__ = 'stock_adjustments'

    # Adjustment types
    TYPE_DAMAGE       = 'damage'
    TYPE_EXPIRY       = 'expiry'
    TYPE_CORRECTION   = 'correction'
    TYPE_OPENING      = 'opening'
    TYPE_TRANSFER_OUT = 'transfer_out'
    TYPE_TRANSFER_IN  = 'transfer_in'
    TYPE_RETURN       = 'return'
    TYPE_AUDIT        = 'audit'

    ADJUSTMENT_TYPES = [
        TYPE_DAMAGE, TYPE_EXPIRY, TYPE_CORRECTION, TYPE_OPENING,
        TYPE_TRANSFER_OUT, TYPE_TRANSFER_IN, TYPE_RETURN, TYPE_AUDIT,
    ]

    id           = db.Column(db.Integer, primary_key=True)
    business_id  = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    branch_id    = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    adj_number   = db.Column(db.String(30), unique=True, nullable=False)
    adj_type     = db.Column(db.String(20), nullable=False)
    reason       = db.Column(db.Text)
    notes        = db.Column(db.Text)
    adjusted_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                             nullable=True)
    approved_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                             nullable=True)
    status       = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow, nullable=False)

    # Relationships
    items        = db.relationship('StockAdjustmentItem', backref='adjustment', lazy='dynamic',
                                   cascade='all, delete-orphan')
    branch       = db.relationship('Branch', foreign_keys=[branch_id])
    adjuster     = db.relationship('User', foreign_keys=[adjusted_by])
    approver     = db.relationship('User', foreign_keys=[approved_by])

    def __repr__(self):
        return f'<StockAdjustment {self.adj_number}>'

    def to_dict(self):
        return {
            'id':          self.id,
            'adj_number':  self.adj_number,
            'adj_type':    self.adj_type,
            'status':      self.status,
            'reason':      self.reason,
            'created_at':  self.created_at.isoformat(),
        }


class StockAdjustmentItem(db.Model):
    __tablename__ = 'stock_adjustment_items'

    id              = db.Column(db.Integer, primary_key=True)
    adjustment_id   = db.Column(db.Integer, db.ForeignKey('stock_adjustments.id',
                                ondelete='CASCADE'), nullable=False, index=True)
    batch_id        = db.Column(db.Integer, db.ForeignKey('medicine_batches.id',
                                ondelete='CASCADE'), nullable=False)
    medicine_id     = db.Column(db.Integer, db.ForeignKey('medicines.id',
                                ondelete='CASCADE'), nullable=False)
    qty_before      = db.Column(db.Integer, nullable=False, default=0)
    qty_change      = db.Column(db.Integer, nullable=False, default=0)  # positive=add, negative=reduce
    qty_after       = db.Column(db.Integer, nullable=False, default=0)
    reason          = db.Column(db.String(200))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    batch    = db.relationship('MedicineBatch', foreign_keys=[batch_id])
    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])

    def __repr__(self):
        return f'<StockAdjustmentItem adj={self.adjustment_id} batch={self.batch_id} change={self.qty_change}>'
