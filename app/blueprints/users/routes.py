"""User management routes (Super Admin / Owner only)."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.user import User
from app.models.branch import Branch
from app.utils.decorators import role_required

ROLE_CHOICES = ['super_admin', 'owner', 'admin', 'pharmacist', 'cashier', 'store_manager',
                 'inventory_manager', 'accountant', 'auditor', 'doctor', 'viewer']


@bp.route('/')
@login_required
@role_required('super_admin', 'owner', 'admin')
def index():
    users = User.query.order_by(User.full_name).all()
    users = [u for u in users if u.business_id == current_user.business_id]
    return render_template('users/index.html', title='Users', users=users)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'owner', 'admin')
def create():
    branches = Branch.query.filter_by(business_id=current_user.business_id).all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('users/form.html', title='Add User', user=None, branches=branches, roles=ROLE_CHOICES)
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('users/form.html', title='Add User', user=None, branches=branches, roles=ROLE_CHOICES)
        u = User(
            username=username, email=email, full_name=request.form.get('full_name', '').strip(),
            phone=request.form.get('phone', '').strip() or None, role=request.form.get('role', 'viewer'),
            branch_id=request.form.get('branch_id') or None, is_active=True,
            designation=request.form.get('designation', '').strip() or None,
        )
        u.set_password(request.form.get('password') or 'Changeme@123')
        db.session.add(u)
        db.session.commit()
        flash(f'User {u.username} created.', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', title='Add User', user=None, branches=branches, roles=ROLE_CHOICES)


@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('super_admin', 'owner', 'admin')
def edit(user_id):
    user = User.query.get_or_404(user_id)
    branches = Branch.query.filter_by(business_id=current_user.business_id).all()
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.phone = request.form.get('phone', '').strip() or None
        user.role = request.form.get('role', user.role)
        user.branch_id = request.form.get('branch_id') or None
        user.designation = request.form.get('designation', '').strip() or None
        user.is_active = 'is_active' in request.form
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', title='Edit User', user=user, branches=branches, roles=ROLE_CHOICES)


@bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
@role_required('super_admin', 'owner', 'admin')
def deactivate(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('users.index'))
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} deactivated.', 'info')
    return redirect(url_for('users.index'))
