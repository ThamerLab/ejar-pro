# ARCHITECTURE.md — هيكل النظام

## Stack

| الطبقة | التقنية | الدور |
|--------|---------|-------|
| Web server | FastAPI (Python) | API + Static files |
| Database | SQLite + SQLAlchemy | تخزين البيانات |
| Auth | itsdangerous + bcrypt | Session cookie |
| Frontend | Vanilla JS | SPA بدون framework |
| Container | Docker | نشر كل شيء معاً |

---

## تدفق الطلب

```
المتصفح
   │
   ├── GET /            → login.html (إذا لم يوجد session)
   ├── GET /app         → app.html   (يتحقق من session أولاً)
   ├── POST /api/auth/login → يضع session cookie
   │
   └── GET|POST /api/* → FastAPI routes
                              │
                         SQLite (ejar.db)
```

---

## Backend — `backend/`

```
main.py
  ├── Auth routes      /api/auth/*
  ├── Users            /api/users
  ├── Properties       /api/properties
  ├── Units            /api/units
  ├── Tenants          /api/tenants
  ├── Contracts        /api/contracts
  ├── Payments         /api/payments
  ├── Receipt tokens   /receipt/{token}
  ├── Follow-up log    /api/followup
  ├── Stats            /api/stats
  ├── Settings         /api/settings/*
  └── Export           /api/export

models.py   → SQLAlchemy ORM (8 جداول)
auth.py     → hash_password, session cookie, get_current_user
database.py → SQLite engine, SessionLocal, get_db
seed.py     → بيانات تجريبية + إنشاء admin عند أول تشغيل
```

---

## Frontend — `frontend/`

```
login.html  → صفحة مستقلة، POST /api/auth/login بـ fetch
app.html    → SPA كاملة
  ├── API{}         كل fetch calls
  ├── _cache{}      بيانات محمّلة في الذاكرة (تُحدَّث عند كل navigate)
  ├── navigate()    router
  ├── render*()     page renderers → HTML strings
  ├── handleAction() action dispatcher
  └── bindActions() ربط الأزرار
```

---

## Auth Flow

```
POST /api/auth/login
        │
  verify_password()
        │
  create_session_cookie(user_id)
        │
  Set-Cookie: ejar_session=<signed_token>; HttpOnly
        │
  كل طلب تالٍ: get_current_user()
        ├── يقرأ الـ cookie
        ├── يفكّ التوقيع (itsdangerous)
        └── يجلب User من DB
```

---

## Receipt Token Flow

```
تسجيل دفعة ناجح
       │
POST /api/payments/{id}/receipt-token
       │
secrets.token_hex(24)  → 48 حرف عشوائي
       │
DB: receipt_tokens (token, payment_id, expiry+10days)
       │
URL: /receipt/{token}
       │
GET /receipt/{token}
       │
تحقق من expiry → عرض HTML إيصال عام (بلا login)
```
