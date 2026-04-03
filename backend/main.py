"""
إيجار Pro — FastAPI Backend
All API routes + static file serving
"""
from __future__ import annotations
import json, os, secrets
from datetime import date, datetime
from typing import Optional

from fastapi import (FastAPI, Depends, HTTPException, Request, Response,
                     Form, UploadFile, File)
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine, get_db, Base
from .models import (User, Property, Unit, Tenant, Contract,
                     Payment, ReceiptToken, FollowupLog, AppSetting)
from .auth import (hash_password, verify_password, create_session_cookie,
                   get_current_user, require_admin, COOKIE_NAME, SESSION_MAX_AGE)
from .seed import seed

# ── Bootstrap ────────────────────────────────────────────────────────────────
os.makedirs("/data", exist_ok=True)
Base.metadata.create_all(bind=engine)

from .database import SessionLocal as _SL
with _SL() as _s:
    seed(_s)

app = FastAPI(title="إيجار Pro", docs_url=None, redoc_url=None)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# ── Helpers ───────────────────────────────────────────────────────────────────
def today() -> str:
    return date.today().isoformat()

def get_seq(db: Session, key: str) -> int:
    row = db.get(AppSetting, key)
    val = int(row.value) if row else 1
    if not row:
        db.add(AppSetting(key=key, value=str(val + 1)))
    else:
        row.value = str(val + 1)
    db.commit()
    return val

def next_receipt(db: Session) -> str:
    seq = get_seq(db, "receipt_seq")
    return f"RV-{date.today().year}-{seq:03d}"

def days_diff(from_str: str, to_str: str) -> int:
    a = date.fromisoformat(from_str)
    b = date.fromisoformat(to_str)
    return (b - a).days

def is_overdue(p: Payment) -> bool:
    if p.deleted or p.status == "paid":
        return False
    remaining = p.amount_due - (p.amount_paid or 0)
    if remaining <= 0:
        return False
    return days_diff(p.due_date, today()) >= 1

def overdue_days(p: Payment) -> int:
    if not is_overdue(p):
        return 0
    return days_diff(p.due_date, today())

def get_active_contract(db: Session, unit_id: str) -> Optional[Contract]:
    return db.query(Contract).filter_by(
        unit_id=unit_id, status="active", archived=False, deleted=False
    ).first()

def get_setting(db: Session, key: str, default=None):
    row = db.get(AppSetting, key)
    return json.loads(row.value) if row else default

def set_setting(db: Session, key: str, value):
    row = db.get(AppSetting, key)
    if row:
        row.value = json.dumps(value, ensure_ascii=False)
    else:
        db.add(AppSetting(key=key, value=json.dumps(value, ensure_ascii=False)))
    db.commit()

def contract_to_dict(c: Contract) -> dict:
    return {
        "id": c.id, "unit_id": c.unit_id, "tenant_id": c.tenant_id,
        "ejar_number": c.ejar_number, "start_date": c.start_date,
        "end_date": c.end_date, "annual_rent": c.annual_rent,
        "installments": c.installments, "installment_day": c.installment_day,
        "status": c.status, "archived": c.archived, "deleted": c.deleted,
        "archived_at": c.archived_at,
    }

def payment_to_dict(p: Payment) -> dict:
    return {
        "id": p.id, "contract_id": p.contract_id, "due_date": p.due_date,
        "amount_due": p.amount_due, "amount_paid": p.amount_paid or 0,
        "paid_date": p.paid_date, "status": p.status,
        "receipt_number": p.receipt_number,
        "deleted": p.deleted, "deleted_at": p.deleted_at,
    }

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/demo-terms", response_class=HTMLResponse)
async def demo_terms_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "demo-terms.html"))

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "demo.html"))

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        from .auth import decode_session_cookie
        data = decode_session_cookie(token)
        if data:
            return RedirectResponse("/app")
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/app", response_class=HTMLResponse)
async def app_page(user: User = Depends(get_current_user)):
    return FileResponse(os.path.join(FRONTEND_DIR, "app.html"))

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "demo.html"))

