"""ABHA Integration routes — simulated ABDM sandbox (no live network access available here)."""
import re
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.patient import Patient
from app.models.audit_log import AuditLog

ABHA_PATTERN = re.compile(r'^\d{2}-\d{4}-\d{4}-\d{4}$|^\d{14}$')


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    with_abha = Patient.query.filter(Patient.business_id == bid, Patient.abha_id.isnot(None), Patient.abha_id != '').count()
    without_abha = Patient.query.filter(Patient.business_id == bid).filter(db.or_(Patient.abha_id.is_(None), Patient.abha_id == '')).all()
    return render_template('abha/index.html', title='ABHA Integration', with_abha=with_abha, without_abha=without_abha)


@bp.route('/verify/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def verify(patient_id):
    patient = Patient.query.filter_by(id=patient_id, business_id=current_user.business_id).first_or_404()
    if request.method == 'POST':
        abha_id = request.form.get('abha_id', '').strip()
        if not ABHA_PATTERN.match(abha_id):
            flash('Invalid ABHA ID format. Expected 14 digits (e.g. 12-3456-7890-1234).', 'danger')
            return render_template('abha/verify.html', title='Verify ABHA', patient=patient)
        patient.abha_id = abha_id
        db.session.commit()
        AuditLog.log(
            action='abha_verify', module='abha',
            description=f'ABHA ID {abha_id} linked to patient {patient.full_name} (format-validated, simulated verification)',
            record_type='patient', record_id=patient.id,
            user_id=current_user.id, ip_address=request.remote_addr,
        )
        db.session.commit()
        flash('ABHA ID verified (simulated — format check only, no live ABDM connection) and linked to patient.', 'success')
        return redirect(url_for('abha.index'))
    return render_template('abha/verify.html', title='Verify ABHA', patient=patient)


@bp.route('/qr-scan')
@login_required
def qr_scan():
    patients = Patient.query.filter_by(business_id=current_user.business_id).order_by(Patient.full_name).all()
    return render_template('abha/qr_scan.html', title='ABHA QR Scan', patients=patients)


@bp.route('/sync/<int:patient_id>', methods=['POST'])
@login_required
def sync(patient_id):
    patient = Patient.query.filter_by(id=patient_id, business_id=current_user.business_id).first_or_404()
    if not patient.abha_id:
        flash('Patient has no linked ABHA ID to sync.', 'danger')
        return redirect(url_for('abha.index'))
    AuditLog.log(
        action='abha_sync', module='abha',
        description=f'Simulated health-record sync for patient {patient.full_name} (ABHA {patient.abha_id}) at {datetime.utcnow().isoformat()}',
        record_type='patient', record_id=patient.id,
        user_id=current_user.id, ip_address=request.remote_addr,
    )
    db.session.commit()
    flash('Health record sync simulated (no live ABDM sandbox credentials configured).', 'info')
    return redirect(url_for('abha.index'))
