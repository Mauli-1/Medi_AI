"""Sequence model — thread-safe, per-key auto-incrementing number generator.

Uses SELECT … FOR UPDATE to prevent race conditions in concurrent environments.
"""
from datetime import datetime
from sqlalchemy import text
from ..extensions import db


class Sequence(db.Model):
    __tablename__ = 'sequences'

    id            = db.Column(db.Integer, primary_key=True)
    key           = db.Column(db.String(50), unique=True, nullable=False, index=True)
    current_value = db.Column(db.Integer, default=0, nullable=False)
    prefix        = db.Column(db.String(10), default='')
    pad_length    = db.Column(db.Integer, default=6)
    reset_yearly  = db.Column(db.Boolean, default=False)
    last_reset_year = db.Column(db.Integer)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    @classmethod
    def next_number(cls, key: str, prefix: str = None,
                    pad: int = None, reset_yearly: bool = False) -> tuple:
        """Atomically increment and return the next sequence number.

        Uses SELECT … FOR UPDATE to serialise concurrent calls within a
        transaction, preventing duplicate numbers.

        Args:
            key:          Unique identifier for this sequence (e.g. 'invoice').
            prefix:       Override the stored prefix (optional).
            pad:          Override the stored pad length (optional).
            reset_yearly: Reset counter to 0 on new financial year start.

        Returns:
            (formatted_code: str, raw_number: int)
            e.g. ('INV000042', 42)
        """
        current_year = datetime.utcnow().year

        # Lock the row for this key
        seq = (cls.query
               .filter_by(key=key)
               .with_for_update()
               .first())

        if seq is None:
            # First time — create the sequence record
            seq = cls(
                key=key,
                current_value=0,
                prefix=prefix or '',
                pad_length=pad or 6,
                reset_yearly=reset_yearly,
                last_reset_year=current_year,
            )
            db.session.add(seq)

        # Yearly reset
        if seq.reset_yearly and seq.last_reset_year != current_year:
            seq.current_value = 0
            seq.last_reset_year = current_year

        seq.current_value += 1
        seq.updated_at = datetime.utcnow()

        # Allow call-time overrides
        used_prefix = prefix if prefix is not None else seq.prefix
        used_pad    = pad    if pad    is not None else seq.pad_length

        code = f'{used_prefix}{str(seq.current_value).zfill(used_pad)}'
        return code, seq.current_value

    @classmethod
    def peek(cls, key: str) -> int:
        """Return the current value without incrementing (no lock needed)."""
        seq = cls.query.filter_by(key=key).first()
        return seq.current_value if seq else 0

    def __repr__(self):
        return f'<Sequence key={self.key} current={self.current_value}>'
