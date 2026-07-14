from datetime import datetime, date
from ..extensions import db


class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    prescription_code = db.Column(db.String(25), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='RESTRICT'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    rx_date = db.Column(db.Date, nullable=False, default=date.today)
    image_path = db.Column(db.String(300))
    eprescription_xml = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    verified_at = db.Column(db.DateTime)
    validity_days = db.Column(db.Integer, default=30)
    status = db.Column(db.Enum('pending', 'verified', 'dispensed', 'expired'), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('PrescriptionItem', backref='prescription', lazy='select', cascade='all, delete-orphan')
    verifier = db.relationship('User', foreign_keys=[verified_by])

    def __repr__(self):
        return f'<Prescription {self.prescription_code}>'


class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='SET NULL'), nullable=True)
    generic_name = db.Column(db.String(150))
    dosage = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    dispensed_qty = db.Column(db.Integer, default=0)

    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])

    def __repr__(self):
        return f'<PrescriptionItem rx={self.prescription_id}>'
