"""Medicine Master CRUD routes."""
import csv
import io
import os
from datetime import date, datetime
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, current_app, send_file, abort,
)
from flask_login import login_required, current_user

from . import bp
from .forms import MedicineForm
from ...extensions import db
from ...models.medicine import Medicine, MedicineCategory, MedicineBatch
from ...models.business import Business
from ...models.branch import Branch
from ...models.sequence import Sequence
from ...services.barcode_service import generate_barcode, generate_qr, generate_medicine_label_pdf


def _get_business():
    return Business.query.first()


def _category_choices(business_id):
    cats = MedicineCategory.query.filter_by(business_id=business_id).order_by('name').all()
    choices = [(0, '-- Select Category --')]
    choices += [(c.id, c.name) for c in cats]
    return choices


# ── List ──────────────────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    business = _get_business()
    page = request.args.get('page', 1, type=int)
    per_page = 25
    q = request.args.get('q', '').strip()
    schedule = request.args.get('schedule', '').strip()
    category_id = request.args.get('category_id', 0, type=int)

    query = Medicine.query.filter_by(is_deleted=False)
    if business:
        query = query.filter_by(business_id=business.id)

    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Medicine.name.ilike(like),
                Medicine.generic_name.ilike(like),
                Medicine.barcode.ilike(like),
                Medicine.medicine_code.ilike(like),
            )
        )
    if schedule:
        query = query.filter_by(schedule_type=schedule)
    if category_id:
        query = query.filter_by(category_id=category_id)

    pagination = query.order_by(Medicine.name.asc()).paginate(page=page, per_page=per_page)
    medicines = pagination.items

    # Attach stock qty to each medicine (all branches)
    branch_id = request.args.get('branch_id', 0, type=int) or None
    for med in medicines:
        med._stock_qty = med.total_stock(branch_id=branch_id)

    categories = MedicineCategory.query.filter_by(
        business_id=business.id if business else 0
    ).order_by('name').all() if business else []

    branches = Branch.query.filter_by(
        business_id=business.id if business else 0, is_active=True
    ).all() if business else []

    return render_template(
        'medicines/list.html',
        title='Medicine Master',
        medicines=medicines,
        pagination=pagination,
        categories=categories,
        branches=branches,
        q=q,
        schedule=schedule,
        category_id=category_id,
        branch_id=branch_id or 0,
    )


# ── Create ────────────────────────────────────────────────────────────────────

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    business = _get_business()
    form = MedicineForm()
    form.category_id.choices = _category_choices(business.id if business else 0)

    if form.validate_on_submit():
        # Auto-generate medicine code
        med_code, _ = Sequence.next_number('medicine', prefix='MED-', pad=4)

        med = Medicine(
            business_id      = business.id if business else 1,
            medicine_code    = med_code,
            name             = form.name.data.strip(),
            generic_name     = form.generic_name.data.strip() if form.generic_name.data else None,
            brand_name       = form.brand_name.data.strip() if form.brand_name.data else None,
            salt_composition = form.salt_composition.data,
            category_id      = form.category_id.data if form.category_id.data else None,
            manufacturer     = form.manufacturer.data,
            hsn_code         = form.hsn_code.data,
            schedule_type    = form.schedule_type.data,
            gst_rate         = form.gst_rate.data,
            mrp              = form.mrp.data,
            purchase_rate    = form.purchase_rate.data,
            selling_rate     = form.selling_rate.data,
            unit             = form.unit.data or 'Strip',
            pack_size        = form.pack_size.data or 10,
            barcode          = form.barcode.data or None,
            rack_location    = form.rack_location.data,
            storage_condition = form.storage_condition.data,
            prescription_req  = form.prescription_req.data,
            temp_sensitive    = form.temp_sensitive.data,
            narcotic_flag     = form.narcotic_flag.data,
            returnable_flag   = form.returnable_flag.data,
            reorder_level    = form.reorder_level.data or 10,
            max_stock_level  = form.max_stock_level.data or 500,
        )

        db.session.add(med)
        db.session.flush()  # get med.id

        # Generate barcode if not provided
        if not med.barcode:
            try:
                generate_barcode(med.id, med.medicine_code)
            except Exception as e:
                current_app.logger.warning('Barcode generation failed: %s', e)

        # QR data
        qr_data = f'{med.medicine_code}|{med.name}|{med.generic_name or ""}|{float(med.mrp)}'
        med.qr_data = qr_data
        try:
            generate_qr(qr_data)
        except Exception as e:
            current_app.logger.warning('QR generation failed: %s', e)

        db.session.commit()
        flash(f'Medicine "{med.name}" created successfully (Code: {med_code}).', 'success')
        return redirect(url_for('medicines.detail', medicine_id=med.id))

    return render_template('medicines/create.html', title='Add Medicine', form=form)


