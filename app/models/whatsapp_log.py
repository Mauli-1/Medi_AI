from datetime import datetime
from ..extensions import db


class WhatsappLog(db.Model):
    __tablename__ = 'whatsapp_logs'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    to_number = db.Column(db.String(20), nullable=False)
    message_type = db.Column(db.Enum('invoice', 'payment_reminder', 'prescription_reminder', 'refill_reminder', 'promotional'), nullable=False)
    reference_type = db.Column(db.String(20))
    reference_id = db.Column(db.Integer)
    message_body = db.Column(db.Text)
    status = db.Column(db.Enum('queued', 'sent', 'failed'), default='queued')
    error_message = db.Column(db.String(255))
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<WhatsappLog {self.message_type} to={self.to_number} status={self.status}>'
