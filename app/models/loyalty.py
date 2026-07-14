from datetime import datetime
from ..extensions import db


class LoyaltyProgram(db.Model):
    __tablename__ = 'loyalty_programs'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, unique=True)
    name = db.Column(db.String(100), default='Loyalty Program')
    points_per_rupee = db.Column(db.Numeric(5, 2), default=1)
    rupees_per_point = db.Column(db.Numeric(5, 2), default=0.25)
    min_redeem_points = db.Column(db.Integer, default=100)
    expiry_days = db.Column(db.Integer, default=365)
    silver_min_spend = db.Column(db.Numeric(12, 2), default=0)
    gold_min_spend = db.Column(db.Numeric(12, 2), default=10000)
    platinum_min_spend = db.Column(db.Numeric(12, 2), default=50000)
    silver_cashback_pct = db.Column(db.Numeric(5, 2), default=0)
    gold_cashback_pct = db.Column(db.Numeric(5, 2), default=2)
    platinum_cashback_pct = db.Column(db.Numeric(5, 2), default=5)
    referral_bonus_points = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<LoyaltyProgram business={self.business_id}>'

    def tier_for_spend(self, total_spend):
        total_spend = float(total_spend or 0)
        if total_spend >= float(self.platinum_min_spend or 0):
            return 'platinum'
        if total_spend >= float(self.gold_min_spend or 0):
            return 'gold'
        return 'silver'

    def cashback_pct_for_tier(self, tier):
        return float({
            'platinum': self.platinum_cashback_pct,
            'gold': self.gold_cashback_pct,
            'silver': self.silver_cashback_pct,
        }.get(tier, self.silver_cashback_pct) or 0)


class LoyaltyTransaction(db.Model):
    __tablename__ = 'loyalty_transactions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='SET NULL'), nullable=True)
    type = db.Column(db.Enum('earn', 'redeem', 'expire', 'adjust', 'referral', 'cashback'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', foreign_keys=[patient_id])

    def __repr__(self):
        return f'<LoyaltyTxn patient={self.patient_id} {self.type} {self.points}pts>'
