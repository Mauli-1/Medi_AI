from datetime import datetime
from ..extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    type = db.Column(db.Enum(
        'expiry', 'reorder', 'low_stock', 'dead_stock',
        'payment_due', 'license_expiry', 'system', 'whatsapp'
    ), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    reference_type = db.Column(db.String(20))
    reference_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False, index=True)
    priority = db.Column(db.Enum('low', 'medium', 'high', 'critical'), default='medium')
    sent_via = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<Notification {self.type}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
        }
