let cart = [];
let lastAddedIndex = -1;
let selectedMode = 'cash';
let lastInteractions = [];
let interactionOverrideReason = '';

// Medicine search
const searchInput = document.getElementById('medicineSearch');
const dropdown = document.getElementById('searchDropdown');
let searchTimer;

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  const q = searchInput.value.trim();
  if (q.length < 2) { dropdown.style.display = 'none'; return; }
  searchTimer = setTimeout(() => {
    fetch(`/sales/api/medicine-search?q=${encodeURIComponent(q)}`)
      .then(r => r.json()).then(data => showDropdown(data));
  }, 300);
});

function showDropdown(meds) {
  if (!meds.length) { dropdown.style.display = 'none'; return; }
  dropdown.innerHTML = meds.map(m => {
    const stockBadge = m.batches.length ? `<span class="badge bg-success ms-1">${m.batches.reduce((s,b)=>s+b.available_qty,0)}</span>` : `<span class="badge bg-danger ms-1">Out</span>`;
    const schedBadge = m.schedule_type !== 'OTC' ? `<span class="badge bg-warning text-dark ms-1">${m.schedule_type}</span>` : '';
    return `<div class="px-3 py-2 border-bottom" style="cursor:pointer" onmousedown="addToCart(${JSON.stringify(m).replace(/"/g,'&quot;')})">`+
      `<strong>${m.name}</strong>${schedBadge}${stockBadge}`+
      `<div class="small text-muted">${m.generic_name || ''}</div></div>`;
  }).join('');
  const rect = searchInput.getBoundingClientRect();
  dropdown.style.top = (rect.bottom + window.scrollY) + 'px';
  dropdown.style.left = rect.left + 'px';
  dropdown.style.display = 'block';
}

document.addEventListener('click', e => { if (!dropdown.contains(e.target)) dropdown.style.display = 'none'; });

function addToCart(med) {
  dropdown.style.display = 'none';
  searchInput.value = '';
  if (!med.batches.length) { alert('No stock available for ' + med.name); return; }
  const batch = med.batches[0];
  const item = {
    medicine_id: med.id, medicine_name: med.name, generic_name: med.generic_name,
    batch_id: batch.id, batch_number: batch.batch_number, expiry_date: batch.expiry_date,
    available_qty: batch.available_qty, selling_rate: batch.selling_rate, mrp: batch.mrp,
    gst_rate: med.gst_rate, discount_pct: 0, qty: 1,
    prescription_req: med.prescription_req, schedule_type: med.schedule_type
  };
  cart.push(item);
  lastAddedIndex = cart.length - 1;
  renderCart();
  checkInteractions();
}

function removeLastAdded() { if (lastAddedIndex >= 0) { cart.splice(lastAddedIndex, 1); lastAddedIndex = -1; renderCart(); }}
function removeItem(idx) { cart.splice(idx, 1); renderCart(); checkInteractions(); }

function renderCart() {
  const tbody = document.getElementById('cartBody');
  const empty = document.getElementById('emptyRow');
  if (!cart.length) { tbody.innerHTML = '<tr id="emptyRow"><td colspan="10" class="text-center text-muted py-4">Search and add medicines above</td></tr>'; updateTotals(); return; }
  tbody.innerHTML = cart.map((item, i) => `
    <tr>
      <td><strong>${item.medicine_name}</strong><div class="small text-muted">${item.generic_name||''}</div></td>
      <td><span class="badge bg-light text-dark border">${item.batch_number}</span></td>
      <td class="small">${item.expiry_date}</td>
      <td><input type="number" class="form-control form-control-sm" value="${item.qty}" min="1" max="${item.available_qty}" onchange="updateQty(${i},this.value)" style="width:65px"></td>
      <td class="small">₹${item.mrp.toFixed(2)}</td>
      <td class="small">₹${item.selling_rate.toFixed(2)}</td>
      <td><input type="number" class="form-control form-control-sm" value="${item.discount_pct}" min="0" max="100" onchange="updateDisc(${i},this.value)" style="width:60px"></td>
      <td class="small">${item.gst_rate}%</td>
      <td class="small fw-semibold">₹${lineTotal(item).toFixed(2)}</td>
      <td><button class="btn btn-sm btn-outline-danger" onclick="removeItem(${i})">✕</button></td>
    </tr>`).join('');
  updateTotals();
}

function lineTotal(item) {
  const base = item.selling_rate * item.qty;
  const disc = base * item.discount_pct / 100;
  const taxable = base - disc;
  return taxable * (1 + item.gst_rate / 100);
}

function updateQty(i, val) { cart[i].qty = Math.min(parseInt(val)||1, cart[i].available_qty); renderCart(); }
function updateDisc(i, val) { cart[i].discount_pct = parseFloat(val)||0; renderCart(); }

