from datetime import datetime, date
from ..extensions import db


class ChartOfAccount(db.Model):
    __tablename__ = 'chart_of_accounts'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('asset', 'liability', 'equity', 'revenue', 'expense'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id', ondelete='SET NULL'), nullable=True)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    children = db.relationship('ChartOfAccount', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    entry_lines = db.relationship('JournalEntryLine', backref='account', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('business_id', 'code', name='uq_account_code'),)

    def __repr__(self):
        return f'<Account {self.code}: {self.name}>'


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False)
    entry_number = db.Column(db.String(25), unique=True, nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    reference_type = db.Column(db.String(20))
    reference_id = db.Column(db.Integer)
    narration = db.Column(db.Text)
    total_debit = db.Column(db.Numeric(12, 2), default=0)
    total_credit = db.Column(db.Numeric(12, 2), default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('JournalEntryLine', backref='entry', lazy='select', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<JournalEntry {self.entry_number}>'


class JournalEntryLine(db.Model):
    __tablename__ = 'journal_entry_lines'

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id', ondelete='CASCADE'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=False)
    debit = db.Column(db.Numeric(12, 2), default=0)
    credit = db.Column(db.Numeric(12, 2), default=0)

    def __repr__(self):
        return f'<JournalLine entry={self.entry_id} Dr={self.debit} Cr={self.credit}>'
