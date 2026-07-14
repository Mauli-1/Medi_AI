"""Doctors CRUD routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.doctor import Doctor
from app.models.sequence import Sequence
from app.models.prescription import Prescription


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Doctor.query.filter_by(business_id=bid)
    if q:
        query = query.filter(db.or_(Doctor.full_name.ilike(f'%{q}%'), Doctor.registration_no.ilike(f'%{q}%')))
    doctors = query.order_by(Doctor.full_name).paginate(page=page, per_page=25)
    return render_template('doctors/index.html', title='Doctors', doctors=doctors, q=q)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    bid = current_user.business_id
    if request.method == 'POST':
        name = request.form.get('full_name', '').strip()
        if not name:
            flash('Doctor name is required.', 'danger')
            return render_template('doctors/form.html', title='Add Doctor', doctor=None)
        code, _ = Sequence.next_number(f'doctor-{bid}', prefix='DOC-', pad=5)
        d = Doctor(
            business_id=bid, doctor_code=code, full_name=name,
            specialization=request.form.get('specialization', '').strip() or None,
            qualification=request.form.get('qualification', '').strip() or None,
            registration_no=request.form.get('registration_no', '').strip() or None,
            phone=request.form.get('phone', '').strip() or None, email=request.form.get('email', '').strip() or None,
            clinic_name=request.form.get('clinic_name', '').strip() or None,
            clinic_address=request.form.get('clinic_address', '').strip() or None, is_active=True,
        )
        db.session.add(d)
        db.session.commit()
        flash(f'Doctor {d.doctor_code} added.', 'success')
        return redirect(url_for('doctors.index'))
    return render_template('doctors/form.html', title='Add Doctor', doctor=None)


@bp.route('/<int:doctor_id>')
@login_required
def detail(doctor_id):
    doctor = Doctor.query.filter_by(id=doctor_id, business_id=current_user.business_id).first_or_404()
    prescriptions = Prescription.query.filter_by(doctor_id=doctor.id).order_by(Prescription.rx_date.desc()).limit(20).all()
    return render_template('doctors/detail.html', title=doctor.full_name, doctor=doctor, prescriptions=prescriptions)


@bp.route('/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(doctor_id):
    doctor = Doctor.query.filter_by(id=doctor_id, business_id=current_user.business_id).first_or_404()
    if request.method == 'POST':
        doctor.full_name = request.form.get('full_name', '').strip()
        doctor.specialization = request.form.get('specialization', '').strip() or None
        doctor.qualification = request.form.get('qualification', '').strip() or None
        doctor.registration_no = request.form.get('registration_no', '').strip() or None
        doctor.phone = request.form.get('phone', '').strip() or None
        doctor.email = request.form.get('email', '').strip() or None
        doctor.clinic_name = request.form.get('clinic_name', '').strip() or None
        doctor.clinic_address = request.form.get('clinic_address', '').strip() or None
        doctor.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Doctor updated.', 'success')
        return redirect(url_for('doctors.detail', doctor_id=doctor.id))
    return render_template('doctors/form.html', title='Edit Doctor', doctor=doctor)


@bp.route('/<int:doctor_id>/delete', methods=['POST'])
@login_required
def delete(doctor_id):
    doctor = Doctor.query.filter_by(id=doctor_id, business_id=current_user.business_id).first_or_404()
    doctor.is_active = False
    db.session.commit()
    flash('Doctor deactivated.', 'info')
    return redirect(url_for('doctors.index'))
