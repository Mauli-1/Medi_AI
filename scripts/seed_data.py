"""Run: python scripts/seed_data.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db, bcrypt
from app.models.business import Business
from app.models.branch import Branch
from app.models.user import User
from app.models.medicine import Medicine, MedicineCategory, MedicineBatch
from app.models.supplier import Supplier
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.drug_interaction import DrugInteraction
from datetime import date, timedelta

app = create_app('development')

with app.app_context():
    db.create_all()
    print("Tables created.")

    if Business.query.first():
        print("Seed data already exists. Skipping.")
        sys.exit(0)

    # Business
    biz = Business(
        name="Sai Medical Store",
        legal_name="Sai Medical Store",
        gstin="27AAPFU0939F1ZV",
        drug_license_no="MH-MUM-123456",
        phone="9876543210",
        email="sai.medical@gmail.com",
        address_line1="Shop No 12, MG Road",
        state="Maharashtra",
        city="Mumbai",
        pincode="400001",
        setup_complete=True,
        is_gst_registered=True
    )
    db.session.add(biz)
    db.session.flush()

    # Branch
    branch = Branch(business_id=biz.id, name="Main Branch", code="BR001", address_line1="Shop No 12, MG Road", phone="9876543210", is_headquarters=True, is_active=True)
    db.session.add(branch)
    db.session.flush()

    # Users
    users = [
        ("admin", "Admin User", "admin@sai.com", "Admin@123", "super_admin"),
        ("owner1", "Sai Owner", "owner@sai.com", "Owner@123", "owner"),
        ("pharmacist1", "Raj Sharma", "raj@sai.com", "Pharma@123", "pharmacist"),
        ("cashier1", "Priya Patel", "priya@sai.com", "Cash@123", "cashier"),
        ("manager1", "Amit Singh", "amit@sai.com", "Manager@123", "store_manager"),
        ("auditor1", "Neha Auditor", "auditor@sai.com", "Audit@123", "auditor"),
    ]
    for uname, fname, email, pwd, role in users:
        u = User(branch_id=branch.id, username=uname, full_name=fname, email=email, role=role, is_active=True)
        u.set_password(pwd)
        db.session.add(u)

    # Categories
    cats = {}
    for cname in ['Analgesic', 'Antibiotic', 'Antidiabetic', 'Cardiac', 'Antidepressant', 'Vitamin', 'Antacid']:
        c = MedicineCategory(business_id=biz.id, name=cname)
        db.session.add(c)
        db.session.flush()
        cats[cname] = c.id

    # Medicines
    meds_data = [
        ("Paracetamol 500mg", "Paracetamol", "Crocin", "Paracetamol 500mg", "Analgesic", "GSK", "30049099", "OTC", 12, 25, 18, 22),
        ("Amoxicillin 250mg", "Amoxicillin", "Mox", "Amoxicillin 250mg", "Antibiotic", "Cipla", "30041020", "H", 12, 85, 65, 75),
        ("Metformin 500mg", "Metformin", "Glycomet", "Metformin 500mg", "Antidiabetic", "USV", "30049099", "H", 12, 45, 30, 38),
        ("Atorvastatin 10mg", "Atorvastatin", "Lipitor", "Atorvastatin 10mg", "Cardiac", "Pfizer", "30049099", "H", 12, 120, 90, 105),
        ("Alprazolam 0.25mg", "Alprazolam", "Alprax", "Alprazolam 0.25mg", "Antidepressant", "Sun Pharma", "30049099", "X", 12, 60, 45, 55),
        ("Omeprazole 20mg", "Omeprazole", "Omez", "Omeprazole 20mg", "Antacid", "Dr Reddy's", "30049099", "H", 12, 55, 40, 48),
        ("Vitamin D3 1000IU", "Cholecalciferol", "D3-Must", "Cholecalciferol 1000IU", "Vitamin", "Mankind", "30049099", "OTC", 12, 180, 130, 160),
        ("Cetirizine 10mg", "Cetirizine", "Zyrtec", "Cetirizine 10mg", "Analgesic", "UCB", "30049099", "OTC", 5, 35, 22, 30),
        ("Azithromycin 500mg", "Azithromycin", "Azee", "Azithromycin 500mg", "Antibiotic", "Cipla", "30041020", "H", 12, 95, 72, 85),
        ("Pantoprazole 40mg", "Pantoprazole", "Pan 40", "Pantoprazole 40mg", "Antacid", "Alkem", "30049099", "H", 12, 65, 48, 58),
    ]
    med_objs = []
    for i, (name, generic, brand, salt, cat, mfr, hsn, sched, gst, mrp, pr, sr) in enumerate(meds_data):
        m = Medicine(
            business_id=biz.id,
            medicine_code=f"MED-{i+1:04d}",
            name=name, generic_name=generic, brand_name=brand, salt_composition=salt,
            category_id=cats.get(cat), manufacturer=mfr, hsn_code=hsn,
            schedule_type=sched, gst_rate=gst, mrp=mrp, purchase_rate=pr, selling_rate=sr,
            prescription_req=(sched in ('H','H1','X')),
            narcotic_flag=(sched == 'X'),
            reorder_level=20, max_stock_level=500, is_active=True
        )
        db.session.add(m)
        db.session.flush()
        med_objs.append(m)
        # Batches
        for j in range(2):
            exp = date.today() + timedelta(days=365 - j*90)
            b = MedicineBatch(
                medicine_id=m.id, branch_id=branch.id,
                batch_number=f"B{i+1:02d}{j+1:02d}",
                mfg_date=date.today() - timedelta(days=180),
                expiry_date=exp,
                quantity=100 - j*30,
                purchase_rate=pr, mrp=mrp, selling_rate=sr
            )
            db.session.add(b)

    # Suppliers
    for sname, code, phone, gst in [
        ("Sun Pharma", "SUP-0001", "9811234567", "24ABCDE1234F1Z5"),
        ("Cipla Ltd", "SUP-0002", "9822345678", "27FGHIJ5678G2Z6"),
        ("Medley Pharma", "SUP-0003", "9833456789", "29KLMNO9012H3Z7"),
    ]:
        s = Supplier(business_id=biz.id, supplier_code=code, name=sname, phone=phone, gst_number=gst, payment_terms=30, is_active=True)
        db.session.add(s)

    # Doctors
    for dname, code, spec, reg in [
        ("Dr. Ramesh Sharma", "DOC-0001", "Cardiology", "MH-12345"),
        ("Dr. Anjali Patel", "DOC-0002", "General Physician", "MH-67890"),
    ]:
        d = Doctor(business_id=biz.id, doctor_code=code, full_name=dname, specialization=spec, registration_no=reg, is_active=True)
        db.session.add(d)

    # Patients
    for pname, code, phone in [
        ("Ramesh Kumar", "PAT-0001", "9900001111"),
        ("Sunita Devi", "PAT-0002", "9900002222"),
        ("Vikram Singh", "PAT-0003", "9900003333"),
        ("Meena Shah", "PAT-0004", "9900004444"),
        ("Arun Joshi", "PAT-0005", "9900005555"),
    ]:
        p = Patient(business_id=biz.id, patient_code=code, full_name=pname, phone=phone, gender='male', is_active=True)
        db.session.add(p)

    # Drug interactions
    interactions = [
        ("Warfarin", "Aspirin", "major", "Increased bleeding risk. Avoid combination."),
        ("Metformin", "Alcohol", "moderate", "Increased risk of lactic acidosis."),
        ("Alprazolam", "Alcohol", "contraindicated", "CNS depression, respiratory failure risk."),
        ("Atorvastatin", "Erythromycin", "moderate", "Increased statin levels, myopathy risk."),
        ("Amoxicillin", "Warfarin", "moderate", "May enhance anticoagulant effect."),
    ]
    for da, db_, sev, desc in interactions:
        di = DrugInteraction(drug_a_generic=da, drug_b_generic=db_, severity=sev, description=desc, source='WHO')
        db.session.add(di)

    db.session.commit()
    print("\n✅ Seed data created successfully!")
    print("=" * 40)
    print("Login URL : http://localhost:5000/auth/login")
    print("Username  : admin")
    print("Password  : Admin@123")
    print("=" * 40)
    print("Other users: owner1/Owner@123, pharmacist1/Pharma@123, cashier1/Cash@123, manager1/Manager@123, auditor1/Audit@123")
