"""User model with Flask-Login integration."""
from datetime import datetime
from flask_login import UserMixin
from ..extensions import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id                  = db.Column(db.Integer, primary_key=True)
    branch_id           = db.Column(db.Integer, db.ForeignKey('branches.id',
                                    ondelete='SET NULL'), nullable=True)

    # Identity
    username            = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email               = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name           = db.Column(db.String(150), nullable=False)
    phone               = db.Column(db.String(15))
    avatar_filename     = db.Column(db.String(200))

    # Auth
    password_hash       = db.Column(db.String(255), nullable=False)
    role                = db.Column(db.String(30), nullable=False, default='viewer')
    is_active           = db.Column(db.Boolean, default=True, nullable=False)
    is_verified         = db.Column(db.Boolean, default=False)

    # Two-factor auth (TOTP)
    totp_secret         = db.Column(db.String(32))
    totp_enabled        = db.Column(db.Boolean, default=False)

    # Account lockout
    failed_login_count  = db.Column(db.Integer, default=0)
    locked_until        = db.Column(db.DateTime)

    # Password reset
    reset_token         = db.Column(db.String(200), unique=True)
    reset_token_expiry  = db.Column(db.DateTime)

    # Email verification
    email_verify_token  = db.Column(db.String(200))

    # Session tracking
    last_login_at       = db.Column(db.DateTime)
    last_login_ip       = db.Column(db.String(45))
    last_active_at      = db.Column(db.DateTime)

    # Profile extras
    designation         = db.Column(db.String(100))
    qualification       = db.Column(db.String(200))
    drug_license_no     = db.Column(db.String(50))   # for pharmacists
    registration_no     = db.Column(db.String(50))   # for doctors

    # Preferences
    theme               = db.Column(db.String(20), default='light')
    language            = db.Column(db.String(10), default='en')

    # Timestamps
    created_at          = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow,
                                    onupdate=datetime.utcnow, nullable=False)

    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic',
                                 foreign_keys='AuditLog.user_id')

    @property
    def business_id(self):
        return self.branch.business_id if self.branch else None

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_locked(self) -> bool:
        """Return True if the account is currently locked due to failed logins."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def increment_failed_login(self, max_attempts: int = 5,
                               lockout_minutes: int = 30) -> None:
        """Increment failed login counter and lock the account if threshold reached."""
        from datetime import timedelta
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)

    def reset_failed_logins(self) -> None:
        """Clear failed login counter and lock after successful authentication."""
        self.failed_login_count = 0
        self.locked_until = None

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'

    def to_dict(self):
        return {
            'id':        self.id,
            'username':  self.username,
            'email':     self.email,
            'full_name': self.full_name,
            'role':      self.role,
            'is_active': self.is_active,
        }
