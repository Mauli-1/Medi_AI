"""Barcode Manager routes: generate/view barcode & QR, print labels."""
import io
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.medicine import Medicine, MedicineBatch
from app.services.barcode_service import generate_barcode, generate_qr, generate_medicine_label_pdf


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    q = request.args.get('q', '').strip()
    query = Medicine.query.filter_by(business_id=bid, is_deleted=False)
    if q:
        query = query.filter(db.or_(Medicine.name.ilike(f'%{q}%'), Medicine.medicine_code.ilike(f'%{q}%')))
    medicines = query.order_by(Medicine.name).limit(100).all()
    return render_template('barcode/index.html', title='Barcode Manager', medicines=medicines, q=q)


@bp.route('/generate/<int:medicine_id>', methods=['POST'])
@login_required
def generate(medicine_id):
    med = Medicine.query.filter_by(id=medicine_id, business_id=current_user.business_id).first_or_404()
    rel_path = generate_barcode(med.id, med.medicine_code)
    if rel_path:
        med.barcode = med.barcode or f"890{str(med.id).zfill(9)}"[:13]
        qr_path = generate_qr(f"{med.medicine_code}|{med.name}|{med.mrp}")
        med.qr_data = qr_path
        db.session.commit()
        flash(f'Barcode generated for {med.name}.', 'success')
    else:
        flash('Barcode generation failed — python-barcode library may not be installed.', 'danger')
    return redirect(url_for('barcode.index'))


@bp.route('/print-labels', methods=['POST'])
@login_required
def print_labels():
    batch_ids = request.form.getlist('batch_ids', type=int)
    if not batch_ids:
        flash('Select at least one batch to print labels for.', 'warning')
        return redirect(url_for('barcode.index'))
    pdf_bytes = generate_medicine_label_pdf(batch_ids)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                      download_name=f'labels_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf')


@bp.route('/medicine/<int:medicine_id>/batches')
@login_required
def medicine_batches(medicine_id):
    med = Medicine.query.filter_by(id=medicine_id, business_id=current_user.business_id).first_or_404()
    batches = MedicineBatch.query.filter_by(medicine_id=med.id).order_by(MedicineBatch.expiry_date).all()
    return render_template('barcode/batches.html', title=f'{med.name} — Batches', medicine=med, batches=batches)
