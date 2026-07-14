"""E-Prescription routes — import, mock signature verification, and billing hand-off."""
import json
import xml.etree.ElementTree as ET
from datetime import date
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.prescription import Prescription, PrescriptionItem
from app.models.patient import Patient
from app.models.sequence import Sequence

ALLOWED_EXTENSIONS = {'xml', 'json', 'pdf'}


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    queue = (
        Prescription.query.filter(Prescription.business_id == bid, Prescription.eprescription_xml.isnot(None))
        .order_by(Prescription.created_at.desc())
        .all()
    )
    return render_template('eprescription/index.html', title='E-Prescription', queue=queue)


@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_rx():
    bid = current_user.business_id
    patients = Patient.query.filter_by(business_id=bid).order_by(Patient.full_name).all()
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        raw_text = request.form.get('raw_text', '').strip()
        uploaded = request.files.get('file')

        if uploaded and uploaded.filename:
            ext = uploaded.filename.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash('Only .xml, .json, or .pdf files are supported.', 'danger')
                return render_template('eprescription/import.html', title='Import E-Prescription', patients=patients)
            if ext == 'pdf':
                flash('PDF stored — text extraction requires the OCR pipeline (image-based bills only, not wired for PDF prescriptions yet). Please also paste the prescription text below if available.', 'warning')
                raw_text = raw_text or ''
            else:
                raw_text = uploaded.read().decode('utf-8', errors='ignore')

        if not patient_id or not raw_text:
            flash('Select a patient and provide the e-prescription content (paste or upload).', 'danger')
            return render_template('eprescription/import.html', title='Import E-Prescription', patients=patients)

        items = _parse_eprescription(raw_text)

        code, _ = Sequence.next_number(f'prescription-{bid}', prefix='RX-', pad=5)
        rx = Prescription(
            business_id=bid,
            branch_id=current_user.branch_id,
            prescription_code=code,
            patient_id=patient_id,
            rx_date=date.today(),
            eprescription_xml=raw_text,
            status='pending',
        )
        db.session.add(rx)
        db.session.flush()
        for it in items:
            db.session.add(PrescriptionItem(
                prescription_id=rx.id,
                generic_name=it.get('name'),
                dosage=it.get('dosage'),
                duration=it.get('duration'),
                quantity=it.get('quantity'),
            ))
        db.session.commit()
        flash(f'E-prescription {code} imported with {len(items)} medicine line(s).', 'success')
        return redirect(url_for('eprescription.index'))

    return render_template('eprescription/import.html', title='Import E-Prescription', patients=patients)


def _parse_eprescription(raw_text):
    items = []
    stripped = raw_text.strip()
    try:
        if stripped.startswith('{') or stripped.startswith('['):
            data = json.loads(stripped)
            meds = data.get('medicines') or data.get('items') or []
            for m in meds:
                items.append({'name': m.get('name') or m.get('generic_name'), 'dosage': m.get('dosage'),
                              'duration': m.get('duration'), 'quantity': m.get('quantity')})
        elif stripped.startswith('<'):
            root = ET.fromstring(stripped)
            for med_el in root.iter():
                tag = med_el.tag.lower()
                if tag.endswith('medicine') or tag.endswith('drug'):
                    items.append({
                        'name': med_el.findtext('name') or med_el.get('name'),
                        'dosage': med_el.findtext('dosage') or med_el.get('dosage'),
                        'duration': med_el.findtext('duration') or med_el.get('duration'),
                        'quantity': med_el.findtext('quantity') or med_el.get('quantity'),
                    })
    except Exception:
        pass
    return items


@bp.route('/<int:rx_id>/verify-signature')
@login_required
def verify_signature(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    raw = rx.eprescription_xml or ''
    has_signature = '<signature' in raw.lower() or '"signature"' in raw.lower()
    if has_signature:
        rx.is_verified = True
        rx.status = 'verified'
        db.session.commit()
        flash('Signature format present (mock verification — no real X.509/PKI validation performed).', 'success')
    else:
        flash('No signature block found in this e-prescription. Verification withheld.', 'warning')
    return redirect(url_for('eprescription.index'))


@bp.route('/<int:rx_id>/populate-bill', methods=['POST'])
@login_required
def populate_bill(rx_id):
    rx = Prescription.query.filter_by(id=rx_id, business_id=current_user.business_id).first_or_404()
    return redirect(url_for('sales.billing', prescription_id=rx.id))
