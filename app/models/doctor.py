from datetime import datetime
from ..extensions import db


class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    registration_no = db.Column(db.String(50))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    clinic_name = db.Column(db.String(150))
    clinic_address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescriptions = db.relationship('Prescription', backref='doctor', lazy='dynamic')

    def __repr__(self):
        return f'<Doctor {self.doctor_code}: {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_code': self.doctor_code,
            'full_name': self.full_name,
            'specialization': self.specialization,
            'registration_no': self.registration_no,
        }
