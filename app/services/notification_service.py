from datetime import datetime, timedelta
from app.extensions import db
from app.models.notification import Notification
from app.models.medicine import MedicineBatch
from app.models.medicine import Medicine

def scan_and_create_notifications(business_id):
    now = datetime.utcnow()
    # Expiry alerts
    for days in [7, 15, 30]:
        threshold = now + timedelta(days=days)
        batches = MedicineBatch.query.join(Medicine).filter(
            Medicine.business_id == business_id,
            MedicineBatch.expiry_date <= threshold,
            MedicineBatch.expiry_date >= now,
            MedicineBatch.quantity > 0,
            MedicineBatch.is_expired == False
        ).all()
        for b in batches:
            exists = Notification.query.filter_by(
                business_id=business_id,
                reference_type='batch',
                reference_id=b.id,
                type='expiry'
            ).first()
            if not exists:
                n = Notification(
                    business_id=business_id,
                    type='expiry',
                    priority='critical' if days <= 7 else ('high' if days <= 15 else 'medium'),
                    title=f'Expiry Alert: {b.medicine.name}',
                    message=f'Batch {b.batch_number} expires on {b.expiry_date.strftime("%d-%m-%Y")}. Qty: {b.quantity}',
                    reference_type='batch',
                    reference_id=b.id
                )
                db.session.add(n)
    # Low stock alerts
    medicines = Medicine.query.filter_by(business_id=business_id, is_active=True, is_deleted=False).all()
    for med in medicines:
        total_qty = sum(b.quantity for b in med.batches if not b.is_expired)
        if total_qty <= med.reorder_level:
            exists = Notification.query.filter_by(
                business_id=business_id, reference_type='medicine',
                reference_id=med.id, type='low_stock', is_read=False
            ).first()
            if not exists:
                n = Notification(
                    business_id=business_id,
                    type='low_stock',
                    priority='high',
                    title=f'Low Stock: {med.name}',
                    message=f'Current stock {total_qty} is at or below reorder level {med.reorder_level}.',
                    reference_type='medicine',
                    reference_id=med.id
                )
                db.session.add(n)
    db.session.commit()

def get_unread_count(user_id, business_id):
    return Notification.query.filter_by(
        business_id=business_id, is_read=False
    ).count()

def mark_read(notification_id, user_id):
    n = Notification.query.get(notification_id)
    if n:
        n.is_read = True
        db.session.commit()
