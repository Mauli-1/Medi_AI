from app.extensions import db
from app.models.loyalty import LoyaltyProgram, LoyaltyTransaction


def award_points_for_sale(sale):
    if not sale.patient_id:
        return None
    from app.models.patient import Patient
    patient = Patient.query.get(sale.patient_id)
    if not patient:
        return None
    program = LoyaltyProgram.query.filter_by(business_id=sale.business_id, is_active=True).first()
    if not program:
        return None

    patient.total_purchases = (patient.total_purchases or 0) + sale.total_amount
    tier = program.tier_for_spend(patient.total_purchases)
    patient.loyalty_tier = tier

    points = int(float(sale.total_amount) * float(program.points_per_rupee or 0))
    if points > 0:
        patient.loyalty_points = (patient.loyalty_points or 0) + points
        db.session.add(LoyaltyTransaction(
            patient_id=patient.id, sale_id=sale.id, type='earn', points=points,
            balance=patient.loyalty_points, notes=f'Earned on invoice {sale.invoice_number}',
        ))

    cashback_pct = program.cashback_pct_for_tier(tier)
    cashback_amount = round(float(sale.total_amount) * cashback_pct / 100, 2)
    if cashback_amount > 0:
        cashback_points = int(cashback_amount)
        patient.loyalty_points = (patient.loyalty_points or 0) + cashback_points
        db.session.add(LoyaltyTransaction(
            patient_id=patient.id, sale_id=sale.id, type='cashback', points=cashback_points,
            balance=patient.loyalty_points, notes=f'{cashback_pct}% cashback on invoice {sale.invoice_number}',
        ))

    db.session.commit()
    return patient
