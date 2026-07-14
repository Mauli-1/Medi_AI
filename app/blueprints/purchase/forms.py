"""WTForms for Purchase and PurchaseOrder."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, DecimalField,
    IntegerField, HiddenField, SubmitField, DateField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


PAYMENT_MODE_CHOICES = [
    ('credit',        'Credit'),
    ('cash',          'Cash'),
    ('bank_transfer', 'Bank Transfer'),
    ('cheque',        'Cheque'),
    ('upi',           'UPI'),
]

PAYMENT_STATUS_CHOICES = [
    ('unpaid',  'Unpaid'),
    ('partial', 'Partial'),
    ('paid',    'Paid'),
]

PO_STATUS_CHOICES = [
    ('draft',     'Draft'),
    ('sent',      'Sent to Supplier'),
    ('partial',   'Partially Received'),
    ('received',  'Fully Received'),
    ('cancelled', 'Cancelled'),
]

GST_RATE_CHOICES = [
    ('0.00',  '0%'),
    ('5.00',  '5%'),
    ('12.00', '12%'),
    ('18.00', '18%'),
    ('28.00', '28%'),
]


class PurchaseForm(FlaskForm):
    supplier_id     = SelectField('Supplier *', coerce=int, validators=[DataRequired()])
    po_id           = SelectField('Against PO (optional)', coerce=int, validators=[Optional()])
    bill_date       = DateField('Bill Date *', validators=[DataRequired()])
    invoice_number  = StringField('Supplier Invoice No.', validators=[Optional(), Length(max=50)])
    invoice_date    = DateField('Invoice Date', validators=[Optional()])
    payment_mode    = SelectField('Payment Mode', choices=PAYMENT_MODE_CHOICES,
                                  default='credit', validators=[Optional()])
    payment_status  = SelectField('Payment Status', choices=PAYMENT_STATUS_CHOICES,
                                  default='unpaid', validators=[Optional()])
    paid_amount     = DecimalField('Paid Amount', places=2, default=0.00,
                                   validators=[Optional(), NumberRange(min=0)])
    notes           = TextAreaField('Notes', validators=[Optional()])
    ocr_bill        = FileField('Scan Bill (OCR)',
                                validators=[Optional(), FileAllowed(
                                    ['jpg', 'jpeg', 'png', 'tiff', 'pdf'],
                                    'Images only!')])
    submit          = SubmitField('Save Purchase')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.supplier_id.choices:
            self.supplier_id.choices = [(0, '-- Select Supplier --')]
        if not self.po_id.choices:
            self.po_id.choices = [(0, '-- None --')]


class PurchaseOrderForm(FlaskForm):
    supplier_id     = SelectField('Supplier *', coerce=int, validators=[DataRequired()])
    order_date      = DateField('Order Date *', validators=[DataRequired()])
    expected_date   = DateField('Expected Delivery Date', validators=[Optional()])
    status          = SelectField('Status', choices=PO_STATUS_CHOICES,
                                  default='draft', validators=[Optional()])
    notes           = TextAreaField('Notes', validators=[Optional()])
    submit          = SubmitField('Save Purchase Order')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.supplier_id.choices:
            self.supplier_id.choices = [(0, '-- Select Supplier --')]
