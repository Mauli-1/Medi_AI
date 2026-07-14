"""Security routes: audit log viewer, 2FA setup, on-demand backup."""
import base64
import io
import subprocess
import os
from datetime import datetime

import pyotp
import qrcode
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.audit_log import AuditLog


@bp.route('/')
@login_required
def index():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template('security/index.html', title='Security', logs=logs)


@bp.route('/audit-logs')
@login_required
def audit_logs():
    query = AuditLog.query
    module = request.args.get('module', '')
    severity = request.args.get('severity', '')
    action = request.args.get('action', '')
    if module:
        query = query.filter_by(module=module)
    if severity:
        query = query.filter_by(severity=severity)
    if action:
        query = query.filter(AuditLog.action.ilike(f'%{action}%'))
    page = request.args.get('page', 1, type=int)
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('security/audit_logs.html', title='Audit Logs', logs=logs,
                            module=module, severity=severity, action=action)


@bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def twofa_setup():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        secret = request.form.get('secret', '')
        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=1):
            current_user.totp_secret = secret
            current_user.totp_enabled = True
            db.session.commit()
            AuditLog.log(action='2fa_enabled', module='security',
                          description=f'User {current_user.username} enabled 2FA.',
                          user_id=current_user.id, ip_address=request.remote_addr)
            db.session.commit()
            flash('Two-factor authentication enabled.', 'success')
            return redirect(url_for('security.index'))
        flash('Invalid code. Please scan the QR again and try the current code.', 'danger')

    if current_user.totp_enabled:
        return render_template('security/twofa_setup.html', title='2FA Setup', already_enabled=True)

    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name='MSMS')
    qr_img = qrcode.make(uri)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return render_template('security/twofa_setup.html', title='2FA Setup', secret=secret, qr_b64=qr_b64, already_enabled=False)


@bp.route('/2fa/disable', methods=['POST'])
@login_required
def twofa_disable():
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.session.commit()
    AuditLog.log(action='2fa_disabled', module='security',
                 description=f'User {current_user.username} disabled 2FA.',
                 user_id=current_user.id, ip_address=request.remote_addr)
    db.session.commit()
    flash('Two-factor authentication disabled.', 'info')
    return redirect(url_for('security.index'))


@bp.route('/backup/run', methods=['POST'])
@login_required
def backup_run():
    backups_dir = os.path.join(current_app.root_path, '..', 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(backups_dir, f'msms_backup_{timestamp}.sql')

    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    try:
        import re
        m = re.match(r'mysql\+pymysql://([^:]+):([^@]*)@([^/:]+)(?::(\d+))?/(\w+)', db_uri)
        if not m:
            raise RuntimeError('Could not parse database URI for backup.')
        user, pwd, host, port, dbname = m.groups()
        cmd = ['mysqldump', '-h', host, '-u', user, f'-p{pwd}', dbname]
        if port:
            cmd[2:2] = ['-P', port]
        with open(filename, 'wb') as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, timeout=60)
        AuditLog.log(action='backup_run', module='security',
                     description=f'Manual backup created: {os.path.basename(filename)}',
                     user_id=current_user.id, ip_address=request.remote_addr)
        db.session.commit()
        flash(f'Backup created: {os.path.basename(filename)}', 'success')
    except FileNotFoundError:
        flash('mysqldump not available in this environment.', 'warning')
    except Exception as exc:
        flash(f'Backup failed: {exc}', 'danger')
    return redirect(url_for('security.index'))
