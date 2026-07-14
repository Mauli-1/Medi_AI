"""Reports routes — generic report viewer over report_service functions."""
from datetime import date
from flask import render_template, request
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.services import report_service, inventory_service

REPORT_CATALOG = {
    'sales': [
        ('daily-sales', 'Daily Sales'),
        ('monthly-sales', 'Monthly Sales'),
        ('medicine-wise-sales', 'Medicine-wise Sales'),
        ('customer-wise-sales', 'Customer-wise Sales'),
        ('cashier-wise-sales', 'Cashier-wise Sales'),
        ('tax-wise-sales', 'Tax-wise Sales'),
    ],
    'purchase': [
        ('purchase-register', 'Purchase Register'),
        ('supplier-wise-purchase', 'Supplier-wise Purchase'),
        ('product-wise-purchase', 'Product-wise Purchase'),
        ('purchase-audit', 'Purchase Audit (Unpaid/Partial)'),
        ('supplier-outstanding', 'Supplier Outstanding Balances'),
    ],
    'inventory': [
        ('stock-summary', 'Stock Summary'),
        ('medicine-master-list', 'Medicine Master List'),
        ('low-stock', 'Low Stock Report'),
        ('expiry-near', 'Expiry Near (30 days)'),
        ('expiry-alerts-90', 'Expiry Alerts (90 days)'),
        ('non-moving-stock', 'Non-Moving Stock (90 days)'),
        ('dead-stock', 'Dead Stock (180 days)'),
        ('batch-wise-stock', 'Batch-wise Stock'),
        ('rack-wise-stock', 'Rack-wise Stock'),
        ('overstock', 'Overstock Report'),
        ('understock', 'Understock Report'),
    ],
    'financial': [
        ('pl-statement', 'Profit & Loss Statement'),
    ],
    'gst': [
        ('gstr1-summary', 'GSTR-1 Summary (current month)'),
    ],
    'compliance': [
        ('schedule-h-register', 'Schedule H / H1 Register'),
        ('narcotic-register', 'Narcotic Register'),
    ],
    'patient_doctor': [
        ('top-prescribing-doctors', 'Top Prescribing Doctors'),
        ('active-patients', 'Active Patients List'),
        ('credit-outstanding', 'Patient Credit Outstanding'),
    ],
    'loyalty': [
        ('loyalty-summary', 'Loyalty Points Summary'),
    ],
}


@bp.route('/')
@login_required
def index():
    return render_template('reports/index.html', title='Reports', catalog=REPORT_CATALOG)


