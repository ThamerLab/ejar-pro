"""Seed the database with demo data and default admin user."""
import json, os
from datetime import date, timedelta
from sqlalchemy.orm import Session
from .models import (User, Property, Unit, Tenant, Contract,
                     Payment, AppSetting)
from .auth import hash_password


def _today() -> str:
    return date.today().isoformat()


DEFAULT_TEMPLATES = {
    "reminder": """مرحباً {{tenant_name}}،

نودّ تذكيركم بأن دفعة الإيجار المستحقة على وحدة {{unit_number}} في {{property_name}} لم يتم سدادها بعد.

تفاصيل الدفعات المتأخرة:
{{installments_list}}

إجمالي المبلغ المستحق: {{total_overdue}}
عدد أيام التأخير: {{overdue_days}} يوم

رقم العقد: {{contract_number}}
رقم عقد إيجار: {{ejar_number}}

نأمل منكم التكرم بسداد المبلغ في أقرب وقت.

مع تحيات الإدارة""",
    "escalation": """تنبيه هام — {{tenant_name}}

لا يزال مبلغ الإيجار المستحق على وحدة {{unit_number}} في {{property_name}} غير مسدد.

إجمالي المبلغ المتأخر: {{total_overdue}}
عدد أيام التأخير: {{overdue_days}} يوم
تاريخ أقدم دفعة: {{oldest_due}}

{{installments_list}}

رقم العقد: {{contract_number}} | إيجار: {{ejar_number}}

استمرار التأخر قد يستوجب اتخاذ الإجراءات النظامية اللازمة.

يرجى التواصل فوراً.""",
    "receipt": """إيصال استلام دفعة — {{property_name}}

عزيزي {{tenant_name}}،

تم استلام دفعتكم بنجاح.

رقم الإيصال: {{receipt_number}}
المبلغ المدفوع: {{amount_paid}}
تاريخ الدفع: {{paid_date}}
الوحدة: {{unit_number}} — {{property_name}}
رقم العقد: {{contract_number}}

{{receipt_link}}

شكراً لكم. مع تحيات الإدارة""",
}

DEFAULT_TELEGRAM = {
    "bot_token": "",
    "chat_id": "",
    "alerts": {
        "overdue_new": True,
        "overdue_escalation": True,
        "payment_received": True,
        "contract_expiring": True,
    },
}


