"""Business setup / edit forms."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, SelectField, BooleanField, TextAreaField,
                     SubmitField, IntegerField)
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

from ...utils.constants import INDIAN_STATES, GST_RATES


class BusinessStep1Form(FlaskForm):
    """Step 1: Basic information."""
    name       = StringField('Business Name',   validators=[DataRequired(), Length(max=200)])
    legal_name = StringField('Legal Name',       validators=[Optional(), Length(max=200)])
    short_name = StringField('Short Name / Alias', validators=[Optional(), Length(max=50)])
    email      = StringField('Email',            validators=[Optional(), Email(), Length(max=120)])
    phone      = StringField('Primary Phone',    validators=[DataRequired(), Length(max=15)])
    alt_phone  = StringField('Alternate Phone',  validators=[Optional(), Length(max=15)])
    website    = StringField('Website',          validators=[Optional(), Length(max=200)])
    tagline    = StringField('Tagline',          validators=[Optional(), Length(max=200)])
    submit     = SubmitField('Next: Address')


class BusinessStep2Form(FlaskForm):
    """Step 2: Address & regulatory."""
    address_line1    = StringField('Address Line 1', validators=[DataRequired(), Length(max=200)])
    address_line2    = StringField('Address Line 2', validators=[Optional(), Length(max=200)])
    city             = StringField('City',            validators=[DataRequired(), Length(max=100)])
    state            = SelectField('State / UT',      choices=[], validators=[DataRequired()])
    pincode          = StringField('PIN Code',        validators=[DataRequired(),
                                    Regexp(r'^\d{6}$', message='Enter a 6-digit PIN code.')])
    gstin            = StringField('GSTIN',           validators=[Optional(), Length(min=15, max=15)])
    pan              = StringField('PAN',             validators=[Optional(), Length(min=10, max=10)])
    drug_license_no  = StringField('Drug License (Retail)',   validators=[Optional(), Length(max=50)])
    drug_license_no2 = StringField('Drug License (Wholesale)', validators=[Optional(), Length(max=50)])
    fssai_no         = StringField('FSSAI License No.',       validators=[Optional(), Length(max=20)])
    submit           = SubmitField('Next: Banking')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state.choices = [('', '— Select State / UT —')] + [
            (code, name) for code, name in sorted(INDIAN_STATES.items(), key=lambda x: x[1])
        ]


class BusinessStep3Form(FlaskForm):
    """Step 3: Banking, branding & features."""
    bank_name       = StringField('Bank Name',       validators=[Optional(), Length(max=100)])
    bank_branch     = StringField('Branch Name',     validators=[Optional(), Length(max=100)])
    bank_account_no = StringField('Account Number',  validators=[Optional(), Length(max=20)])
    bank_ifsc       = StringField('IFSC Code',       validators=[Optional(), Length(max=11)])
    upi_id          = StringField('UPI ID',          validators=[Optional(), Length(max=50)])

    logo_file  = FileField('Business Logo', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')
    ])
    invoice_prefix  = StringField('Invoice Prefix', validators=[Optional(), Length(max=10)])
    invoice_terms   = TextAreaField('Invoice Terms', validators=[Optional()])
    invoice_footer  = TextAreaField('Invoice Footer', validators=[Optional()])

    enable_loyalty      = BooleanField('Enable Loyalty Points')
    enable_whatsapp     = BooleanField('Enable WhatsApp Notifications')
    enable_abha         = BooleanField('Enable ABHA Integration')
    enable_eprescription = BooleanField('Enable e-Prescription')
    enable_barcode      = BooleanField('Enable Barcode Generation')
    enable_sms          = BooleanField('Enable SMS Alerts')

    submit = SubmitField('Save & Finish Setup')


class BusinessEditForm(FlaskForm):
    """Full edit form (all fields on one page)."""
    name             = StringField('Business Name',   validators=[DataRequired(), Length(max=200)])
    legal_name       = StringField('Legal Name',       validators=[Optional(), Length(max=200)])
    short_name       = StringField('Short Name',       validators=[Optional(), Length(max=50)])
    email            = StringField('Email',            validators=[Optional(), Email()])
    phone            = StringField('Phone',            validators=[DataRequired(), Length(max=15)])
    alt_phone        = StringField('Alternate Phone',  validators=[Optional(), Length(max=15)])
    website          = StringField('Website',          validators=[Optional(), Length(max=200)])
    tagline          = StringField('Tagline',          validators=[Optional(), Length(max=200)])

    address_line1    = StringField('Address Line 1',   validators=[DataRequired()])
    address_line2    = StringField('Address Line 2',   validators=[Optional()])
    city             = StringField('City',             validators=[DataRequired()])
    state            = SelectField('State',            choices=[], validators=[DataRequired()])
    pincode          = StringField('PIN Code',         validators=[DataRequired()])

    gstin            = StringField('GSTIN',            validators=[Optional(), Length(max=15)])
    pan              = StringField('PAN',              validators=[Optional(), Length(max=10)])
    drug_license_no  = StringField('Drug License (Retail)',    validators=[Optional()])
    drug_license_no2 = StringField('Drug License (Wholesale)', validators=[Optional()])
    fssai_no         = StringField('FSSAI',            validators=[Optional()])

    bank_name        = StringField('Bank Name',        validators=[Optional()])
    bank_branch      = StringField('Bank Branch',      validators=[Optional()])
    bank_account_no  = StringField('Account Number',   validators=[Optional()])
    bank_ifsc        = StringField('IFSC',             validators=[Optional()])
    upi_id           = StringField('UPI ID',           validators=[Optional()])

    invoice_prefix   = StringField('Invoice Prefix',   validators=[Optional(), Length(max=10)])
    invoice_terms    = TextAreaField('Terms',           validators=[Optional()])
    invoice_footer   = TextAreaField('Footer',          validators=[Optional()])

    logo_file        = FileField('Logo', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')
    ])

    enable_loyalty       = BooleanField('Loyalty Points')
    enable_whatsapp      = BooleanField('WhatsApp Notifications')
    enable_abha          = BooleanField('ABHA Integration')
    enable_eprescription = BooleanField('e-Prescription')
    enable_barcode       = BooleanField('Barcode Generation')
    enable_sms           = BooleanField('SMS Alerts')

    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state.choices = [('', '— Select —')] + [
            (code, name) for code, name in sorted(INDIAN_STATES.items(), key=lambda x: x[1])
        ]
