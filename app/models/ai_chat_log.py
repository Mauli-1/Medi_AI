from datetime import datetime
from ..extensions import db


class AiChatLog(db.Model):
    __tablename__ = 'ai_chat_logs'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    intent = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AiChatLog intent={self.intent}>'
