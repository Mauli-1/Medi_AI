"""WTForms for Medicine CRUD."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, DecimalField,
    IntegerField, BooleanField, HiddenField, SubmitField,
)
from wtforms.validators import (
    DataRequired, Optional, Length, NumberRange, ValidationError,
)


SCHEDULE_CHOICES = [
    ('OTC', 'OTC – Over the Counter'),
    ('G',   'Schedule G'),
    ('H',   'Schedule H'),
    ('H1',  'Schedule H1'),
    ('X',   'Schedule X (Narcotic)'),
    ('P',   'Schedule P'),
]

STORAGE_CHOICES = [
    ('room_temp',    'Room Temperature'),
    ('refrigerated', 'Refrigerated (2–8°C)'),
    ('cold_chain',   'Cold Chain (<0°C)'),
]

GST_CHOICES = [
    ('0.00',  '0%'),
    ('5.00',  '5%'),
    ('12.00', '12%'),
    ('18.00', '18%'),
    ('28.00', '28%'),
]


class MedicineForm(FlaskForm):
    # ── Basic Info ────────────────────────────────────────────────────────────
    name             = StringField('Medicine Name *', validators=[DataRequired(), Length(max=200)])
    generic_name     = StringField('Generic Name', validators=[Optional(), Length(max=200)])
    brand_name       = StringField('Brand Name', validators=[Optional(), Length(max=200)])
    salt_composition = TextAreaField('Salt Composition', validators=[Optional()])

    # ── Classification ────────────────────────────────────────────────────────
    category_id      = SelectField('Category', coerce=int, validators=[Optional()])
    manufacturer     = StringField('Manufacturer', validators=[Optional(), Length(max=200)])
    hsn_code         = StringField('HSN Code', validators=[Optional(), Length(max=20)])
    schedule_type    = SelectField('Schedule Type *', choices=SCHEDULE_CHOICES,
                                   validators=[DataRequired()])

    # ── Pricing ───────────────────────────────────────────────────────────────
    gst_rate         = SelectField('GST Rate *', choices=GST_CHOICES, default='12.00',
                                   validators=[DataRequired()])
    mrp              = DecimalField('MRP (Rs.) *', places=2, validators=[
                                    DataRequired(), NumberRange(min=0)])
    purchase_rate    = DecimalField('Purchase Rate (Rs.)', places=2, default=0.00,
                                    validators=[Optional(), NumberRange(min=0)])
    selling_rate     = DecimalField('Selling Rate (Rs.) *', places=2, validators=[
                                    DataRequired(), NumberRange(min=0)])

    # ── Packaging ────────────────────────────────────────────────────────────
    unit             = StringField('Unit', default='Strip',
                                   validators=[Optional(), Length(max=20)])
    pack_size        = IntegerField('Pack Size', default=10,
                                    validators=[Optional(), NumberRange(min=1)])

    # ── Barcode ───────────────────────────────────────────────────────────────
    barcode          = StringField('Barcode', validators=[Optional(), Length(max=50)])

    # ── Storage ───────────────────────────────────────────────────────────────
    rack_location     = StringField('Rack Location', validators=[Optional(), Length(max=50)])
    storage_condition = SelectField('Storage Condition', choices=STORAGE_CHOICES,
                                    default='room_temp', validators=[Optional()])

    # ── Flags ─────────────────────────────────────────────────────────────────
    prescription_req  = BooleanField('Prescription Required')
    temp_sensitive    = BooleanField('Temperature Sensitive')
    narcotic_flag     = BooleanField('Narcotic / Controlled Substance')
    returnable_flag   = BooleanField('Returnable', default=True)

    # ── Inventory Control ─────────────────────────────────────────────────────
    reorder_level    = IntegerField('Reorder Level', default=10,
                                    validators=[Optional(), NumberRange(min=0)])
    max_stock_level  = IntegerField('Max Stock Level', default=500,
                                    validators=[Optional(), NumberRange(min=0)])

    submit = SubmitField('Save Medicine')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Category choices populated dynamically in route
        if not self.category_id.choices:
            self.category_id.choices = [(0, '-- Select Category --')]

    def validate_selling_rate(self, field):
        """Selling rate must not exceed MRP."""
        if field.data is not None and self.mrp.data is not None:
            if field.data > self.mrp.data:
                raise ValidationError('Selling rate cannot exceed MRP.')

    def validate_purchase_rate(self, field):
        """Purchase rate must not exceed MRP."""
        if field.data is not None and self.mrp.data is not None:
            if field.data > self.mrp.data:
                raise ValidationError('Purchase rate cannot exceed MRP.')
