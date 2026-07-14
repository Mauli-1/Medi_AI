"""Inventory service functions: FEFO, stock checks, alerts, adjustments."""
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

from ..extensions import db
from ..models.medicine import Medicine, MedicineBatch
from ..models.stock_adjustment import StockAdjustment, StockAdjustmentItem


# ---------------------------------------------------------------------------
# FEFO (First Expired First Out)
# ---------------------------------------------------------------------------

def get_fefo_batches(medicine_id: int, branch_id: int, qty_needed: int) -> list:
    """Return an ordered list of batch allocations to fulfil qty_needed.

    Uses FEFO: batches are consumed in ascending expiry_date order.
    Each entry in the returned list is::

        {'batch_id': int, 'batch_number': str, 'qty_to_take': int}

    If total available stock is less than qty_needed the list will cover
    only what is available.
    """
    batches = (MedicineBatch.query
               .filter_by(medicine_id=medicine_id, branch_id=branch_id,
                          is_expired=False, is_damaged=False)
               .filter(MedicineBatch.quantity > MedicineBatch.reserved_qty)
               .order_by(MedicineBatch.expiry_date.asc())
               .all())

    allocations = []
    remaining = qty_needed

    for batch in batches:
        if remaining <= 0:
            break
        available = batch.available_qty
        if available <= 0:
            continue
        take = min(available, remaining)
        allocations.append({
            'batch_id':     batch.id,
            'batch_number': batch.batch_number,
            'qty_to_take':  take,
        })
        remaining -= take

    return allocations


# ---------------------------------------------------------------------------
# Stock levels
# ---------------------------------------------------------------------------

def get_available_stock(medicine_id: int, branch_id: int) -> int:
    """Return the total available stock for a medicine at a branch."""
    batches = (MedicineBatch.query
               .filter_by(medicine_id=medicine_id, branch_id=branch_id,
                          is_expired=False, is_damaged=False)
               .all())
    return sum(b.available_qty for b in batches)


def check_low_stock(business_id: int, branch_id: int = None) -> list:
    """Return medicines whose current stock is at or below reorder_level.

    Returns a list of dicts::

        {'medicine': Medicine, 'current_qty': int, 'reorder_level': int}
    """
    query = (Medicine.query
             .filter_by(business_id=business_id, is_active=True, is_deleted=False))
    results = []

    for med in query.all():
        if branch_id:
            current_qty = get_available_stock(med.id, branch_id)
        else:
            # Sum across all branches
            batches = (MedicineBatch.query
                       .filter_by(medicine_id=med.id, is_expired=False, is_damaged=False)
                       .all())
            current_qty = sum(b.available_qty for b in batches)

        if current_qty <= med.reorder_level:
            results.append({
                'medicine':     med,
                'current_qty':  current_qty,
                'reorder_level': med.reorder_level,
            })

    results.sort(key=lambda x: x['current_qty'])
    return results


# ---------------------------------------------------------------------------
# Expiry alerts
# ---------------------------------------------------------------------------

def get_expiry_alerts(business_id: int, branch_id: int = None, days: int = 30) -> list:
    """Return batches expiring within the next `days` days.

    Returns a list of MedicineBatch objects ordered by expiry_date ASC.
    """
    today = date.today()
    cutoff = today + timedelta(days=days)

    query = (MedicineBatch.query
             .join(Medicine, MedicineBatch.medicine_id == Medicine.id)
             .filter(
                 Medicine.business_id == business_id,
                 Medicine.is_deleted == False,
                 MedicineBatch.is_expired == False,
                 MedicineBatch.is_damaged == False,
                 MedicineBatch.expiry_date >= today,
                 MedicineBatch.expiry_date <= cutoff,
                 MedicineBatch.quantity > 0,
             )
             .order_by(MedicineBatch.expiry_date.asc()))

    if branch_id:
        query = query.filter(MedicineBatch.branch_id == branch_id)

    return query.all()


# ---------------------------------------------------------------------------
# Non-moving / dead stock
# ---------------------------------------------------------------------------

def get_non_moving_stock(business_id: int, branch_id: int = None, days: int = 90) -> list:
    """Return medicines with no sales movement in the last `days` days.

    Since the sales module may not be fully built, this falls back to checking
    batches whose updated_at has not changed (or uses a last_sold_date column
    if present). Here we use batch created_at as a proxy — batches older than
    `days` days with stock remaining are flagged.

    Returns list of dicts::

        {'medicine': Medicine, 'current_qty': int, 'days_idle': int, 'stock_value': float}
    """
    cutoff = date.today() - timedelta(days=days)
    result = []

    med_query = (Medicine.query
                 .filter_by(business_id=business_id, is_active=True, is_deleted=False))

    for med in med_query.all():
        batch_q = (MedicineBatch.query
                   .filter_by(medicine_id=med.id, is_expired=False, is_damaged=False)
                   .filter(MedicineBatch.quantity > 0))
        if branch_id:
            batch_q = batch_q.filter_by(branch_id=branch_id)

        batches = batch_q.all()
        if not batches:
            continue

        # Find most recent batch update
        latest_update = max(b.updated_at.date() for b in batches)
        if latest_update <= cutoff:
            current_qty = sum(b.available_qty for b in batches)
            if current_qty <= 0:
                continue
            days_idle = (date.today() - latest_update).days
            stock_value = sum(float(b.purchase_rate or 0) * b.available_qty for b in batches)
            result.append({
                'medicine':    med,
                'current_qty': current_qty,
                'days_idle':   days_idle,
                'stock_value': round(stock_value, 2),
                'last_update': latest_update,
            })

    result.sort(key=lambda x: x['days_idle'], reverse=True)
    return result


def get_dead_stock(business_id: int, branch_id: int = None) -> list:
    """Dead stock = non-moving for 180 days."""
    return get_non_moving_stock(business_id, branch_id=branch_id, days=180)


# ---------------------------------------------------------------------------
# Stock adjustment
# ---------------------------------------------------------------------------

def adjust_stock(batch_id: int, qty_change: int, reason: str,
                 user_id: int, adj_type: str) -> StockAdjustment:
    """Apply a stock adjustment to a MedicineBatch and create audit records.

    Args:
        batch_id:   ID of the MedicineBatch to adjust.
        qty_change: Positive to increase stock, negative to decrease.
        reason:     Free-text reason.
        user_id:    ID of the User performing the adjustment.
        adj_type:   One of StockAdjustment.ADJUSTMENT_TYPES.

    Returns:
        The created StockAdjustment record (already flushed to session).
    """
    batch = MedicineBatch.query.get_or_404(batch_id)
    med = batch.medicine

    # Generate adjustment number
    from ..models.sequence import Sequence
    adj_number, _ = Sequence.next_number('stock_adjustment', prefix='ADJ-', pad=6)

    qty_before = batch.quantity
    new_qty = max(0, qty_before + qty_change)
    batch.quantity = new_qty
    batch.updated_at = datetime.utcnow()

    adj = StockAdjustment(
        business_id  = med.business_id,
        branch_id    = batch.branch_id,
        adj_number   = adj_number,
        adj_type     = adj_type,
        reason       = reason,
        adjusted_by  = user_id,
        status       = 'approved',
    )
    db.session.add(adj)
    db.session.flush()  # get adj.id

    item = StockAdjustmentItem(
        adjustment_id = adj.id,
        batch_id      = batch_id,
        medicine_id   = med.id,
        qty_before    = qty_before,
        qty_change    = qty_change,
        qty_after     = new_qty,
        reason        = reason,
    )
    db.session.add(item)
    db.session.commit()

    return adj
