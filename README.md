# إيجار Pro 🏢

نظام إدارة العقارات والإيجارات للسوق السعودي.

**Stack:** FastAPI · SQLite · Python · Vanilla JS · Docker

---

## تشغيل سريع

```bash
git clone https://github.com/YOUR_USERNAME/ejar-pro.git
cd ejar-pro
cp .env.example .env        # عدّل كلمة المرور والـ secret
docker compose up -d
```

افتح المتصفح على: `http://localhost:8000`

**الدخول الافتراضي:** `admin` / `admin123`

---

## هيكل المشروع

```
ejar-pro/
├── backend/
│   ├── main.py        # FastAPI — كل الـ API routes
│   ├── models.py      # SQLAlchemy models (8 جداول)
│   ├── auth.py        # Session cookie + bcrypt
│   ├── database.py    # SQLite connection
│   └── seed.py        # بيانات تجريبية + admin
├── frontend/
│   ├── login.html     # صفحة الدخول
│   ├── app.html       # التطبيق الرئيسي
│   └── static/        # ملفات ثابتة (أيقونات، CSS إضافي)
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
├── ARCHITECTURE.md
└── DATABASE.md
```

---

## المميزات

- 📥 متابعة يومية للمتأخرات مع تصنيف الخطورة
- 📋 إدارة عقود مرتبطة بمنصة إيجار (EJR)
- 💰 دفع جزئي، إيصالات، روابط واتساب تلقائية
- 📨 إشعارات Telegram
- ✉️ قوالب رسائل عربية قابلة للتخصيص
- 👥 نظام مستخدمين (admin / viewer)
- 🔐 Session cookie آمن

---

## متطلبات النشر

- Docker + Docker Compose
- لا يوجد قاعدة بيانات خارجية — SQLite مدمجة

راجع [DEPLOYMENT.md](./DEPLOYMENT.md) للتفاصيل.
