"""WTForms for Supplier CRUD."""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, DecimalField,
    IntegerField, BooleanField, SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange


PAYMENT_TERMS_CHOICES = [
    (0,   'Immediate (0 days)'),
    (7,   '7 days'),
    (15,  '15 days'),
    (30,  '30 days'),
    (45,  '45 days'),
    (60,  '60 days'),
    (90,  '90 days'),
]

INDIAN_STATES = [
    ('', '-- Select State --'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Chandigarh', 'Chandigarh'),
    ('Puducherry', 'Puducherry'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Lakshadweep', 'Lakshadweep'),
]


class SupplierForm(FlaskForm):
    # Basic
    name            = StringField('Company / Supplier Name *',
                                  validators=[DataRequired(), Length(max=200)])
    contact_person  = StringField('Contact Person', validators=[Optional(), Length(max=150)])
    phone           = StringField('Phone', validators=[Optional(), Length(max=15)])
    email           = StringField('Email', validators=[Optional(), Email(), Length(max=120)])

    # Regulatory
    gst_number      = StringField('GSTIN', validators=[Optional(), Length(max=15)])
    drug_license_no = StringField('Drug License No.', validators=[Optional(), Length(max=50)])

    # Address
    address         = TextAreaField('Address', validators=[Optional()])
    city            = StringField('City', validators=[Optional(), Length(max=100)])
    state           = SelectField('State', choices=INDIAN_STATES, validators=[Optional()])

    # Financial
    payment_terms   = SelectField('Payment Terms (days)', coerce=int,
                                  choices=PAYMENT_TERMS_CHOICES,
                                  validators=[Optional()], default=30)
    credit_limit    = DecimalField('Credit Limit (Rs.)', places=2, default=0.00,
                                   validators=[Optional(), NumberRange(min=0)])

    is_active       = BooleanField('Active', default=True)

    submit = SubmitField('Save Supplier')
