"""WhatsApp Notifications routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from app.models.whatsapp_log import WhatsappLog
from app.models.sales import Sale
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.services.whatsapp_service import send_whatsapp, is_twilio_available


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    logs = WhatsappLog.query.filter_by(business_id=bid).order_by(WhatsappLog.created_at.desc()).limit(10).all()
    patients = Patient.query.filter_by(business_id=bid, is_active=True).order_by(Patient.full_name).all()
    return render_template('whatsapp/index.html', title='WhatsApp Notifications', logs=logs,
                            patients=patients, demo_mode=not is_twilio_available())


@bp.route('/send-invoice/<int:sale_id>', methods=['POST'])
@login_required
def send_invoice(sale_id):
    sale = Sale.query.filter_by(id=sale_id, business_id=current_user.business_id).first_or_404()
    if not sale.patient or not sale.patient.phone:
        flash('No patient phone number on file for this sale.', 'danger')
        return redirect(url_for('whatsapp.index'))
    body = f"Your invoice {sale.invoice_number} for ₹{sale.total_amount} has been generated. Thank you for shopping with us."
    log = send_whatsapp(current_user.business_id, sale.patient.phone, 'invoice', body,
                         patient_id=sale.patient_id, reference_type='sale', reference_id=sale.id, sent_by=current_user.id)
    flash(f'Invoice message {log.status}.', 'success' if log.status == 'sent' else 'info')
    return redirect(url_for('whatsapp.index'))


@bp.route('/send-payment-reminder/<int:patient_id>', methods=['POST'])
@login_required
def send_payment_reminder(patient_id):
    patient = Patient.query.filter_by(id=patient_id, business_id=current_user.business_id).first_or_404()
    if not patient.phone:
        flash('No phone number on file for this patient.', 'danger')
        return redirect(url_for('whatsapp.index'))
    body = f"Dear {patient.full_name}, you have an outstanding payment due. Please visit the store to clear your dues."
    log = send_whatsapp(current_user.business_id, patient.phone, 'payment_reminder', body,
                         patient_id=patient.id, sent_by=current_user.id)
    flash(f'Payment reminder {log.status}.', 'success' if log.status == 'sent' else 'info')
    return redirect(url_for('whatsapp.index'))


@bp.route('/send-refill-reminder/<int:prescription_id>', methods=['POST'])
@login_required
def send_refill_reminder(prescription_id):
    rx = Prescription.query.filter_by(id=prescription_id, business_id=current_user.business_id).first_or_404()
    if not rx.patient or not rx.patient.phone:
        flash('No phone number on file for this patient.', 'danger')
        return redirect(url_for('whatsapp.index'))
    body = f"Dear {rx.patient.full_name}, your prescription {rx.prescription_code} refill is due. Please visit the store."
    log = send_whatsapp(current_user.business_id, rx.patient.phone, 'refill_reminder', body,
                         patient_id=rx.patient_id, reference_type='prescription', reference_id=rx.id, sent_by=current_user.id)
    flash(f'Refill reminder {log.status}.', 'success' if log.status == 'sent' else 'info')
    return redirect(url_for('whatsapp.index'))


@bp.route('/logs')
@login_required
def logs():
    bid = current_user.business_id
    msg_type = request.args.get('type', '')
    status = request.args.get('status', '')
    query = WhatsappLog.query.filter_by(business_id=bid)
    if msg_type:
        query = query.filter_by(message_type=msg_type)
    if status:
        query = query.filter_by(status=status)
    entries = query.order_by(WhatsappLog.created_at.desc()).all()
    return render_template('whatsapp/logs.html', title='WhatsApp Logs', entries=entries, msg_type=msg_type, status=status)