@bp.route('/view/<report_key>')
@login_required
def view(report_key):
    bid = current_user.business_id
    today = date.today()
    from_date = request.args.get('from') or today.replace(day=1).isoformat()
    to_date = request.args.get('to') or today.isoformat()
    year = int(request.args.get('year') or today.year)

    rows = None
    columns = []

    if report_key == 'daily-sales':
        d = request.args.get('date') or today.isoformat()
        rows = report_service.daily_sales_report(bid, current_user.branch_id, d)
        columns = ['invoice_number', 'invoice_date', 'patient', 'total_amount', 'payment_mode', 'status']
    elif report_key == 'monthly-sales':
        rows = report_service.monthly_sales_report(bid, year)
        columns = ['month', 'total']
    elif report_key == 'medicine-wise-sales':
        rows = report_service.medicine_wise_sales(bid, from_date, to_date)
        columns = ['medicine', 'quantity', 'amount']
    elif report_key == 'customer-wise-sales':
        rows = report_service.customer_wise_sales(bid, from_date, to_date)
        columns = ['customer', 'visits', 'total']
    elif report_key == 'cashier-wise-sales':
        rows = report_service.cashier_wise_sales(bid, from_date, to_date)
        columns = ['cashier', 'bills', 'total']
    elif report_key == 'tax-wise-sales':
        rows = report_service.tax_wise_sales(bid, from_date, to_date)
        columns = ['gst_rate', 'total']
    elif report_key == 'purchase-register':
        rows = report_service.purchase_register(bid, current_user.branch_id, from_date, to_date)
        columns = ['bill_number', 'bill_date', 'supplier', 'invoice_number', 'total_amount', 'paid_amount', 'due_amount', 'payment_status']
    elif report_key == 'supplier-wise-purchase':
        rows = report_service.supplier_wise_purchase(bid, from_date, to_date)
        columns = ['supplier', 'bills', 'total']
    elif report_key == 'product-wise-purchase':
        rows = report_service.product_wise_purchase(bid, from_date, to_date)
        columns = ['medicine', 'quantity', 'amount']
    elif report_key == 'purchase-audit':
        rows = report_service.purchase_audit_report(bid)
        columns = ['bill_number', 'bill_date', 'supplier', 'total', 'paid', 'due', 'status']
    elif report_key == 'stock-summary':
        rows = report_service.stock_summary(bid)
        columns = ['medicine_code', 'name', 'category', 'total_qty', 'reorder_level', 'status']
    elif report_key == 'low-stock':
        records = inventory_service.check_low_stock(bid, current_user.branch_id)
        rows = [{'medicine': r['medicine'].name, 'current_qty': r['current_qty'], 'reorder_level': r['reorder_level']} for r in records]
        columns = ['medicine', 'current_qty', 'reorder_level']
    elif report_key == 'expiry-near':
        rows = report_service.expiry_near_report(bid)
        columns = ['medicine', 'batch_number', 'expiry_date', 'quantity']
    elif report_key == 'expiry-alerts-90':
        records = inventory_service.get_expiry_alerts(bid, current_user.branch_id, days=90)
        rows = [{'medicine': b.medicine.name if b.medicine else '', 'batch_number': b.batch_number,
                  'expiry_date': b.expiry_date.isoformat() if b.expiry_date else '', 'quantity': b.quantity} for b in records]
        columns = ['medicine', 'batch_number', 'expiry_date', 'quantity']
    elif report_key == 'non-moving-stock':
        records = inventory_service.get_non_moving_stock(bid, current_user.branch_id, days=90)
        rows = [{'medicine': r['medicine'].name, 'current_qty': r['current_qty'], 'days_idle': r['days_idle'], 'stock_value': r['stock_value']} for r in records]
        columns = ['medicine', 'current_qty', 'days_idle', 'stock_value']
    elif report_key == 'dead-stock':
        records = inventory_service.get_dead_stock(bid, current_user.branch_id)
        rows = [{'medicine': r['medicine'].name, 'current_qty': r['current_qty'], 'days_idle': r['days_idle'], 'stock_value': r['stock_value']} for r in records]
        columns = ['medicine', 'current_qty', 'days_idle', 'stock_value']
    elif report_key == 'batch-wise-stock':
        rows = report_service.batch_wise_stock(bid)
        columns = ['medicine', 'batch_number', 'expiry_date', 'quantity', 'rack']
    elif report_key == 'rack-wise-stock':
        rows = report_service.rack_wise_stock(bid)
        columns = ['rack', 'quantity', 'item_count']
    elif report_key == 'overstock':
        rows = report_service.overstock_report(bid)
        columns = ['medicine', 'max_stock_level', 'current_qty']
    elif report_key == 'understock':
        rows = report_service.understock_report(bid)
        columns = ['medicine', 'reorder_level', 'current_qty']
    elif report_key == 'pl-statement':
        data = report_service.pl_statement(bid, from_date, to_date)
        rows = [data]
        columns = ['revenue', 'cogs', 'gross_profit', 'expenses', 'net_profit']
    elif report_key == 'schedule-h-register':
        records = report_service.schedule_h_register(bid, from_date, to_date)
        rows = [{'type': r.record_type, 'medicine_id': r.medicine_id, 'sale_id': r.sale_id, 'patient_id': r.patient_id, 'date': r.dispensed_date.isoformat() if r.dispensed_date else ''} for r in records]
        columns = ['type', 'medicine_id', 'sale_id', 'patient_id', 'date']
    elif report_key == 'narcotic-register':
        records = report_service.narcotic_register(bid, from_date, to_date)
        rows = [{'medicine_id': r.medicine_id, 'sale_id': r.sale_id, 'patient_id': r.patient_id, 'date': r.dispensed_date.isoformat() if r.dispensed_date else ''} for r in records]
        columns = ['medicine_id', 'sale_id', 'patient_id', 'date']
    elif report_key == 'top-prescribing-doctors':
        rows = report_service.top_prescribing_doctors(bid)
        columns = ['doctor', 'prescription_count']
    elif report_key == 'gstr1-summary':
        period = request.args.get('period') or today.strftime('%Y-%m')
        rows = report_service.gstr1_data(bid, period)
        columns = ['invoice_number', 'invoice_date', 'customer_gstin', 'subtotal', 'cgst_amount', 'sgst_amount', 'igst_amount', 'total_amount']
    elif report_key == 'active-patients':
        from app.models.patient import Patient
        patients = Patient.query.filter_by(business_id=bid, is_active=True).order_by(Patient.full_name).all()
        rows = [{'patient_code': p.patient_code, 'full_name': p.full_name, 'phone': p.phone,
                  'loyalty_points': p.loyalty_points or 0, 'total_purchases': float(p.total_purchases or 0)} for p in patients]
        columns = ['patient_code', 'full_name', 'phone', 'loyalty_points', 'total_purchases']
    elif report_key == 'credit-outstanding':
        from app.models.sales import Sale
        from sqlalchemy import func
        rows_q = (
            db.session.query(
                Sale.patient_id, func.sum(Sale.total_amount - Sale.paid_amount).label('due')
            )
            .filter(Sale.business_id == bid, Sale.payment_mode == 'credit', Sale.status == 'confirmed')
            .group_by(Sale.patient_id)
            .having(func.sum(Sale.total_amount - Sale.paid_amount) > 0)
            .all()
        )
        from app.models.patient import Patient
        rows = []
        for pid, due in rows_q:
            p = Patient.query.get(pid) if pid else None
            rows.append({'patient': p.full_name if p else 'Walk-in', 'outstanding': float(due)})
        columns = ['patient', 'outstanding']
    elif report_key == 'loyalty-summary':
        from app.models.patient import Patient
        patients = Patient.query.filter_by(business_id=bid).order_by(Patient.loyalty_points.desc()).limit(50).all()
        rows = [{'patient': p.full_name, 'tier': p.loyalty_tier or 'silver', 'points': p.loyalty_points or 0} for p in patients]
        columns = ['patient', 'tier', 'points']
    elif report_key == 'supplier-outstanding':
        from app.models.supplier import Supplier
        suppliers = Supplier.query.filter(Supplier.business_id == bid, Supplier.outstanding > 0).order_by(Supplier.outstanding.desc()).all()
        rows = [{'supplier': s.name, 'outstanding': float(s.outstanding or 0), 'payment_terms_days': s.payment_terms} for s in suppliers]
        columns = ['supplier', 'outstanding', 'payment_terms_days']
    elif report_key == 'medicine-master-list':
        from app.models.medicine import Medicine
        meds = Medicine.query.filter_by(business_id=bid, is_deleted=False).order_by(Medicine.name).all()
        rows = [{'medicine_code': m.medicine_code, 'name': m.name, 'generic_name': m.generic_name,
                  'schedule_type': m.schedule_type, 'mrp': float(m.mrp or 0)} for m in meds]
        columns = ['medicine_code', 'name', 'generic_name', 'schedule_type', 'mrp']

    if rows is None:
        rows = []

    report_name = next((name for cat in REPORT_CATALOG.values() for key, name in cat if key == report_key), report_key)
    return render_template('reports/view.html', title=report_name, report_key=report_key, rows=rows,
                            columns=columns, from_date=from_date, to_date=to_date, year=year)


@bp.route('/export/<report_key>.xlsx')
@login_required
def export(report_key):
    from flask import send_file
    import io
    bid = current_user.business_id
    from_date = request.args.get('from') or date.today().replace(day=1).isoformat()
    to_date = request.args.get('to') or date.today().isoformat()

    rows = []
    columns = []
    if report_key == 'medicine-wise-sales':
        rows = report_service.medicine_wise_sales(bid, from_date, to_date)
        columns = ['medicine', 'quantity', 'amount']
    elif report_key == 'stock-summary':
        rows = report_service.stock_summary(bid)
        columns = ['medicine_code', 'name', 'category', 'total_qty', 'reorder_level', 'status']
    elif report_key == 'purchase-register':
        rows = report_service.purchase_register(bid, current_user.branch_id, from_date, to_date)
        columns = ['bill_number', 'bill_date', 'supplier', 'invoice_number', 'total_amount', 'paid_amount', 'due_amount', 'payment_status']

    excel = report_service.export_to_excel(rows, columns, sheet_name=report_key[:31])
    return send_file(io.BytesIO(excel), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      download_name=f'{report_key}.xlsx', as_attachment=True)
