"""AuditLog model — immutable record of all significant user actions."""
from datetime import datetime
from ..extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
                              nullable=True, index=True)

    # What happened
    action        = db.Column(db.String(50), nullable=False, index=True)
    module        = db.Column(db.String(50), nullable=False, index=True)
    description   = db.Column(db.Text)

    # Which record was affected
    record_type   = db.Column(db.String(50))
    record_id     = db.Column(db.Integer)

    # Snapshot data (JSON)
    old_values    = db.Column(db.JSON)
    new_values    = db.Column(db.JSON)

    # Request context
    ip_address    = db.Column(db.String(45))
    user_agent    = db.Column(db.String(300))
    endpoint      = db.Column(db.String(200))

    # Severity / category
    severity      = db.Column(db.String(20), default='info')   # info / warning / critical

    # Timestamp (only created, never updated — audit logs are immutable)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow,
                              nullable=False, index=True)

    @classmethod
    def log(cls, action: str, module: str, description: str = None,
            record_type: str = None, record_id: int = None,
            old_values: dict = None, new_values: dict = None,
            severity: str = 'info', user_id: int = None,
            ip_address: str = None, user_agent: str = None,
            endpoint: str = None):
        """Convenience factory method to create and add an audit entry."""
        from ..extensions import db as _db
        entry = cls(
            user_id=user_id,
            action=action,
            module=module,
            description=description,
            record_type=record_type,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
        )
        _db.session.add(entry)
        return entry

    def __repr__(self):
        return (f'<AuditLog id={self.id} action={self.action} '
                f'module={self.module} user={self.user_id}>')
