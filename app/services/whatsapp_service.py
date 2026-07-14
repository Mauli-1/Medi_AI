"""WhatsApp send wrapper — degrades to simulated/demo mode if twilio isn't installed or fails."""
from flask import current_app
from app.extensions import db
from app.models.whatsapp_log import WhatsappLog


def is_twilio_available():
    try:
        import twilio  # noqa: F401
        return True
    except ImportError:
        return False


def send_whatsapp(business_id, to_number, message_type, message_body, patient_id=None,
                   reference_type=None, reference_id=None, sent_by=None):
    status = 'queued'
    error_message = None

    if is_twilio_available() and current_app.config.get('TWILIO_ACCOUNT_SID'):
        try:
            from twilio.rest import Client
            client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            client.messages.create(
                from_=current_app.config['TWILIO_WHATSAPP_FROM'],
                to=f'whatsapp:{to_number}',
                body=message_body,
            )
            status = 'sent'
        except Exception as exc:
            status = 'failed'
            error_message = str(exc)[:255]
    else:
        error_message = 'Demo Mode — Twilio not installed / not configured; message simulated only.'

    log = WhatsappLog(
        business_id=business_id, patient_id=patient_id, to_number=to_number,
        message_type=message_type, reference_type=reference_type, reference_id=reference_id,
        message_body=message_body, status=status, error_message=error_message, sent_by=sent_by,
    )
    db.session.add(log)
    db.session.commit()
    return log