def seed(db: Session):
    # ---- Admin user ----
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    if not db.query(User).first():
        db.add(User(
            username=admin_user,
            full_name="المدير",
            hashed_pw=hash_password(admin_pass),
            role="admin",
        ))
        db.commit()

    # ---- Skip if data exists ----
    if db.query(Property).first():
        return

    # ---- Properties ----
    props = [
        Property(id="P001", name="برج النجد", city="الرياض", address="طريق الملك فهد", type="commercial"),
        Property(id="P002", name="مجمع الواحة", city="جدة", address="حي الروضة", type="residential"),
        Property(id="P003", name="أبراج الغدير", city="الدمام", address="الكورنيش", type="mixed"),
    ]
    db.add_all(props)

    # ---- Units ----
    units = [
        Unit(id="U001", property_id="P001", number="101", floor=1, type="office", area_m2=120),
        Unit(id="U002", property_id="P001", number="102", floor=1, type="office", area_m2=95),
        Unit(id="U003", property_id="P001", number="201", floor=2, type="office", area_m2=200),
        Unit(id="U004", property_id="P002", number="A1",  floor=0, type="apartment", area_m2=140),
        Unit(id="U005", property_id="P002", number="A2",  floor=0, type="apartment", area_m2=140),
        Unit(id="U006", property_id="P002", number="B1",  floor=1, type="apartment", area_m2=180),
        Unit(id="U007", property_id="P003", number="301", floor=3, type="retail", area_m2=60),
        Unit(id="U008", property_id="P003", number="302", floor=3, type="retail", area_m2=60),
    ]
    db.add_all(units)

    # ---- Tenants ----
    tenants = [
        Tenant(id="T001", name="محمد الرشيدي",        phone="0501234567", email="mrashidi@example.com",  id_number="1012345678"),
        Tenant(id="T002", name="شركة الفجر للتجارة",  phone="0556789012", email="info@alfajr.com",       id_number="7001234567"),
        Tenant(id="T003", name="سارة القحطاني",       phone="0509876543", email="sara.q@example.com",    id_number="1098765432"),
        Tenant(id="T004", name="أحمد العتيبي",        phone="0551122334", email="a.otaibi@example.com",  id_number="1055443322"),
        Tenant(id="T005", name="مؤسسة النور",         phone="0504455667", email="alnour@example.com",    id_number="7009988776"),
        Tenant(id="T006", name="خالد الدوسري",        phone="0507654321", email="k.dosari@example.com",  id_number="1076543210"),
    ]
    db.add_all(tenants)

    # ---- Contracts ----
    contracts = [
        Contract(id="C001", unit_id="U001", tenant_id="T001", ejar_number="EJR-2024-00881",
                 start_date="2024-01-01", end_date="2024-12-31", annual_rent=36000, installments=12, status="active"),
        Contract(id="C002", unit_id="U002", tenant_id="T002", ejar_number="EJR-2024-00912",
                 start_date="2024-03-01", end_date="2025-02-28", annual_rent=60000, installments=4,  status="active"),
        Contract(id="C003", unit_id="U004", tenant_id="T003", ejar_number="EJR-2024-01050",
                 start_date="2024-06-01", end_date="2025-05-31", annual_rent=48000, installments=12, status="active"),
        Contract(id="C004", unit_id="U005", tenant_id="T004", ejar_number="EJR-2023-00422",
                 start_date="2023-07-01", end_date="2024-06-30", annual_rent=42000, installments=12, status="expired"),
        Contract(id="C005", unit_id="U006", tenant_id="T005", ejar_number="EJR-2024-01200",
                 start_date="2024-09-01", end_date="2025-08-31", annual_rent=72000, installments=4,  status="active"),
        Contract(id="C006", unit_id="U007", tenant_id="T006", ejar_number="EJR-2024-01331",
                 start_date="2024-10-01", end_date="2025-09-30", annual_rent=30000, installments=12, status="active"),
    ]
    db.add_all(contracts)
    db.flush()

    # ---- Payments ----
    payments = [
        # C001 — 3000/mo
        Payment(id="PAY001", contract_id="C001", due_date="2024-01-01", amount_due=3000, amount_paid=3000, paid_date="2024-01-01", status="paid", receipt_number="RV-2024-001"),
        Payment(id="PAY002", contract_id="C001", due_date="2024-02-01", amount_due=3000, amount_paid=3000, paid_date="2024-02-03", status="paid", receipt_number="RV-2024-002"),
        Payment(id="PAY003", contract_id="C001", due_date="2024-03-01", amount_due=3000, amount_paid=3000, paid_date="2024-03-02", status="paid", receipt_number="RV-2024-003"),
        Payment(id="PAY004", contract_id="C001", due_date="2024-04-01", amount_due=3000, amount_paid=3000, paid_date="2024-04-01", status="paid", receipt_number="RV-2024-004"),
        Payment(id="PAY005", contract_id="C001", due_date="2024-05-01", amount_due=3000, amount_paid=3000, paid_date="2024-05-04", status="paid", receipt_number="RV-2024-005"),
        Payment(id="PAY006", contract_id="C001", due_date="2024-06-01", amount_due=3000, amount_paid=3000, paid_date="2024-06-02", status="paid", receipt_number="RV-2024-006"),
        Payment(id="PAY007", contract_id="C001", due_date="2024-07-01", amount_due=3000, amount_paid=3000, paid_date="2024-07-03", status="paid", receipt_number="RV-2024-007"),
        Payment(id="PAY008", contract_id="C001", due_date="2024-08-01", amount_due=3000, amount_paid=3000, paid_date="2024-08-01", status="paid", receipt_number="RV-2024-008"),
        Payment(id="PAY009", contract_id="C001", due_date="2024-09-01", amount_due=3000, amount_paid=3000, paid_date="2024-09-05", status="paid", receipt_number="RV-2024-009"),
        Payment(id="PAY010", contract_id="C001", due_date="2024-10-01", amount_due=3000, amount_paid=3000, paid_date="2024-10-02", status="paid", receipt_number="RV-2024-010"),
        Payment(id="PAY011", contract_id="C001", due_date="2024-11-01", amount_due=3000, amount_paid=1500, paid_date="2024-11-10", status="partial", receipt_number="RV-2024-011"),
        Payment(id="PAY012", contract_id="C001", due_date="2024-12-01", amount_due=3000, amount_paid=0,    paid_date=None,         status="overdue"),
        # C002 — 15000/qtr
        Payment(id="PAY013", contract_id="C002", due_date="2024-03-01", amount_due=15000, amount_paid=15000, paid_date="2024-03-01", status="paid", receipt_number="RV-2024-012"),
        Payment(id="PAY014", contract_id="C002", due_date="2024-06-01", amount_due=15000, amount_paid=15000, paid_date="2024-06-03", status="paid", receipt_number="RV-2024-013"),
        Payment(id="PAY015", contract_id="C002", due_date="2024-09-01", amount_due=15000, amount_paid=15000, paid_date="2024-09-10", status="paid", receipt_number="RV-2024-014"),
        Payment(id="PAY016", contract_id="C002", due_date="2024-12-01", amount_due=15000, amount_paid=0,     paid_date=None,         status="overdue"),
        # C003 — 4000/mo
        Payment(id="PAY017", contract_id="C003", due_date="2024-06-01", amount_due=4000, amount_paid=4000, paid_date="2024-06-01", status="paid", receipt_number="RV-2024-015"),
        Payment(id="PAY018", contract_id="C003", due_date="2024-07-01", amount_due=4000, amount_paid=4000, paid_date="2024-07-04", status="paid", receipt_number="RV-2024-016"),
        Payment(id="PAY019", contract_id="C003", due_date="2024-08-01", amount_due=4000, amount_paid=4000, paid_date="2024-08-02", status="paid", receipt_number="RV-2024-017"),
        Payment(id="PAY020", contract_id="C003", due_date="2024-09-01", amount_due=4000, amount_paid=4000, paid_date="2024-09-01", status="paid", receipt_number="RV-2024-018"),
        Payment(id="PAY021", contract_id="C003", due_date="2024-10-01", amount_due=4000, amount_paid=4000, paid_date="2024-10-06", status="paid", receipt_number="RV-2024-019"),
        Payment(id="PAY022", contract_id="C003", due_date="2024-11-01", amount_due=4000, amount_paid=2000, paid_date="2024-11-20", status="partial", receipt_number="RV-2024-020"),
        Payment(id="PAY023", contract_id="C003", due_date="2024-12-01", amount_due=4000, amount_paid=0,    paid_date=None,         status="overdue"),
        # C005 — 18000/qtr
        Payment(id="PAY024", contract_id="C005", due_date="2024-09-01", amount_due=18000, amount_paid=18000, paid_date="2024-09-01", status="paid", receipt_number="RV-2024-021"),
        Payment(id="PAY025", contract_id="C005", due_date="2024-12-01", amount_due=18000, amount_paid=0,     paid_date=None,         status="overdue"),
        # C006 — 2500/mo
        Payment(id="PAY026", contract_id="C006", due_date="2024-10-01", amount_due=2500, amount_paid=2500, paid_date="2024-10-01", status="paid", receipt_number="RV-2024-022"),
        Payment(id="PAY027", contract_id="C006", due_date="2024-11-01", amount_due=2500, amount_paid=2500, paid_date="2024-11-03", status="paid", receipt_number="RV-2024-023"),
        Payment(id="PAY028", contract_id="C006", due_date="2024-12-01", amount_due=2500, amount_paid=0,    paid_date=None,         status="overdue"),
    ]
    db.add_all(payments)

    # ---- App settings ----
    db.add(AppSetting(key="templates",     value=json.dumps(DEFAULT_TEMPLATES, ensure_ascii=False)))
    db.add(AppSetting(key="telegram",      value=json.dumps(DEFAULT_TELEGRAM)))
    db.add(AppSetting(key="receipt_seq",   value="24"))
    db.add(AppSetting(key="prop_seq",      value="4"))
    db.add(AppSetting(key="unit_seq",      value="9"))
    db.add(AppSetting(key="tenant_seq",    value="7"))
    db.add(AppSetting(key="contract_seq",  value="7"))
    db.add(AppSetting(key="payment_seq",   value="29"))

    db.commit()
