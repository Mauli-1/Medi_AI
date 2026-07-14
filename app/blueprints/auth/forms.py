"""Auth forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp


class LoginForm(FlaskForm):
    username = StringField(
        'Username or Email',
        validators=[DataRequired(message='Username or email is required.'),
                    Length(max=120)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required.')]
    )
    remember_me = BooleanField('Stay signed in')
    submit = SubmitField('Sign In')


class TwoFactorForm(FlaskForm):
    token = StringField(
        'Authenticator Code',
        validators=[
            DataRequired(message='Enter the 6-digit code from your authenticator app.'),
            Length(min=6, max=8),
            Regexp(r'^\d+$', message='Code must contain only digits.'),
        ]
    )
    submit = SubmitField('Verify')


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'Registered Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
            Length(max=120),
        ]
    )
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters.'),
        ]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ]
    )
    submit = SubmitField('Set New Password')
