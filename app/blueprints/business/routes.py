"""Business setup and edit routes."""
import os
import uuid
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from . import bp
from .forms import BusinessStep1Form, BusinessStep2Form, BusinessStep3Form, BusinessEditForm
from ...extensions import db
from ...models.business import Business
from ...utils.decorators import role_required
from ...utils.helpers import allowed_file


# ── Setup wizard ─────────────────────────────────────────────────────────────

@bp.route('/setup', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def setup():
    """3-step business setup wizard."""
    step = int(request.args.get('step', 1))
    business = Business.query.first()

    if business and business.setup_complete and step == 1:
        flash('Business is already configured.', 'info')
        return redirect(url_for('business.edit'))

    if step == 1:
        form = BusinessStep1Form(obj=business)
        if form.validate_on_submit():
            session['setup_step1'] = {
                'name':       form.name.data,
                'legal_name': form.legal_name.data,
                'short_name': form.short_name.data,
                'email':      form.email.data,
                'phone':      form.phone.data,
                'alt_phone':  form.alt_phone.data,
                'website':    form.website.data,
                'tagline':    form.tagline.data,
            }
            return redirect(url_for('business.setup', step=2))
        return render_template('business/setup.html', form=form, step=1)

    elif step == 2:
        form = BusinessStep2Form(obj=business)
        if form.validate_on_submit():
            session['setup_step2'] = {
                'address_line1':    form.address_line1.data,
                'address_line2':    form.address_line2.data,
                'city':             form.city.data,
                'state':            form.state.data,
                'pincode':          form.pincode.data,
                'gstin':            form.gstin.data,
                'pan':              form.pan.data,
                'drug_license_no':  form.drug_license_no.data,
                'drug_license_no2': form.drug_license_no2.data,
                'fssai_no':         form.fssai_no.data,
            }
            return redirect(url_for('business.setup', step=3))
        return render_template('business/setup.html', form=form, step=2)

    elif step == 3:
        form = BusinessStep3Form()
        if form.validate_on_submit():
            step1 = session.pop('setup_step1', {})
            step2 = session.pop('setup_step2', {})

            if not business:
                business = Business()
                db.session.add(business)

            # Apply all collected data
            for k, v in {**step1, **step2}.items():
                setattr(business, k, v)

            business.bank_name        = form.bank_name.data
            business.bank_branch      = form.bank_branch.data
            business.bank_account_no  = form.bank_account_no.data
            business.bank_ifsc        = form.bank_ifsc.data
            business.upi_id           = form.upi_id.data
            business.invoice_prefix   = form.invoice_prefix.data or 'INV'
            business.invoice_terms    = form.invoice_terms.data
            business.invoice_footer   = form.invoice_footer.data
            business.enable_loyalty       = form.enable_loyalty.data
            business.enable_whatsapp      = form.enable_whatsapp.data
            business.enable_abha          = form.enable_abha.data
            business.enable_eprescription = form.enable_eprescription.data
            business.enable_barcode       = form.enable_barcode.data
            business.enable_sms           = form.enable_sms.data
            business.setup_complete   = True

            # Logo upload
            logo = form.logo_file.data
            if logo and allowed_file(logo.filename,
                                     current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
                ext = logo.filename.rsplit('.', 1)[1].lower()
                filename = f'logo_{uuid.uuid4().hex[:8]}.{ext}'
                logo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                business.logo_filename = filename

            db.session.commit()
            flash('Business setup complete! Welcome to MSMS.', 'success')
            return redirect(url_for('dashboard.index'))

        return render_template('business/setup.html', form=form, step=3)

    flash('Invalid setup step.', 'danger')
    return redirect(url_for('business.setup', step=1))


# ── Edit ─────────────────────────────────────────────────────────────────────

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def edit():
    business = Business.query.first()
    if not business:
        flash('Please complete the setup wizard first.', 'warning')
        return redirect(url_for('business.setup'))

    form = BusinessEditForm(obj=business)
    if form.validate_on_submit():
        form.populate_obj(business)

        logo = form.logo_file.data
        if logo and hasattr(logo, 'filename') and logo.filename and allowed_file(
                logo.filename, current_app.config['ALLOWED_IMAGE_EXTENSIONS']):
            ext = logo.filename.rsplit('.', 1)[1].lower()
            filename = f'logo_{uuid.uuid4().hex[:8]}.{ext}'
            logo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            business.logo_filename = filename

        db.session.commit()
        flash('Business settings saved.', 'success')
        return redirect(url_for('business.edit'))

    return render_template('business/edit.html', form=form, business=business)