@app.get("/demo-app", response_class=HTMLResponse)
async def demo_app_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "demo-app.html"))

@app.post("/api/auth/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(username=username, is_active=True).first()
    if not user or not verify_password(password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    cookie = create_session_cookie(user.id)
    response.set_cookie(
        COOKIE_NAME, cookie,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True, "role": user.role, "full_name": user.full_name}

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}

@app.get("/api/auth/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username,
            "full_name": user.full_name, "role": user.role}

# ── Users (admin only) ────────────────────────────────────────────────────────
@app.get("/api/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return [{"id": u.id, "username": u.username, "full_name": u.full_name,
             "role": u.role, "is_active": u.is_active} for u in db.query(User).all()]

@app.post("/api/users")
def create_user(
    username: str = Form(...), full_name: str = Form(...),
    password: str = Form(...), role: str = Form("viewer"),
    db: Session = Depends(get_db), admin: User = Depends(require_admin),
):
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(400, "اسم المستخدم موجود مسبقاً")
    u = User(username=username, full_name=full_name,
             hashed_pw=hash_password(password), role=role)
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "username": u.username, "role": u.role}

@app.delete("/api/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "مستخدم غير موجود")
    u.is_active = False
    db.commit()
    return {"ok": True}

@app.post("/api/users/{uid}/password")
def change_password(
    uid: int, new_password: str = Form(...),
    db: Session = Depends(get_db), admin: User = Depends(require_admin),
):
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404)
    u.hashed_pw = hash_password(new_password)
    db.commit()
    return {"ok": True}