function updateTotals() {
  let subtotal = 0, cgst = 0, sgst = 0;
  cart.forEach(item => {
    const base = item.selling_rate * item.qty;
    const disc = base * item.discount_pct / 100;
    const taxable = base - disc;
    subtotal += taxable;
    const half = taxable * (item.gst_rate / 2) / 100;
    cgst += half; sgst += half;
  });
  const invDisc = parseFloat(document.getElementById('invoiceDisc').value)||0;
  const discAmt = subtotal * invDisc / 100;
  const grand = subtotal - discAmt + cgst + sgst;
  document.getElementById('subtotal').textContent = '₹' + subtotal.toFixed(2);
  document.getElementById('discAmount').textContent = '-₹' + discAmt.toFixed(2);
  document.getElementById('cgstTotal').textContent = '₹' + cgst.toFixed(2);
  document.getElementById('sgstTotal').textContent = '₹' + sgst.toFixed(2);
  document.getElementById('grandTotal').textContent = '₹' + grand.toFixed(2);
  const tendered = parseFloat(document.getElementById('cashTendered').value)||0;
  document.getElementById('changeAmt').textContent = '₹' + Math.max(0, tendered - grand).toFixed(2);
}

document.getElementById('invoiceDisc').addEventListener('input', updateTotals);
document.getElementById('cashTendered').addEventListener('input', updateTotals);

// Payment mode toggle
document.getElementById('paymentMode').querySelectorAll('button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#paymentMode button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedMode = btn.dataset.mode;
    document.getElementById('cashFields').style.display = selectedMode === 'cash' ? 'block' : 'none';
  });
});

function checkInteractions() {
  if (cart.length < 2) return;
  const ids = cart.map(i => i.medicine_id);
  fetch('/sales/api/check-interaction', {
    method: 'POST', headers: {'Content-Type':'application/json', 'X-CSRFToken': getCsrf()},
    body: JSON.stringify({medicine_ids: ids})
  }).then(r => r.json()).then(data => {
    lastInteractions = data;
    if (data.length) {
      interactionOverrideReason = '';
      const hasSevere = data.some(d => d.severity === 'major' || d.severity === 'contraindicated');
      document.getElementById('interactionBody').innerHTML = data.map(d =>
        `<div class="alert alert-${d.severity==='contraindicated'?'danger':d.severity==='major'?'danger':'warning'} py-2">
          <strong>${d.drug_a} + ${d.drug_b}</strong> — <span class="badge bg-danger">${d.severity}</span>
          <div class="small mt-1">${d.description}</div></div>`
      ).join('');
      document.getElementById('overrideReasonWrap').classList.toggle('d-none', !hasSevere);
      document.getElementById('overrideReason').value = '';
      new bootstrap.Modal(document.getElementById('interactionModal')).show();
    }
  });
}

function hasUnresolvedSevereInteraction() {
  const severe = lastInteractions.filter(d => d.severity === 'major' || d.severity === 'contraindicated');
  return severe.length > 0 && !interactionOverrideReason;
}

document.getElementById('overrideContinueBtn').addEventListener('click', () => {
  const reason = document.getElementById('overrideReason').value.trim();
  const wrapVisible = !document.getElementById('overrideReasonWrap').classList.contains('d-none');
  if (wrapVisible && !reason) { alert('Please enter an override reason.'); return; }
  interactionOverrideReason = reason;
  bootstrap.Modal.getInstance(document.getElementById('interactionModal'))?.hide();
});

function generateInvoice() {
  if (!cart.length) { alert('Cart is empty'); return; }
  if (hasUnresolvedSevereInteraction()) {
    new bootstrap.Modal(document.getElementById('interactionModal')).show();
    return;
  }
  const grand = parseFloat(document.getElementById('grandTotal').textContent.replace('₹',''));
  const btn = document.getElementById('generateBtn');
  btn.disabled = true; btn.textContent = 'Processing...';
  const payload = {
    patient_id: document.getElementById('patientSelect').value || null,
    payment_mode: selectedMode,
    paid_amount: selectedMode === 'cash' ? (parseFloat(document.getElementById('cashTendered').value)||grand) : grand,
    discount_amount: grand * (parseFloat(document.getElementById('invoiceDisc').value)||0) / 100,
    override_reason: interactionOverrideReason || undefined,
    items: cart.map(item => ({
      medicine_id: item.medicine_id, batch_id: item.batch_id,
      batch_number: item.batch_number, qty: item.qty,
      selling_rate: item.selling_rate, mrp: item.mrp,
      gst_rate: item.gst_rate, discount_pct: item.discount_pct
    }))
  };
  fetch('/sales/billing/save', {
    method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken':getCsrf()},
    body: JSON.stringify(payload)
  }).then(r => r.json()).then(data => {
    if (data.error) { alert(data.error); btn.disabled = false; btn.textContent = 'Generate Invoice'; return; }
    window.open(data.pdf_url || `/sales/${data.sale_id}/invoice`, '_blank');
    cart = []; renderCart();
    btn.disabled = false; btn.textContent = 'Generate Invoice';
    document.getElementById('patientSelect').value = '';
  }).catch(() => { btn.disabled = false; btn.textContent = 'Generate Invoice'; });
}

function getCsrf() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}
