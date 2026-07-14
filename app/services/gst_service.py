from app.utils.helpers import get_state_from_gstin

def get_supply_type(business_gstin, customer_gstin=None):
    if not customer_gstin:
        return 'intra'
    b_state = business_gstin[:2] if business_gstin else '27'
    c_state = customer_gstin[:2] if customer_gstin else '27'
    return 'intra' if b_state == c_state else 'inter'

def calculate_line_gst(selling_rate, qty, discount_pct, gst_rate, supply_type='intra'):
    line_amount = float(selling_rate) * int(qty)
    discount = line_amount * float(discount_pct) / 100
    taxable_value = line_amount - discount
    gst_rate = float(gst_rate)
    half_rate = gst_rate / 2
    if supply_type == 'intra':
        cgst = round(taxable_value * half_rate / 100, 2)
        sgst = round(taxable_value * half_rate / 100, 2)
        igst = 0.0
    else:
        cgst = 0.0
        sgst = 0.0
        igst = round(taxable_value * gst_rate / 100, 2)
    total = round(taxable_value + cgst + sgst + igst, 2)
    return {
        'taxable_value': round(taxable_value, 2),
        'cgst_rate': half_rate if supply_type == 'intra' else 0,
        'cgst_amount': cgst,
        'sgst_rate': half_rate if supply_type == 'intra' else 0,
        'sgst_amount': sgst,
        'igst_rate': gst_rate if supply_type == 'inter' else 0,
        'igst_amount': igst,
        'total': total,
    }

def calculate_invoice_gst(items, supply_type='intra'):
    totals = {'subtotal': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'total': 0}
    for item in items:
        g = calculate_line_gst(item['selling_rate'], item['qty'], item.get('discount_pct', 0), item['gst_rate'], supply_type)
        totals['subtotal'] += g['taxable_value']
        totals['cgst'] += g['cgst_amount']
        totals['sgst'] += g['sgst_amount']
        totals['igst'] += g['igst_amount']
        totals['total'] += g['total']
    return {k: round(v, 2) for k, v in totals.items()}
