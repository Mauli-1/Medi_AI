"""AI Insights routes: smart reorder, chatbot (rule-based), sales forecast."""
import re
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from . import bp
from app.extensions import db
from app.models.ai_chat_log import AiChatLog
from app.services import ai_service, inventory_service, report_service


@bp.route('/')
@login_required
def index():
    return render_template('ai/index.html', title='AI Insights')


@bp.route('/smart-reorder')
@login_required
def smart_reorder():
    suggestions = ai_service.suggest_reorder(current_user.business_id, current_user.branch_id)
    return render_template('ai/smart_reorder.html', title='Smart Reorder', suggestions=suggestions)


@bp.route('/sales-forecast')
@login_required
def sales_forecast():
    days = request.args.get('days', 30, type=int)
    forecast = ai_service.sales_forecast(current_user.business_id, current_user.branch_id, days)
    return render_template('ai/sales_forecast.html', title='Sales Forecast', forecast=forecast, days=days)


@bp.route('/chatbot')
@login_required
def chatbot():
    return render_template('ai/chatbot.html', title='Smart Assistant')


@bp.route('/chatbot/ask', methods=['POST'])
@login_required
def chatbot_ask():
    question = (request.get_json() or {}).get('question', '').strip()
    bid = current_user.business_id
    branch_id = current_user.branch_id
    answer, intent = _answer(question, bid, branch_id)
    log = AiChatLog(business_id=bid, user_id=current_user.id, question=question, answer=answer, intent=intent)
    db.session.add(log)
    db.session.commit()
    return jsonify({'answer': answer})


def _answer(question, bid, branch_id):
    q = question.lower()

    m = re.search(r'stock of (.+)', q)
    if m:
        from app.models.medicine import Medicine
        name = m.group(1).strip()
        med = Medicine.query.filter(Medicine.business_id == bid, Medicine.name.ilike(f'%{name}%')).first()
        if med:
            stock = med.total_stock(branch_id)
            return f"{med.name} has {stock} units in stock.", 'stock_query'
        return f"I couldn't find a medicine matching '{name}'.", 'stock_query'

    if 'low stock' in q:
        rows = inventory_service.check_low_stock(bid, branch_id)
        if not rows:
            return "No medicines are currently below their reorder level.", 'low_stock'
        names = ', '.join(r['medicine'].name for r in rows[:5])
        return f"{len(rows)} medicine(s) are low on stock, including: {names}.", 'low_stock'

    if 'expir' in q:
        rows = inventory_service.get_expiry_alerts(bid, branch_id, days=30)
        if not rows:
            return "No batches are expiring in the next 30 days.", 'expiry_query'
        return f"{len(rows)} batch(es) are expiring within 30 days.", 'expiry_query'

    if 'sales today' in q or ('today' in q and 'sales' in q):
        from datetime import date
        from app.models.sales import Sale
        total = db.session.query(db.func.coalesce(db.func.sum(Sale.total_amount), 0)).filter(
            Sale.business_id == bid, db.func.date(Sale.invoice_date) == date.today(), Sale.status == 'confirmed',
        ).scalar() or 0
        return f"Today's sales total is ₹{float(total):,.2f}.", 'sales_query'

    if 'reorder' in q:
        suggestions = ai_service.suggest_reorder(bid, branch_id)
        if not suggestions:
            return "No reorder suggestions right now — stock levels look healthy.", 'reorder_query'
        top = suggestions[0]
        return f"{len(suggestions)} medicine(s) need reordering. Most urgent: {top['medicine_name']} ({top['days_of_stock_left']} days of stock left).", 'reorder_query'

    return ("I can help with: stock levels (\"stock of Paracetamol\"), \"low stock\", \"expiry\", "
            "\"sales today\", or \"reorder\" suggestions. This is a rule-based assistant, not a general AI."), 'unknown'
