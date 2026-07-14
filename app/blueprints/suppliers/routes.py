"""Suppliers blueprint routes."""
from datetime import datetime, date, timedelta
from decimal import Decimal

from flask import (
    render_template, redirect, url_for, flash,
    request, jsonify, abort,
)
from flask_login import login_required, current_user

from . import bp
from .forms import SupplierForm
from ...extensions import db
from ...models.supplier import Supplier
from ...models.sequence import Sequence


def _get_business_id():
    """Return the business_id for the current user's context."""
    try:
        from ...models.business import Business
        biz = Business.query.first()
        return biz.id if biz else 1
    except Exception:
        return 1


# ── List ──────────────────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    business_id = _get_business_id()
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Supplier.query.filter_by(business_id=business_id, is_deleted=False)
    if q:
        query = query.filter(
            db.or_(
                Supplier.name.ilike(f'%{q}%'),
                Supplier.supplier_code.ilike(f'%{q}%'),
                Supplier.contact_person.ilike(f'%{q}%'),
                Supplier.phone.ilike(f'%{q}%'),
            )
        )

    suppliers = query.order_by(Supplier.name).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        'suppliers/list.html',
        suppliers=suppliers,
        q=q,
        title='Suppliers',
    )


# ── Create ────────────────────────────────────────────────────────────────────

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = SupplierForm()
    if form.validate_on_submit():
        business_id = _get_business_id()
        code, _ = Sequence.next_number(
            key='supplier',
            prefix='SUP-',
            pad=4,
        )
        supplier = Supplier(
            business_id=business_id,
            supplier_code=code,
            name=form.name.data.strip(),
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            gst_number=form.gst_number.data,
            drug_license_no=form.drug_license_no.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            payment_terms=form.payment_terms.data,
            credit_limit=form.credit_limit.data or Decimal('0.00'),
            is_active=form.is_active.data,
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'Supplier {supplier.supplier_code} created successfully.', 'success')
        return redirect(url_for('suppliers.index'))

    return render_template('suppliers/create.html', form=form, title='Add Supplier')


# ── Edit ──────────────────────────────────────────────────────────────────────

@bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(supplier_id):
    business_id = _get_business_id()
    supplier = Supplier.query.filter_by(
        id=supplier_id, business_id=business_id, is_deleted=False
    ).first_or_404()

    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        supplier.name           = form.name.data.strip()
        supplier.contact_person = form.contact_person.data
        supplier.phone          = form.phone.data
        supplier.email          = form.email.data
        supplier.gst_number     = form.gst_number.data
        supplier.drug_license_no = form.drug_license_no.data
        supplier.address        = form.address.data
        supplier.city           = form.city.data
        supplier.state          = form.state.data
        supplier.payment_terms  = form.payment_terms.data
        supplier.credit_limit   = form.credit_limit.data or Decimal('0.00')
        supplier.is_active      = form.is_active.data
        db.session.commit()
        flash('Supplier updated successfully.', 'success')
        return redirect(url_for('suppliers.index'))

    return render_template('suppliers/edit.html', form=form, supplier=supplier, title='Edit Supplier')


# ── Soft Delete ───────────────────────────────────────────────────────────────

@bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete(supplier_id):
    business_id = _get_business_id()
    supplier = Supplier.query.filter_by(
        id=supplier_id, business_id=business_id, is_deleted=False
    ).first_or_404()

    supplier.is_deleted = True
    supplier.is_active  = False
    db.session.commit()
    flash(f'Supplier "{supplier.name}" deleted.', 'warning')
    return redirect(url_for('suppliers.index'))


# ── Ledger ────────────────────────────────────────────────────────────────────

@bp.route('/<int:supplier_id>/ledger')
@login_required
def ledger(supplier_id):
    business_id = _get_business_id()
    supplier = Supplier.query.filter_by(
        id=supplier_id, business_id=business_id, is_deleted=False
    ).first_or_404()

    from ...models.purchase import Purchase
    purchases = (
        Purchase.query
        .filter_by(supplier_id=supplier_id, business_id=business_id)
        .order_by(Purchase.bill_date.desc())
        .all()
    )

    # Build ledger entries
    entries = []
    running_balance = Decimal('0.00')
    for p in reversed(purchases):
        running_balance += p.total_amount
        entries.append({
            'date':         p.bill_date,
            'voucher_type': 'Purchase',
            'reference':    p.bill_number,
            'invoice':      p.invoice_number or '',
            'debit':        float(p.total_amount),
            'credit':       float(p.paid_amount),
            'balance':      float(running_balance - p.paid_amount),
        })
        running_balance -= p.paid_amount

    entries.reverse()

    return render_template(
        'suppliers/ledger.html',
        supplier=supplier,
        entries=entries,
        title=f'Ledger – {supplier.name}',
    )


# ── Aging Report ──────────────────────────────────────────────────────────────

@bp.route('/<int:supplier_id>/aging')
@login_required
def aging(supplier_id):
    business_id = _get_business_id()
    supplier = Supplier.query.filter_by(
        id=supplier_id, business_id=business_id, is_deleted=False
    ).first_or_404()

    from ...models.purchase import Purchase
    today = date.today()

    unpaid = (
        Purchase.query
        .filter(
            Purchase.supplier_id == supplier_id,
            Purchase.business_id == business_id,
            Purchase.payment_status.in_(['unpaid', 'partial']),
        )
        .order_by(Purchase.bill_date)
        .all()
    )

    buckets = {'0_30': [], '31_60': [], '61_90': [], '91_plus': []}
    for p in unpaid:
        age = (today - p.bill_date).days
        due = float(p.due_amount)
        entry = {
            'bill_number': p.bill_number,
            'bill_date':   p.bill_date,
            'due':         due,
            'age':         age,
        }
        if age <= 30:
            buckets['0_30'].append(entry)
        elif age <= 60:
            buckets['31_60'].append(entry)
        elif age <= 90:
            buckets['61_90'].append(entry)
        else:
            buckets['91_plus'].append(entry)

    totals = {k: sum(e['due'] for e in v) for k, v in buckets.items()}

    return render_template(
        'suppliers/aging.html',
        supplier=supplier,
        buckets=buckets,
        totals=totals,
        grand_total=sum(totals.values()),
        title=f'Aging – {supplier.name}',
    )


# ── AJAX Search ───────────────────────────────────────────────────────────────

@bp.route('/search')
@login_required
def search():
    business_id = _get_business_id()
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = (
        Supplier.query
        .filter(
            Supplier.business_id == business_id,
            Supplier.is_deleted == False,
            Supplier.is_active == True,
            db.or_(
                Supplier.name.ilike(f'%{q}%'),
                Supplier.supplier_code.ilike(f'%{q}%'),
            ),
        )
        .limit(15)
        .all()
    )
    return jsonify([s.to_dict() for s in results])