# ── Properties ────────────────────────────────────────────────────────────────
@app.get("/api/properties")
def list_properties(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [{"id": p.id, "name": p.name, "city": p.city,
             "address": p.address, "type": p.type} for p in db.query(Property).all()]

@app.post("/api/properties")
def create_property(
    name: str = Form(...), city: str = Form(""), address: str = Form(""), type: str = Form("residential"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    seq = get_seq(db, "prop_seq")
    pid = f"P{seq:03d}"
    db.add(Property(id=pid, name=name, city=city, address=address, type=type))
    db.commit()
    return {"id": pid}

# ── Units ─────────────────────────────────────────────────────────────────────
@app.get("/api/units")
def list_units(property_id: str = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Unit).filter_by(deleted=False)
    if property_id:
        q = q.filter_by(property_id=property_id)
    return [{"id": u.id, "property_id": u.property_id, "number": u.number,
             "floor": u.floor, "type": u.type, "area_m2": u.area_m2,
             "deleted": u.deleted} for u in q.all()]

@app.post("/api/units")
def create_unit(
    property_id: str = Form(...), number: str = Form(...),
    floor: int = Form(0), type: str = Form("office"), area_m2: float = Form(0),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    seq = get_seq(db, "unit_seq")
    uid = f"U{seq:03d}"
    db.add(Unit(id=uid, property_id=property_id, number=number,
                floor=floor, type=type, area_m2=area_m2))
    db.commit()
    return {"id": uid}

# ── Tenants ───────────────────────────────────────────────────────────────────
@app.get("/api/tenants")
def list_tenants(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [{"id": t.id, "name": t.name, "phone": t.phone,
             "email": t.email, "id_number": t.id_number,
             "deleted": t.deleted} for t in db.query(Tenant).filter_by(deleted=False).all()]

@app.post("/api/tenants")
def create_tenant(
    name: str = Form(...), phone: str = Form(""), email: str = Form(""), id_number: str = Form(""),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    seq = get_seq(db, "tenant_seq")
    tid = f"T{seq:03d}"
    db.add(Tenant(id=tid, name=name, phone=phone, email=email, id_number=id_number))
    db.commit()
    return {"id": tid}

# ── Contracts ─────────────────────────────────────────────────────────────────
@app.get("/api/contracts")
def list_contracts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Contract).filter_by(deleted=False)
    return [contract_to_dict(c) for c in q.all()]

@app.post("/api/contracts")
def create_contract(
    unit_id: str = Form(...), tenant_id: str = Form(...),
    ejar_number: str = Form(""), start_date: str = Form(...), end_date: str = Form(...),
    annual_rent: float = Form(...), installments: int = Form(12),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    if get_active_contract(db, unit_id):
        raise HTTPException(400, "الوحدة لديها عقد نشط بالفعل")
    seq = get_seq(db, "contract_seq")
    cid = f"C{seq:03d}"
    c = Contract(id=cid, unit_id=unit_id, tenant_id=tenant_id,
                 ejar_number=ejar_number, start_date=start_date, end_date=end_date,
                 annual_rent=annual_rent, installments=installments)
    db.add(c)
    db.flush()

    # Generate installment payments
    amt = annual_rent / installments
    start = date.fromisoformat(start_date)
    end   = date.fromisoformat(end_date)
    months_total = max(1, round((end - start).days / 30))
    interval = max(1, round(months_total / installments))

    for i in range(installments):
        due = date(start.year, start.month, start.day)
        month = start.month - 1 + i * interval
        due = due.replace(year=start.year + month // 12, month=month % 12 + 1)
        due_str = due.isoformat()
        seq2 = get_seq(db, "payment_seq")
        db.add(Payment(
            id=f"PAY{seq2:03d}", contract_id=cid, due_date=due_str,
            amount_due=amt, amount_paid=0,
            status="overdue" if due_str < today() else "pending",
        ))
    db.commit()
    return {"id": cid}

@app.post("/api/contracts/{cid}/archive")
def archive_contract(cid: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    c = db.get(Contract, cid)
    if not c:
        raise HTTPException(404)
    c.archived = True; c.archived_at = today()
    db.commit()
    return {"ok": True}

@app.post("/api/contracts/{cid}/unarchive")
def unarchive_contract(cid: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    c = db.get(Contract, cid)
    if not c:
        raise HTTPException(404)
    c.archived = False; c.archived_at = None
    db.commit()
    return {"ok": True}

# ── Payments ──────────────────────────────────────────────────────────────────
@app.get("/api/payments")
def list_payments(contract_id: str = None, include_deleted: bool = False,
                  db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Payment)
    if not include_deleted:
        q = q.filter_by(deleted=False)
    if contract_id:
        q = q.filter_by(contract_id=contract_id)
    return [payment_to_dict(p) for p in q.order_by(Payment.due_date).all()]

@app.post("/api/payments/{pid}/record")
def record_payment(
    pid: str,
    amount_paid: float = Form(...),
    paid_date: str = Form(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    p = db.get(Payment, pid)
    if not p:
        raise HTTPException(404)
    remaining = p.amount_due - (p.amount_paid or 0)
    if amount_paid <= 0:
        raise HTTPException(400, "المبلغ يجب أن يكون أكبر من صفر")
    if amount_paid > remaining:
        raise HTTPException(400, f"المبلغ يتجاوز المتبقي ({remaining:.0f} ر.س). الدفع الزائد غير مسموح.")
    p.amount_paid = (p.amount_paid or 0) + amount_paid
    p.paid_date = paid_date or today()
    if p.amount_paid >= p.amount_due:
        p.status = "paid"
        if not p.receipt_number:
            p.receipt_number = next_receipt(db)
    else:
        p.status = "partial"
        if not p.receipt_number:
            p.receipt_number = next_receipt(db)
    db.commit()
    return payment_to_dict(p)

@app.post("/api/payments/{pid}/delete")
def delete_payment(pid: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.get(Payment, pid)
    if not p:
        raise HTTPException(404)
    p.deleted = True; p.deleted_at = today()
    db.commit()
    return {"ok": True}

@app.post("/api/payments/{pid}/restore")
def restore_payment(pid: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.get(Payment, pid)
    if not p:
        raise HTTPException(404)
    p.deleted = False; p.deleted_at = None
    db.commit()
    return {"ok": True}

# ── Receipt tokens ────────────────────────────────────────────────────────────
@app.post("/api/payments/{pid}/receipt-token")
def generate_receipt_token(pid: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.get(Payment, pid)
    if not p or not p.receipt_number:
        raise HTTPException(404)
    token = secrets.token_hex(24)
    expiry = date.today().replace(day=date.today().day)
    from datetime import timedelta
    expiry = (date.today() + timedelta(days=10)).isoformat()
    db.add(ReceiptToken(token=token, payment_id=pid, expiry=expiry))
    db.commit()
    return {"token": token, "expiry": expiry}

@app.get("/receipt/{token}", response_class=HTMLResponse)
def view_receipt(token: str, db: Session = Depends(get_db)):
    rt = db.get(ReceiptToken, token)
    if not rt or rt.expiry < today():
        return HTMLResponse("""<!DOCTYPE html><html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>رابط غير صالح</title>
<style>body{font-family:Arial;display:flex;align-items:center;justify-content:center;height:100vh;background:#f8fafc;color:#0f172a}</style>
</head><body><div style="text-align:center">
<div style="font-size:64px">❌</div>
<h2>رابط غير صالح أو منتهي الصلاحية</h2>
<p style="color:#64748b">يصلح الرابط لمدة 10 أيام من تاريخ الإصدار</p>
</div></body></html>""", status_code=404)

    p = rt.payment
    c = p.contract
    t = c.tenant
    u = c.unit
    prop = u.property

    html = f"""<!DOCTYPE html><html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>إيصال {p.receipt_number}</title>
<style>
  body{{font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a;margin:0;padding:20px;direction:rtl}}
  .card{{background:#fff;border-radius:16px;padding:32px;max-width:480px;margin:40px auto;box-shadow:0 4px 24px rgba(0,0,0,.08)}}
  .header{{text-align:center;margin-bottom:24px}}
  .icon{{font-size:56px}}
  h1{{font-size:20px;margin:8px 0 4px}}
  .sub{{color:#64748b;font-size:14px}}
  .row{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #e2e8f0;font-size:14px}}
  .label{{color:#64748b}}
  .amount{{font-size:24px;font-weight:800;color:#22c55e;text-align:center;margin:16px 0}}
  .footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:16px}}
</style></head>
<body>
<div class="card">
  <div class="header">
    <div class="icon">🧾</div>
    <h1>{p.receipt_number}</h1>
    <div class="sub">إيصال استلام دفعة</div>
  </div>
  <div class="amount">{p.amount_paid:,.0f} ر.س</div>
  <div class="row"><span class="label">المستأجر</span><span>{t.name}</span></div>
  <div class="row"><span class="label">العقار</span><span>{prop.name}</span></div>
  <div class="row"><span class="label">الوحدة</span><span>{u.number}</span></div>
  <div class="row"><span class="label">رقم العقد</span><span>{c.id}</span></div>
  <div class="row"><span class="label">تاريخ الدفع</span><span>{p.paid_date or '—'}</span></div>
  <div class="row"><span class="label">تاريخ الاستحقاق</span><span>{p.due_date}</span></div>
  <div class="footer">إيجار Pro — إدارة العقارات</div>
</div>
</body></html>"""
    return HTMLResponse(html)

# ── Follow-up log ─────────────────────────────────────────────────────────────
@app.post("/api/followup")
def log_followup(
    contract_id: str = Form(...), action: str = Form(...),
    payment_id: str = Form(""), note: str = Form(""),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    entry = FollowupLog(
        id=f"FL{int(datetime.utcnow().timestamp()*1000)}",
        contract_id=contract_id, payment_id=payment_id or None,
        action=action, note=note, ts=datetime.utcnow().isoformat(),
    )
    db.add(entry); db.commit()
    return {"ok": True}

@app.get("/api/followup/{contract_id}")
def get_followup(contract_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    logs = db.query(FollowupLog).filter_by(contract_id=contract_id).order_by(FollowupLog.ts.desc()).all()
    return [{"id": l.id, "action": l.action, "note": l.note, "ts": l.ts} for l in logs]

# ── Dashboard stats ───────────────────────────────────────────────────────────
@app.get("/api/stats")
def dashboard_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    active_contracts = db.query(Contract).filter_by(status="active", archived=False, deleted=False).count()
    all_payments = db.query(Payment).filter_by(deleted=False).all()
    overdue = [p for p in all_payments if is_overdue(p)]
    total_overdue = sum(p.amount_due - (p.amount_paid or 0) for p in overdue)

    this_month = today()[:7]
    collected = sum(p.amount_paid for p in all_payments if p.paid_date and p.paid_date.startswith(this_month))

    cutoff = (date.today().replace(day=1) if False else date.today())
    from datetime import timedelta
    cutoff60 = (date.today() + timedelta(days=60)).isoformat()
    expiring = db.query(Contract).filter(
        Contract.status == "active",
        Contract.archived == False,
        Contract.deleted == False,
        Contract.end_date <= cutoff60,
    ).count()

    return {
        "active_contracts": active_contracts,
        "overdue_count": len(overdue),
        "total_overdue": total_overdue,
        "collected_this_month": collected,
        "expiring_count": expiring,
    }

# ── Overdue list ──────────────────────────────────────────────────────────────
@app.get("/api/overdue")
def get_overdue(db: Session = Depends(get_db), _=Depends(get_current_user)):
    payments = db.query(Payment).filter_by(deleted=False).all()
    result = []
    for p in payments:
        if not is_overdue(p):
            continue
        c = p.contract
        t = c.tenant
        u = c.unit
        prop = u.property
        days = overdue_days(p)
        sev = "low" if days <= 7 else "medium" if days <= 30 else "high"
        result.append({
            **payment_to_dict(p),
            "overdue_days": days,
            "severity": sev,
            "remaining": p.amount_due - (p.amount_paid or 0),
            "tenant_name": t.name,
            "tenant_phone": t.phone,
            "unit_number": u.number,
            "property_name": prop.name,
            "contract_id": c.id,
            "ejar_number": c.ejar_number,
        })
    result.sort(key=lambda x: x["overdue_days"], reverse=True)
    return result

# ── Settings (templates + telegram) ──────────────────────────────────────────
@app.get("/api/settings/templates")
def get_templates(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_setting(db, "templates", {})

@app.post("/api/settings/templates")
async def save_templates(request: Request, db: Session = Depends(get_db), _=Depends(get_current_user)):
    data = await request.json()
    set_setting(db, "templates", data)
    return {"ok": True}

@app.get("/api/settings/telegram")
def get_telegram(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_setting(db, "telegram", {})

@app.post("/api/settings/telegram")
async def save_telegram(request: Request, db: Session = Depends(get_db), _=Depends(get_current_user)):
    data = await request.json()
    set_setting(db, "telegram", data)
    return {"ok": True}

# ── Export / Import ───────────────────────────────────────────────────────────
@app.get("/api/export")
def export_data(db: Session = Depends(get_db), _=Depends(get_current_user)):
    data = {
        "properties": [{"id": p.id, "name": p.name, "city": p.city, "address": p.address, "type": p.type}
                        for p in db.query(Property).all()],
        "units": [{"id": u.id, "property_id": u.property_id, "number": u.number,
                   "floor": u.floor, "type": u.type, "area_m2": u.area_m2}
                  for u in db.query(Unit).all()],
        "tenants": [{"id": t.id, "name": t.name, "phone": t.phone, "email": t.email, "id_number": t.id_number}
                    for t in db.query(Tenant).all()],
        "contracts": [contract_to_dict(c) for c in db.query(Contract).all()],
        "payments": [payment_to_dict(p) for p in db.query(Payment).all()],
        "templates": get_setting(db, "templates", {}),
        "telegram": get_setting(db, "telegram", {}),
        "exported_at": datetime.utcnow().isoformat(),
    }
    return JSONResponse(data, headers={"Content-Disposition": f"attachment; filename=ejar_backup_{today()}.json"})

# ── Static files (last, catch-all) ───────────────────────────────────────────
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
