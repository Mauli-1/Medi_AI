"""Auth routes: login, logout, 2FA, forgot/reset password."""
import secrets
from datetime import datetime, timedelta

import pyotp
from flask import (render_template, redirect, url_for, flash, request,
                   session, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message

from . import bp
from .forms import LoginForm, TwoFactorForm, ForgotPasswordForm, ResetPasswordForm
from ...extensions import db, mail, limiter
from ...models.user import User
from ...models.audit_log import AuditLog

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 30
RESET_TOKEN_EXPIRY_HOURS = 2


# ── Login ──────────────────────────────────────────────────────────────────────

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per minute')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.username.data.strip()
        password   = form.password.data

        # Look up by username or email
        user = (User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first())

        if user is None:
            flash('Invalid credentials. Please try again.', 'danger')
            _log_failed_auth(identifier, request.remote_addr)
            return render_template('auth/login.html', form=form)

        if user.is_locked:
            minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            flash(
                f'Account locked due to too many failed attempts. '
                f'Try again in {minutes_left} minute(s).',
                'danger'
            )
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Your account is disabled. Contact the administrator.', 'danger')
            return render_template('auth/login.html', form=form)

        if not user.check_password(password):
            user.increment_failed_login(
                max_attempts=MAX_FAILED_ATTEMPTS,
                lockout_minutes=LOCKOUT_MINUTES
            )
            db.session.commit()
            remaining = MAX_FAILED_ATTEMPTS - user.failed_login_count
            if remaining > 0:
                flash(
                    f'Invalid credentials. {remaining} attempt(s) remaining before lockout.',
                    'danger'
                )
            else:
                flash(
                    f'Account locked for {LOCKOUT_MINUTES} minutes due to repeated failures.',
                    'danger'
                )
            return render_template('auth/login.html', form=form)

        # Valid password — check 2FA
        user.reset_failed_logins()
        db.session.commit()

        if user.totp_enabled:
            # Store user id in session for the 2FA step
            session['_2fa_user_id'] = user.id
            session['_2fa_remember'] = form.remember_me.data
            return redirect(url_for('auth.two_factor'))

        # Complete login
        _complete_login(user, form.remember_me.data)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    AuditLog.log(
        action='logout', module='auth',
        description=f'User {current_user.username} logged out.',
        user_id=current_user.id, ip_address=request.remote_addr,
    )
    db.session.commit()
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.login'))


# ── Two-Factor Auth ────────────────────────────────────────────────────────────

@bp.route('/two-factor', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def two_factor():
    user_id = session.get('_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if user is None:
        session.pop('_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    form = TwoFactorForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(form.token.data, valid_window=1):
            remember = session.pop('_2fa_remember', False)
            session.pop('_2fa_user_id', None)
            _complete_login(user, remember)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid code. Please try again.', 'danger')

    return render_template('auth/two_factor.html', form=form)


# ── Forgot / Reset Password ────────────────────────────────────────────────────

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per hour')
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        # Always show the same message to prevent user enumeration
        flash(
            'If that email is registered, a password reset link has been sent.',
            'info'
        )
        if user:
            token = secrets.token_urlsafe(48)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
            db.session.commit()
            _send_reset_email(user, token)

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    user = User.query.filter_by(reset_token=token).first()

    if user is None or user.reset_token_expiry < datetime.utcnow():
        flash('That reset link is invalid or has expired. Request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        user.reset_failed_logins()
        db.session.commit()
        flash('Password updated. You can now sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


# ── Private helpers ────────────────────────────────────────────────────────────

def _complete_login(user: User, remember: bool) -> None:
    login_user(user, remember=remember)
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.remote_addr
    AuditLog.log(
        action='login', module='auth',
        description=f'User {user.username} signed in.',
        user_id=user.id, ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:300],
        endpoint=request.endpoint,
    )
    db.session.commit()


def _log_failed_auth(identifier: str, ip: str) -> None:
    AuditLog.log(
        action='failed_login', module='auth',
        description=f'Failed login attempt for "{identifier}" from {ip}.',
        severity='warning', ip_address=ip,
    )
    db.session.commit()


def _send_reset_email(user: User, token: str) -> None:
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    try:
        msg = Message(
            subject='Reset your MSMS password',
            recipients=[user.email],
        )
        msg.body = (
            f'Hi {user.full_name},\n\n'
            f'Click the link below to reset your password. '
            f'This link expires in {RESET_TOKEN_EXPIRY_HOURS} hours.\n\n'
            f'{reset_url}\n\n'
            f'If you did not request this, ignore this email.\n\n'
            f'— Medical Store Management System'
        )
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error('Failed to send reset email to %s: %s', user.email, exc)
