"""Compliance routes: Schedule H/H1/Narcotic registers, drug inspector report."""
from datetime import date, timedelta
from flask import render_template, request, send_file
from flask_login import login_required, current_user
from . import bp
from app.models.compliance import ComplianceRecord
from app.services import report_service
import io


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    today = date.today()
    month_start = today.replace(day=1)
    counts = {
        'schedule_h': ComplianceRecord.query.filter_by(business_id=bid, record_type='schedule_h').count(),
        'schedule_h1': ComplianceRecord.query.filter_by(business_id=bid, record_type='schedule_h1').count(),
        'narcotic': ComplianceRecord.query.filter_by(business_id=bid, record_type='narcotic').count(),
    }
    return render_template('compliance/index.html', title='Compliance', counts=counts, month_start=month_start, today=today)


@bp.route('/register/<record_type>')
@login_required
def register(record_type):
    bid = current_user.business_id
    if record_type not in ('schedule_h', 'schedule_h1', 'narcotic'):
        record_type = 'schedule_h'
    from_date = request.args.get('from') or (date.today() - timedelta(days=30)).isoformat()
    to_date = request.args.get('to') or date.today().isoformat()
    if record_type == 'narcotic':
        records = report_service.narcotic_register(bid, from_date, to_date)
    else:
        records = ComplianceRecord.query.filter(
            ComplianceRecord.business_id == bid, ComplianceRecord.record_type == record_type,
            ComplianceRecord.dispensed_date >= from_date, ComplianceRecord.dispensed_date <= to_date,
        ).order_by(ComplianceRecord.dispensed_date.desc()).all()
    return render_template('compliance/register.html', title=record_type.replace('_', ' ').title() + ' Register',
                            records=records, record_type=record_type, from_date=from_date, to_date=to_date)


@bp.route('/drug-inspector-report')
@login_required
def drug_inspector_report():
    bid = current_user.business_id
    from_date = request.args.get('from') or (date.today() - timedelta(days=30)).isoformat()
    to_date = request.args.get('to') or date.today().isoformat()
    records = ComplianceRecord.query.filter(
        ComplianceRecord.business_id == bid,
        ComplianceRecord.dispensed_date >= from_date, ComplianceRecord.dispensed_date <= to_date,
    ).order_by(ComplianceRecord.dispensed_date.desc()).all()
    return render_template('compliance/drug_inspector_report.html', title='Drug Inspector Report',
                            records=records, from_date=from_date, to_date=to_date)


@bp.route('/drug-inspector-report.pdf')
@login_required
def drug_inspector_report_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    bid = current_user.business_id
    from_date = request.args.get('from') or (date.today() - timedelta(days=30)).isoformat()
    to_date = request.args.get('to') or date.today().isoformat()
    records = ComplianceRecord.query.filter(
        ComplianceRecord.business_id == bid,
        ComplianceRecord.dispensed_date >= from_date, ComplianceRecord.dispensed_date <= to_date,
    ).order_by(ComplianceRecord.dispensed_date.desc()).all()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f'Drug Inspector Report ({from_date} to {to_date})', styles['Title'])]
    data = [['Type', 'Medicine', 'Patient', 'Doctor', 'Qty', 'Date']]
    for r in records:
        data.append([
            r.record_type, r.medicine.name if r.medicine else '', r.patient.full_name if r.patient else '',
            r.doctor.full_name if r.doctor else '', str(r.quantity_dispensed or ''),
            r.dispensed_date.strftime('%d-%m-%Y') if r.dispensed_date else '',
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A6B5A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name='drug_inspector_report.pdf')
