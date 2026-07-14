from datetime import datetime
from ..extensions import db


class ComplianceRecord(db.Model):
    __tablename__ = 'compliance_records'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    record_type = db.Column(db.Enum('schedule_h', 'schedule_h1', 'narcotic', 'rx_log'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='SET NULL'), nullable=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='SET NULL'), nullable=True)
    quantity_dispensed = db.Column(db.Integer)
    dispensed_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    dispensed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    batch_number = db.Column(db.String(50))
    notes = db.Column(db.Text)

    medicine = db.relationship('Medicine', foreign_keys=[medicine_id])
    patient = db.relationship('Patient', foreign_keys=[patient_id])
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id])
    sale = db.relationship('Sale', foreign_keys=[sale_id])

    def __repr__(self):
        return f'<ComplianceRecord {self.record_type} sale={self.sale_id}>'
