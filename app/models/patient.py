from datetime import datetime
from ..extensions import db


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), index=True)
    email = db.Column(db.String(100))
    dob = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other'))
    address = db.Column(db.Text)
    abha_id = db.Column(db.String(20), index=True)
    blood_group = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    loyalty_points = db.Column(db.Integer, default=0)
    total_purchases = db.Column(db.Numeric(12, 2), default=0)
    loyalty_tier = db.Column(db.String(10), default='silver')
    referred_by_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales = db.relationship('Sale', backref='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')

    def __repr__(self):
        return f'<Patient {self.patient_code}: {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_code': self.patient_code,
            'full_name': self.full_name,
            'phone': self.phone,
            'loyalty_points': self.loyalty_points,
        }
