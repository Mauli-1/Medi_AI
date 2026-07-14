"""Prescriptions routes: list, upload, verify, dispense."""
import os
from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import bp
from app.extensions import db
from app.models.prescription import Prescription, PrescriptionItem
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.medicine import Medicine
from app.models.sequence import Sequence

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'pdf'}


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    status = request.args.get('status', '')
    query = Prescription.query.filter_by(business_id=bid)
    if status:
        query = query.filter_by(status=status)
    prescriptions = query.order_by(Prescription.rx_date.desc()).limit(100).all()
    return render_template('prescriptions/index.html', title='Prescriptions', prescriptions=prescriptions, status=status)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    bid = current_user.business_id
    patients = Patient.query.filter_by(business_id=bid, is_active=True).order_by(Patient.full_name).all()
    doctors = Doctor.query.filter_by(business_id=bid, is_active=True).order_by(Doctor.full_name).all()

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id') or None
        if not patient_id:
            flash('Select a patient.', 'danger')
            return render_template('prescriptions/upload.html', title='Upload Prescription', patients=patients, doctors=doctors)

        image_path = None
        file = request.files.get('file')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_EXT:
                flash('Only PNG, JPG, or PDF files are supported.', 'danger')
                return render_template('prescriptions/upload.html', title='Upload Prescription', patients=patients, doctors=doctors)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'prescriptions')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"rx_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(upload_dir, filename))
            image_path = os.path.join('uploads', 'prescriptions', filename)

        code, _ = Sequence.next_number(f'prescription-{bid}', prefix='RX-', pad=5)
        rx = Prescription(
            business_id=bid, branch_id=current_user.branch_id, prescription_code=code,
            patient_id=patient_id, doctor_id=doctor_id, rx_date=date.today(),
            image_path=image_path, status='pending',
            notes=request.form.get('notes', '').strip() or None,
        )
        db.session.add(rx)
        db.session.commit()
        flash(f'Prescription {code} uploaded.', 'success')
        return redirect(url_for('prescriptions.detail', rx_id=rx.id))

    return render_template('prescriptions/upload.html', title='Upload Prescription', patients=patients, doctors=doctors)


@bp.route('/<int:rx_id>')
@login_required
def detail(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    medicines = Medicine.query.filter_by(business_id=current_user.business_id, is_active=True).order_by(Medicine.name).all()
    return render_template('prescriptions/detail.html', title=rx.prescription_code, rx=rx, medicines=medicines)


@bp.route('/<int:rx_id>/add-item', methods=['POST'])
@login_required
def add_item(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    medicine_id = request.form.get('medicine_id') or None
    med = Medicine.query.get(medicine_id) if medicine_id else None
    db.session.add(PrescriptionItem(
        prescription_id=rx.id, medicine_id=medicine_id, generic_name=med.generic_name if med else request.form.get('generic_name'),
        dosage=request.form.get('dosage', '').strip() or None, duration=request.form.get('duration', '').strip() or None,
        quantity=request.form.get('quantity', type=int) or 1,
    ))
    db.session.commit()
    flash('Medicine added to prescription.', 'success')
    return redirect(url_for('prescriptions.detail', rx_id=rx.id))


@bp.route('/<int:rx_id>/verify', methods=['POST'])
@login_required
def verify(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    rx.is_verified = True
    rx.status = 'verified'
    rx.verified_by = current_user.id
    rx.verified_at = datetime.utcnow()
    db.session.commit()
    flash('Prescription verified.', 'success')
    return redirect(url_for('prescriptions.detail', rx_id=rx.id))


@bp.route('/<int:rx_id>/bill', methods=['POST'])
@login_required
def bill(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    return redirect(url_for('sales.billing', prescription_id=rx.id))
