"""Accounting routes: chart of accounts, journal entries, ledger, trial balance, P&L, balance sheet."""
from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from . import bp
from app.extensions import db
from app.models.accounting import ChartOfAccount, JournalEntry, JournalEntryLine
from app.models.sequence import Sequence
from app.services import report_service

DEFAULT_ACCOUNTS = [
    ('1000', 'Cash', 'asset'),
    ('1010', 'Bank', 'asset'),
    ('1100', 'Accounts Receivable', 'asset'),
    ('1200', 'Inventory', 'asset'),
    ('2000', 'Accounts Payable', 'liability'),
    ('3000', 'Owner Equity', 'equity'),
    ('4000', 'Sales Revenue', 'revenue'),
    ('5000', 'Purchase Expense', 'expense'),
    ('5100', 'Operating Expense', 'expense'),
]


def _ensure_default_accounts(business_id):
    if ChartOfAccount.query.filter_by(business_id=business_id).first():
        return
    for code, name, acc_type in DEFAULT_ACCOUNTS:
        db.session.add(ChartOfAccount(business_id=business_id, code=code, name=name, type=acc_type, is_system=True))
    db.session.commit()


@bp.route('/')
@login_required
def index():
    bid = current_user.business_id
    _ensure_default_accounts(bid)
    today = date.today()
    todays_entries = JournalEntry.query.filter_by(business_id=bid, entry_date=today).count()
    account_count = ChartOfAccount.query.filter_by(business_id=bid).count()
    return render_template('accounting/index.html', title='Accounting', todays_entries=todays_entries, account_count=account_count, today=today)


@bp.route('/chart-of-accounts')
@login_required
def chart_of_accounts():
    bid = current_user.business_id
    _ensure_default_accounts(bid)
    accounts = ChartOfAccount.query.filter_by(business_id=bid).order_by(ChartOfAccount.code).all()
    return render_template('accounting/chart_of_accounts.html', title='Chart of Accounts', accounts=accounts)


@bp.route('/chart-of-accounts/new', methods=['POST'])
@login_required
def new_account():
    bid = current_user.business_id
    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    acc_type = request.form.get('type', '')
    if not code or not name or acc_type not in ('asset', 'liability', 'equity', 'revenue', 'expense'):
        flash('Code, name and a valid account type are required.', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))
    if ChartOfAccount.query.filter_by(business_id=bid, code=code).first():
        flash(f'Account code {code} already exists.', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))
    db.session.add(ChartOfAccount(business_id=bid, code=code, name=name, type=acc_type))
    db.session.commit()
    flash('Account added.', 'success')
    return redirect(url_for('accounting.chart_of_accounts'))


@bp.route('/journal/new', methods=['GET', 'POST'])
@login_required
def journal_new():
    bid = current_user.business_id
    _ensure_default_accounts(bid)
    accounts = ChartOfAccount.query.filter_by(business_id=bid).order_by(ChartOfAccount.code).all()

    if request.method == 'POST':
        entry_date = request.form.get('entry_date') or date.today().isoformat()
        narration = request.form.get('narration', '')
        account_ids = request.form.getlist('account_id[]')
        debits = request.form.getlist('debit[]')
        credits = request.form.getlist('credit[]')

        lines = []
        total_debit = total_credit = 0
        for acc_id, dr, cr in zip(account_ids, debits, credits):
            if not acc_id:
                continue
            dr = float(dr or 0)
            cr = float(cr or 0)
            if dr == 0 and cr == 0:
                continue
            total_debit += dr
            total_credit += cr
            lines.append((int(acc_id), dr, cr))

        if not lines:
            flash('Add at least one debit/credit line.', 'danger')
            return render_template('accounting/journal_new.html', title='New Journal Entry', accounts=accounts)

        if round(total_debit, 2) != round(total_credit, 2):
            flash(f'Entry does not balance: Debit ₹{total_debit:,.2f} vs Credit ₹{total_credit:,.2f}', 'danger')
            return render_template('accounting/journal_new.html', title='New Journal Entry', accounts=accounts)

        entry_code, _ = Sequence.next_number(f'journal-{bid}', prefix='JE-', pad=5)
        entry = JournalEntry(
            business_id=bid,
            branch_id=current_user.branch_id,
            entry_number=entry_code,
            entry_date=datetime.strptime(entry_date, '%Y-%m-%d').date(),
            narration=narration,
            total_debit=total_debit,
            total_credit=total_credit,
            created_by=current_user.id,
        )
        db.session.add(entry)
        db.session.flush()
        for acc_id, dr, cr in lines:
            db.session.add(JournalEntryLine(entry_id=entry.id, account_id=acc_id, debit=dr, credit=cr))
        db.session.commit()
        flash(f'Journal entry {entry_code} saved.', 'success')
        return redirect(url_for('accounting.day_book', date=entry.entry_date.isoformat()))

    return render_template('accounting/journal_new.html', title='New Journal Entry', accounts=accounts)


