"""Branch management routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.branch import Branch
from app.models.user import User
from app.models.sales import Sale
from app.utils.decorators import role_required


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    branches = Branch.query.filter_by(business_id=bid).order_by(Branch.is_headquarters.desc(), Branch.name).all()
    return render_template('branches/index.html', title='Branches', branches=branches)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'owner', 'admin')
def create():
    bid = current_user.business_id
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if Branch.query.filter_by(code=code).first():
            flash('Branch code already exists.', 'danger')
            return render_template('branches/form.html', title='Add Branch', branch=None)
        b = Branch(
            business_id=bid, name=request.form.get('name', '').strip(), code=code,
            phone=request.form.get('phone', '').strip() or None, email=request.form.get('email', '').strip() or None,
            address_line1=request.form.get('address_line1', '').strip() or None,
            city=request.form.get('city', '').strip() or None, state=request.form.get('state', '').strip() or None,
            pincode=request.form.get('pincode', '').strip() or None,
            manager_name=request.form.get('manager_name', '').strip() or None,
            manager_phone=request.form.get('manager_phone', '').strip() or None,
            gstin=request.form.get('gstin', '').strip() or None,
            drug_license_no=request.form.get('drug_license_no', '').strip() or None,
            is_active=True,
        )
        db.session.add(b)
        db.session.commit()
        flash(f'Branch {b.name} added.', 'success')
        return redirect(url_for('branches.index'))
    return render_template('branches/form.html', title='Add Branch', branch=None)


@bp.route('/<int:branch_id>')
@login_required
def detail(branch_id):
    branch = Branch.query.filter_by(id=branch_id, business_id=current_user.business_id).first_or_404()
    staff_count = User.query.filter_by(branch_id=branch.id).count()
    sales_count = Sale.query.filter_by(branch_id=branch.id).count()
    from sqlalchemy import func
    total_sales = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter_by(branch_id=branch.id, status='confirmed').scalar()
    return render_template('branches/detail.html', title=branch.name, branch=branch,
                            staff_count=staff_count, sales_count=sales_count, total_sales=float(total_sales or 0))


@bp.route('/<int:branch_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'owner', 'admin')
def edit(branch_id):
    branch = Branch.query.filter_by(id=branch_id, business_id=current_user.business_id).first_or_404()
    if request.method == 'POST':
        branch.name = request.form.get('name', '').strip()
        branch.phone = request.form.get('phone', '').strip() or None
        branch.email = request.form.get('email', '').strip() or None
        branch.address_line1 = request.form.get('address_line1', '').strip() or None
        branch.city = request.form.get('city', '').strip() or None
        branch.state = request.form.get('state', '').strip() or None
        branch.pincode = request.form.get('pincode', '').strip() or None
        branch.manager_name = request.form.get('manager_name', '').strip() or None
        branch.manager_phone = request.form.get('manager_phone', '').strip() or None
        branch.gstin = request.form.get('gstin', '').strip() or None
        branch.drug_license_no = request.form.get('drug_license_no', '').strip() or None
        branch.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Branch updated.', 'success')
        return redirect(url_for('branches.detail', branch_id=branch.id))
    return render_template('branches/form.html', title='Edit Branch', branch=branch)
