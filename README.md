# إيجار Pro 🏢

نظام إدارة عقارات وإيجارات مبني للسوق السعودي — عقود، مستأجرون، متابعة مدفوعات، إيصالات، وتكامل مع واتساب وTelegram.

**Stack:** FastAPI · SQLite · Python · Vanilla JS · Docker

---

## تشغيل سريع عبر Portainer

**1.** Stacks → Add stack → Repository

**2.** أدخل:
```
https://github.com/ThamerLab/ejar-pro
```

**3.** أضف المتغيرات:

| Name | Value |
|------|-------|
| `SECRET_KEY` | سلسلة عشوائية طويلة |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور قوية |
| `DB_PATH` | `/data/ejar.db` |

**4.** Deploy the stack ✅

افتح: `http://SERVER_IP:8000`

> للتعليمات التفصيلية خطوة بخطوة مع Docker Compose → [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## المميزات

- 📥 **متابعة يومية** — صندوق وارد للمتأخرات مرتّبة حسب الخطورة (منخفض / متوسط / حرج)
- 📋 **إدارة عقود** — مرتبطة بمنصة إيجار الحكومية برقم EJR
- 💰 **تسجيل المدفوعات** — دفع جزئي مدعوم، إيصالات برقم `RV-YYYY-NNN`
- 📲 **واتساب تلقائي** — قوالب تذكير وتصعيد وإيصال بالعربي
- 🔗 **رابط إيصال مؤمَّن** — توكن عشوائي صالح 10 أيام يُرسَل للمستأجر
- 📨 **إشعارات Telegram** — بوت مخصص مع تحكم بأنواع التنبيهات
- 👥 **نظام مستخدمين** — أدوار admin / viewer
- 🔐 **Session cookie** — httponly + bcrypt
- 💾 **تصدير / استيراد** — نسخ احتياطي JSON بضغطة واحدة

---

## هيكل المشروع

```
ejar-pro/
├── backend/
│   ├── main.py        # FastAPI — كل الـ API routes
│   ├── models.py      # SQLAlchemy models (8 جداول)
│   ├── auth.py        # Session cookie + bcrypt
│   ├── database.py    # SQLite connection
│   └── seed.py        # بيانات تجريبية + إنشاء admin
├── frontend/
│   ├── login.html     # صفحة الدخول
│   ├── app.html       # التطبيق الرئيسي (SPA)
│   └── static/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DEPLOYMENT.md      # دليل النشر التفصيلي
├── ARCHITECTURE.md    # هيكل النظام
└── DATABASE.md        # مخطط قاعدة البيانات
```

---

## الوثائق

| الملف | المحتوى |
|-------|---------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Portainer · Docker Compose · نسخ احتياطي |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | هيكل النظام · تدفق البيانات · Auth flow |
| [DATABASE.md](./DATABASE.md) | الجداول · العلاقات · قواعد الأعمال |

---

## متطلبات النشر

- Docker + Docker Compose
- لا توجد قاعدة بيانات خارجية — SQLite مدمجة داخل الحاوية
