from datetime import datetime
from ..extensions import db


class GstTransaction(db.Model):
    __tablename__ = 'gst_transactions'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    transaction_type = db.Column(db.Enum('sale', 'purchase', 'sale_return', 'purchase_return'), nullable=False, index=True)
    reference_id = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(20))
    gstin = db.Column(db.String(15))
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    taxable_value = db.Column(db.Numeric(12, 2), default=0)
    cgst_rate = db.Column(db.Numeric(5, 2), default=0)
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_rate = db.Column(db.Numeric(5, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_rate = db.Column(db.Numeric(5, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    hsn_code = db.Column(db.String(8))
    fy = db.Column(db.String(9), index=True)
    period = db.Column(db.String(7), index=True)
    filed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GstTransaction {self.transaction_type} ref={self.reference_id}>'
