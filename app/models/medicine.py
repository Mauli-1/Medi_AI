"""Medicine models: MedicineCategory, Medicine, MedicineBatch."""
from datetime import datetime, date
from ..extensions import db


class MedicineCategory(db.Model):
    __tablename__ = 'medicine_categories'

    id          = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    name        = db.Column(db.String(100), nullable=False)
    parent_id   = db.Column(db.Integer, db.ForeignKey('medicine_categories.id',
                            ondelete='SET NULL'), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Self-referential relationship
    children = db.relationship('MedicineCategory', backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')
    medicines = db.relationship('Medicine', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<MedicineCategory {self.name}>'

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'parent_id': self.parent_id}


class Medicine(db.Model):
    __tablename__ = 'medicines'

    id              = db.Column(db.Integer, primary_key=True)
    business_id     = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'),
                                nullable=False, index=True)

    # Identification
    medicine_code   = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name            = db.Column(db.String(200), nullable=False, index=True)
    generic_name    = db.Column(db.String(200), index=True)
    brand_name      = db.Column(db.String(200))
    salt_composition = db.Column(db.Text)

    # Classification
    category_id     = db.Column(db.Integer, db.ForeignKey('medicine_categories.id',
                                ondelete='SET NULL'), nullable=True)
    manufacturer    = db.Column(db.String(200))
    hsn_code        = db.Column(db.String(20))

    # Schedule type: H, H1, X, G, OTC, P
    SCHEDULE_TYPES = ['H', 'H1', 'X', 'G', 'OTC', 'P']
    schedule_type   = db.Column(db.String(5), default='OTC', nullable=False)

    # Pricing
    gst_rate        = db.Column(db.Numeric(5, 2), default=12.00)
    mrp             = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    purchase_rate   = db.Column(db.Numeric(10, 2), default=0.00)
    selling_rate    = db.Column(db.Numeric(10, 2), default=0.00)

    # Packaging
    unit            = db.Column(db.String(20), default='Strip')
    pack_size       = db.Column(db.Integer, default=10)

    # Barcodes
    barcode         = db.Column(db.String(50), unique=True, nullable=True, index=True)
    qr_data         = db.Column(db.Text)

    # Storage
    rack_location   = db.Column(db.String(50))
    STORAGE_CONDITIONS = ['room_temp', 'refrigerated', 'cold_chain']
    storage_condition = db.Column(db.String(20), default='room_temp')

    # Flags
    prescription_req = db.Column(db.Boolean, default=False)
    temp_sensitive   = db.Column(db.Boolean, default=False)
    narcotic_flag    = db.Column(db.Boolean, default=False)
    returnable_flag  = db.Column(db.Boolean, default=True)

    # Inventory control
    reorder_level    = db.Column(db.Integer, default=10)
    max_stock_level  = db.Column(db.Integer, default=500)

    # Status
    is_active        = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted       = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow, nullable=False)

    # Relationships
    batches = db.relationship('MedicineBatch', backref='medicine', lazy='dynamic',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Medicine {self.medicine_code}: {self.name}>'

    def total_stock(self, branch_id=None):
        """Return total available_qty across all batches (optionally for one branch)."""
        q = self.batches.filter_by(is_expired=False, is_damaged=False)
        if branch_id:
            q = q.filter_by(branch_id=branch_id)
        return sum(b.available_qty for b in q.all())

    def to_dict(self):
        return {
            'id':           self.id,
            'medicine_code': self.medicine_code,
            'name':         self.name,
            'generic_name': self.generic_name,
            'brand_name':   self.brand_name,
            'schedule_type': self.schedule_type,
            'mrp':          float(self.mrp),
            'selling_rate': float(self.selling_rate),
            'barcode':      self.barcode,
            'is_active':    self.is_active,
        }


class MedicineBatch(db.Model):
    __tablename__ = 'medicine_batches'

    id               = db.Column(db.Integer, primary_key=True)
    medicine_id      = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'),
                                 nullable=False, index=True)
    branch_id        = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'),
                                 nullable=False, index=True)

    batch_number     = db.Column(db.String(50), nullable=False)
    mfg_date         = db.Column(db.Date, nullable=True)
    expiry_date      = db.Column(db.Date, nullable=False)

    quantity         = db.Column(db.Integer, default=0, nullable=False)
    reserved_qty     = db.Column(db.Integer, default=0, nullable=False)

    purchase_rate    = db.Column(db.Numeric(10, 2), default=0.00)
    mrp              = db.Column(db.Numeric(10, 2), default=0.00)
    selling_rate     = db.Column(db.Numeric(10, 2), default=0.00)

    rack_location    = db.Column(db.String(50))
    purchase_item_id = db.Column(db.Integer, nullable=True)  # FK to purchase item when purchase module exists

    is_expired       = db.Column(db.Boolean, default=False, nullable=False)
    is_damaged       = db.Column(db.Boolean, default=False, nullable=False)

    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow, nullable=False)

    # Branch relationship (backref declared here; branch already has no backref to batches)
    branch = db.relationship('Branch', foreign_keys=[branch_id])

    @property
    def available_qty(self):
        """Available quantity = total - reserved."""
        return max(0, self.quantity - self.reserved_qty)

    def check_expired(self):
        """Mark as expired if expiry_date has passed."""
        if self.expiry_date and self.expiry_date < date.today():
            self.is_expired = True
        return self.is_expired

    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days

    def __repr__(self):
        return f'<MedicineBatch {self.batch_number} med={self.medicine_id}>'

    def to_dict(self):
        return {
            'id':           self.id,
            'batch_number': self.batch_number,
            'expiry_date':  self.expiry_date.isoformat() if self.expiry_date else None,
            'available_qty': self.available_qty,
            'selling_rate': float(self.selling_rate),
            'mrp':          float(self.mrp),
        }
