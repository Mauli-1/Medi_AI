from datetime import datetime
from app.extensions import db
from app.models.sequence import Sequence
from app.models.sales import Sale, SaleItem
from app.models.gst import GstTransaction
from app.services.gst_service import calculate_line_gst, get_supply_type
from app.services.inventory_service import get_fefo_batches

def next_invoice_number(business_id, branch_id, year=None):
    if not year:
        year = datetime.utcnow().year
    code, _ = Sequence.next_number(f'invoice-{business_id}-{year}', prefix=f'INV-{year}-', pad=5)
    return code

def save_invoice(sale_data, items_data, user_id):
    business_id = sale_data['business_id']
    branch_id = sale_data['branch_id']
    year = datetime.utcnow().year
    invoice_number = next_invoice_number(business_id, branch_id, year)
    supply_type = get_supply_type(
        sale_data.get('business_gstin', ''),
        sale_data.get('customer_gstin', '')
    )
    subtotal = cgst_total = sgst_total = igst_total = 0
    sale_items = []
    for item in items_data:
        g = calculate_line_gst(
            item['selling_rate'], item['qty'],
            item.get('discount_pct', 0), item['gst_rate'], supply_type
        )
        subtotal += g['taxable_value']
        cgst_total += g['cgst_amount']
        sgst_total += g['sgst_amount']
        igst_total += g['igst_amount']
        sale_items.append({**item, **g})
    grand_total = subtotal + cgst_total + sgst_total + igst_total
    round_off = round(round(grand_total) - grand_total, 2)
    grand_total = round(grand_total + round_off, 2)
    sale = Sale(
        business_id=business_id,
        branch_id=branch_id,
        invoice_number=invoice_number,
        patient_id=sale_data.get('patient_id'),
        prescription_id=sale_data.get('prescription_id'),
        cashier_id=user_id,
        subtotal=subtotal,
        discount_amount=sale_data.get('discount_amount', 0),
        cgst_amount=cgst_total,
        sgst_amount=sgst_total,
        igst_amount=igst_total,
        round_off=round_off,
        total_amount=grand_total,
        paid_amount=sale_data.get('paid_amount', grand_total),
        payment_mode=sale_data.get('payment_mode', 'cash'),
        status='confirmed'
    )
    db.session.add(sale)
    db.session.flush()
    from app.models.medicine import MedicineBatch
    for item in sale_items:
        batch = MedicineBatch.query.get(item['batch_id'])
        if batch:
            batch.quantity -= item['qty']
        si = SaleItem(
            sale_id=sale.id,
            medicine_id=item['medicine_id'],
            batch_id=item['batch_id'],
            quantity=item['qty'],
            mrp=item.get('mrp', item['selling_rate']),
            selling_rate=item['selling_rate'],
            discount_pct=item.get('discount_pct', 0),
            gst_rate=item['gst_rate'],
            cgst_amount=item['cgst_amount'],
            sgst_amount=item['sgst_amount'],
            igst_amount=item['igst_amount'],
            total_amount=item['total'],
        )
        db.session.add(si)
        _write_compliance(sale, si, item, business_id, branch_id, user_id)
    db.session.commit()
    if sale.patient_id:
        from app.services.loyalty_service import award_points_for_sale
        award_points_for_sale(sale)
    return sale

def _write_compliance(sale, sale_item, item, business_id, branch_id, user_id):
    from app.models.medicine import Medicine
    from app.models.compliance import ComplianceRecord
    med = Medicine.query.get(item['medicine_id'])
    if med and med.schedule_type in ('H', 'H1', 'X'):
        rec = ComplianceRecord(
            business_id=business_id,
            branch_id=branch_id,
            record_type='schedule_h' if med.schedule_type == 'H' else ('schedule_h1' if med.schedule_type == 'H1' else 'narcotic'),
            sale_id=sale.id,
            medicine_id=med.id,
            patient_id=sale.patient_id,
            prescription_id=sale.prescription_id,
            quantity_dispensed=item['qty'],
            dispensed_by=user_id,
            batch_number=item.get('batch_number', '')
        )
        db.session.add(rec)

def generate_invoice_pdf(sale_id):
    from flask import render_template, current_app
    try:
        from weasyprint import HTML
        sale = Sale.query.get(sale_id)
        html = render_template('sales/invoice.html', sale=sale)
        return HTML(string=html).write_pdf()
    except Exception:
        return None
