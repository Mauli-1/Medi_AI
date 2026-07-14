"""Dashboard routes."""
from datetime import date, timedelta, datetime
from flask import render_template, jsonify
from flask_login import login_required, current_user
from . import bp
from ...extensions import db
from sqlalchemy import text

def _q(sql, params={}):
    try:
        return db.session.execute(text(sql), params).scalar() or 0
    except Exception:
        return 0

@bp.route('/')
@login_required
def index():
    today = date.today()
    bid = current_user.business_id
    month_start = today.replace(day=1)

    fy_start = today.replace(month=4, day=1) if today.month >= 4 else today.replace(year=today.year-1, month=4, day=1)
    kpis = {
        'today_sales': _q("SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE business_id=:b AND DATE(invoice_date)=:d AND status='confirmed'", {'b': bid, 'd': today}),
        'today_transactions': _q("SELECT COUNT(*) FROM sales WHERE business_id=:b AND DATE(invoice_date)=:d AND status='confirmed'", {'b': bid, 'd': today}),
        'month_sales': _q("SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE business_id=:b AND DATE(invoice_date)>=:ms AND status='confirmed'", {'b': bid, 'ms': month_start}),
        'fy_sales': _q("SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE business_id=:b AND DATE(invoice_date)>=:fs AND status='confirmed'", {'b': bid, 'fs': fy_start}),
        'low_stock_count': _q("SELECT COUNT(*) FROM medicines m WHERE m.business_id=:b AND m.is_deleted=0 AND (SELECT COALESCE(SUM(quantity),0) FROM medicine_batches WHERE medicine_id=m.id AND is_expired=0) <= m.reorder_level", {'b': bid}),
        'expiring_soon': _q("SELECT COUNT(*) FROM medicine_batches mb JOIN medicines m ON mb.medicine_id=m.id WHERE m.business_id=:b AND mb.expiry_date<=:ed AND mb.expiry_date>=:td AND mb.quantity>0", {'b': bid, 'ed': today + timedelta(days=30), 'td': today}),
        'outstanding': _q("SELECT COALESCE(SUM(total_amount-paid_amount),0) FROM sales WHERE business_id=:b AND payment_mode='credit' AND status='confirmed'", {'b': bid}),
        'unpaid_invoices': _q("SELECT COALESCE(SUM(total_amount-paid_amount),0) FROM sales WHERE business_id=:b AND payment_mode='credit' AND status='confirmed'", {'b': bid}),
        'pending_purchases': _q("SELECT COUNT(*) FROM purchase_orders WHERE business_id=:b AND status='pending'", {'b': bid}),
        'active_patients': _q("SELECT COUNT(*) FROM patients WHERE business_id=:b AND is_active=1", {'b': bid}),
        'dead_stock_count': 0,
        'non_moving_count': 0,
    }

    # Sales trend last 30 days
    labels, values = [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        val = _q("SELECT COALESCE(SUM(total_amount),0) FROM sales WHERE business_id=:b AND DATE(invoice_date)=:d AND status='confirmed'", {'b': bid, 'd': d})
        labels.append(d.strftime('%d %b'))
        values.append(float(val))

    # Top 5 medicines
    try:
        rows = db.session.execute(text(
            "SELECT m.name, SUM(si.quantity) as qty, SUM(si.total_amount) as amt FROM sale_items si JOIN medicines m ON si.medicine_id=m.id JOIN sales s ON si.sale_id=s.id WHERE s.business_id=:b AND s.invoice_date>=:ms GROUP BY m.id ORDER BY qty DESC LIMIT 5"
        ), {'b': bid, 'ms': month_start}).fetchall()
        top_medicines = [{'name': r[0], 'quantity': int(r[1]), 'amount': float(r[2])} for r in rows]
    except Exception:
        top_medicines = []

    # Recent sales
    try:
        from app.models.sales import Sale
        recent_transactions = Sale.query.filter_by(business_id=bid).order_by(Sale.invoice_date.desc()).limit(5).all()
    except Exception:
        recent_transactions = []

    return render_template('dashboard/index.html', kpis=kpis,
        sales_trend_labels=labels, sales_trend_values=values,
        top_medicines=top_medicines, recent_transactions=recent_transactions, today=today)