@bp.route('/day-book')
@login_required
def day_book():
    bid = current_user.business_id
    day = request.args.get('date') or date.today().isoformat()
    entries = (
        JournalEntry.query.filter_by(business_id=bid, entry_date=datetime.strptime(day, '%Y-%m-%d').date())
        .order_by(JournalEntry.id)
        .all()
    )
    return render_template('accounting/day_book.html', title='Day Book', entries=entries, day=day)


@bp.route('/ledger/<int:account_id>')
@login_required
def ledger(account_id):
    bid = current_user.business_id
    account = ChartOfAccount.query.filter_by(id=account_id, business_id=bid).first_or_404()
    lines = (
        db.session.query(JournalEntryLine, JournalEntry)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(JournalEntryLine.account_id == account_id, JournalEntry.business_id == bid)
        .order_by(JournalEntry.entry_date, JournalEntry.id)
        .all()
    )
    running = 0
    rows = []
    for line, entry in lines:
        running += float(line.debit or 0) - float(line.credit or 0)
        rows.append({'date': entry.entry_date, 'entry_number': entry.entry_number, 'narration': entry.narration,
                      'debit': float(line.debit or 0), 'credit': float(line.credit or 0), 'balance': running})
    return render_template('accounting/ledger.html', title='Ledger', account=account, rows=rows)


@bp.route('/trial-balance')
@login_required
def trial_balance():
    bid = current_user.business_id
    as_of = request.args.get('as_of') or date.today().isoformat()
    as_of_date = datetime.strptime(as_of, '%Y-%m-%d').date()
    rows = (
        db.session.query(
            ChartOfAccount.code, ChartOfAccount.name, ChartOfAccount.type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('credit'),
        )
        .outerjoin(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccount.id)
        .outerjoin(JournalEntry, db.and_(JournalEntry.id == JournalEntryLine.entry_id, JournalEntry.entry_date <= as_of_date))
        .filter(ChartOfAccount.business_id == bid)
        .group_by(ChartOfAccount.id)
        .order_by(ChartOfAccount.code)
        .all()
    )
    total_debit = sum(float(r.debit) for r in rows)
    total_credit = sum(float(r.credit) for r in rows)
    return render_template('accounting/trial_balance.html', title='Trial Balance', rows=rows,
                            total_debit=total_debit, total_credit=total_credit, as_of=as_of)


@bp.route('/pl-statement')
@login_required
def pl_statement():
    bid = current_user.business_id
    from_date = request.args.get('from') or date.today().replace(day=1).isoformat()
    to_date = request.args.get('to') or date.today().isoformat()
    data = report_service.pl_statement(bid, from_date, to_date)
    return render_template('accounting/pl_statement.html', title='Profit & Loss Statement', data=data, from_date=from_date, to_date=to_date)


@bp.route('/balance-sheet')
@login_required
def balance_sheet():
    bid = current_user.business_id
    as_of = request.args.get('as_of') or date.today().isoformat()
    as_of_date = datetime.strptime(as_of, '%Y-%m-%d').date()
    rows = (
        db.session.query(
            ChartOfAccount.type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label('debit'),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label('credit'),
        )
        .outerjoin(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccount.id)
        .outerjoin(JournalEntry, db.and_(JournalEntry.id == JournalEntryLine.entry_id, JournalEntry.entry_date <= as_of_date))
        .filter(ChartOfAccount.business_id == bid)
        .group_by(ChartOfAccount.type)
        .all()
    )
    balances = {'asset': 0, 'liability': 0, 'equity': 0}
    for r in rows:
        net = float(r.debit) - float(r.credit)
        if r.type == 'asset':
            balances['asset'] += net
        elif r.type == 'liability':
            balances['liability'] += -net
        elif r.type == 'equity':
            balances['equity'] += -net
    return render_template('accounting/balance_sheet.html', title='Balance Sheet', balances=balances, as_of=as_of)