# ── Edit ──────────────────────────────────────────────────────────────────────

@bp.route('/<int:medicine_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(medicine_id):
    business = _get_business()
    med = Medicine.query.filter_by(id=medicine_id, is_deleted=False).first_or_404()
    form = MedicineForm(obj=med)
    form.category_id.choices = _category_choices(business.id if business else 0)
    # gst_rate is Numeric; cast to string for SelectField
    if request.method == 'GET':
        form.gst_rate.data = str(float(med.gst_rate)) if med.gst_rate else '12.00'

    if form.validate_on_submit():
        med.name             = form.name.data.strip()
        med.generic_name     = form.generic_name.data.strip() if form.generic_name.data else None
        med.brand_name       = form.brand_name.data.strip() if form.brand_name.data else None
        med.salt_composition = form.salt_composition.data
        med.category_id      = form.category_id.data if form.category_id.data else None
        med.manufacturer     = form.manufacturer.data
        med.hsn_code         = form.hsn_code.data
        med.schedule_type    = form.schedule_type.data
        med.gst_rate         = form.gst_rate.data
        med.mrp              = form.mrp.data
        med.purchase_rate    = form.purchase_rate.data
        med.selling_rate     = form.selling_rate.data
        med.unit             = form.unit.data or 'Strip'
        med.pack_size        = form.pack_size.data or 10
        med.barcode          = form.barcode.data or med.barcode
        med.rack_location    = form.rack_location.data
        med.storage_condition = form.storage_condition.data
        med.prescription_req  = form.prescription_req.data
        med.temp_sensitive    = form.temp_sensitive.data
        med.narcotic_flag     = form.narcotic_flag.data
        med.returnable_flag   = form.returnable_flag.data
        med.reorder_level    = form.reorder_level.data or 10
        med.max_stock_level  = form.max_stock_level.data or 500
        med.updated_at       = datetime.utcnow()

        db.session.commit()
        flash(f'Medicine "{med.name}" updated successfully.', 'success')
        return redirect(url_for('medicines.detail', medicine_id=med.id))

    return render_template('medicines/edit.html', title='Edit Medicine', form=form, medicine=med)


# ── Detail ────────────────────────────────────────────────────────────────────

@bp.route('/<int:medicine_id>')
@login_required
def detail(medicine_id):
    med = Medicine.query.filter_by(id=medicine_id, is_deleted=False).first_or_404()
    batches = (MedicineBatch.query
               .filter_by(medicine_id=medicine_id)
               .order_by(MedicineBatch.expiry_date.asc())
               .all())

    # Build barcode image path
    barcode_path = None
    if med.medicine_code:
        try:
            rel = generate_barcode(med.id, med.medicine_code)
            if rel:
                barcode_path = rel
        except Exception:
            pass

    today = date.today()
    return render_template(
        'medicines/detail.html',
        title=med.name,
        medicine=med,
        batches=batches,
        barcode_path=barcode_path,
        today=today,
    )


# ── Soft delete ───────────────────────────────────────────────────────────────

@bp.route('/<int:medicine_id>/delete', methods=['POST'])
@login_required
def delete(medicine_id):
    med = Medicine.query.filter_by(id=medicine_id, is_deleted=False).first_or_404()
    med.is_deleted = True
    med.is_active  = False
    med.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Medicine "{med.name}" has been deleted.', 'warning')
    return redirect(url_for('medicines.index'))


# ── AJAX search (used by POS / sales module) ──────────────────────────────────

@bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    branch_id = request.args.get('branch_id', 0, type=int) or None
    business = _get_business()

    if not q or not business:
        return jsonify([])

    like = f'%{q}%'
    medicines = (Medicine.query
                 .filter_by(business_id=business.id, is_active=True, is_deleted=False)
                 .filter(db.or_(
                     Medicine.name.ilike(like),
                     Medicine.generic_name.ilike(like),
                     Medicine.barcode.ilike(like),
                     Medicine.medicine_code.ilike(like),
                 ))
                 .limit(20)
                 .all())

    results = []
    for med in medicines:
        batch_q = MedicineBatch.query.filter_by(
            medicine_id=med.id, is_expired=False, is_damaged=False
        )
        if branch_id:
            batch_q = batch_q.filter_by(branch_id=branch_id)
        batches = batch_q.order_by(MedicineBatch.expiry_date.asc()).all()

        results.append({
            'id':           med.id,
            'medicine_code': med.medicine_code,
            'name':         med.name,
            'generic':      med.generic_name or '',
            'schedule':     med.schedule_type,
            'mrp':          float(med.mrp),
            'prescription_req': med.prescription_req,
            'batches': [b.to_dict() for b in batches if b.available_qty > 0],
        })

    return jsonify(results)


# ── CSV Import ────────────────────────────────────────────────────────────────

@bp.route('/import-csv', methods=['POST'])
@login_required
def import_csv():
    """Import medicines from CSV file.

    Expected columns (case-insensitive):
    name, generic_name, brand_name, manufacturer, schedule_type,
    mrp, purchase_rate, selling_rate, gst_rate, unit, pack_size,
    reorder_level, hsn_code
    """
    business = _get_business()
    if not business:
        flash('Business not set up yet.', 'danger')
        return redirect(url_for('medicines.index'))

    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash('Please upload a valid CSV file.', 'danger')
        return redirect(url_for('medicines.index'))

    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))

    # Normalise header keys
    created_count = 0
    error_rows = []

    for i, row in enumerate(reader, start=2):
        row = {k.strip().lower().replace(' ', '_'): v.strip() for k, v in row.items()}
        name = row.get('name', '').strip()
        if not name:
            error_rows.append(f'Row {i}: missing name')
            continue

        try:
            mrp = float(row.get('mrp', 0) or 0)
            selling_rate = float(row.get('selling_rate', 0) or 0)
            purchase_rate = float(row.get('purchase_rate', 0) or 0)
            gst_rate = float(row.get('gst_rate', 12) or 12)
            pack_size = int(row.get('pack_size', 10) or 10)
            reorder_level = int(row.get('reorder_level', 10) or 10)
        except (ValueError, TypeError) as e:
            error_rows.append(f'Row {i}: numeric conversion error — {e}')
            continue

        schedule = row.get('schedule_type', 'OTC').upper()
        if schedule not in Medicine.SCHEDULE_TYPES:
            schedule = 'OTC'

        med_code, _ = Sequence.next_number('medicine', prefix='MED-', pad=4)
        med = Medicine(
            business_id   = business.id,
            medicine_code = med_code,
            name          = name,
            generic_name  = row.get('generic_name') or None,
            brand_name    = row.get('brand_name') or None,
            manufacturer  = row.get('manufacturer') or None,
            hsn_code      = row.get('hsn_code') or None,
            schedule_type = schedule,
            gst_rate      = gst_rate,
            mrp           = mrp,
            purchase_rate = purchase_rate,
            selling_rate  = selling_rate,
            unit          = row.get('unit', 'Strip') or 'Strip',
            pack_size     = pack_size,
            reorder_level = reorder_level,
        )
        db.session.add(med)
        created_count += 1

    db.session.commit()

    if error_rows:
        flash(f'Import completed: {created_count} medicines created. '
              f'{len(error_rows)} rows had errors: ' + '; '.join(error_rows[:5]), 'warning')
    else:
        flash(f'Import successful: {created_count} medicines created.', 'success')

    return redirect(url_for('medicines.index'))


# ── Print label PDF ───────────────────────────────────────────────────────────

@bp.route('/print-labels', methods=['POST'])
@login_required
def print_labels():
    """Generate and download label PDF for selected batch IDs."""
    batch_ids = request.form.getlist('batch_ids', type=int)
    if not batch_ids:
        flash('No batches selected for label printing.', 'warning')
        return redirect(request.referrer or url_for('medicines.index'))

    try:
        pdf_bytes = generate_medicine_label_pdf(batch_ids)
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'medicine_labels_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
        )
    except Exception as e:
        current_app.logger.error('Label PDF generation failed: %s', e)
        flash('Failed to generate label PDF. Please try again.', 'danger')
        return redirect(request.referrer or url_for('medicines.index'))


# ── Generic / Salt Search ──────────────────────────────────────────────────────

@bp.route('/generic-search')
@login_required
def generic_search():
    from ...services.ai_service import search_by_generic_name
    q = request.args.get('q', '').strip()
    results = search_by_generic_name(current_user.business_id, q) if q else []
    return render_template('medicines/generic_search.html', title='Generic / Salt Search', q=q, results=results)
