# DEPLOYMENT.md — دليل النشر

---

## الطريقة 1 — Portainer (موصى بها) 🐳

### المتطلبات
- خادم Linux مع Docker مثبّت
- Portainer مثبّت ويعمل

---

### الخطوة 1 — تثبيت Portainer (إذا لم يكن مثبّتاً)

```bash
docker volume create portainer_data

docker run -d \
  -p 8000:8000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

افتح المتصفح على: `https://SERVER_IP:9443`

---

### الخطوة 2 — نشر إيجار Pro من Portainer

**1.** من القائمة الجانبية اختر **Stacks** ← **+ Add stack**

**2.** في حقل **Name** اكتب:
```
ejar-pro
```

**3.** اختر **Repository** ثم أدخل:

| الحقل | القيمة |
|-------|--------|
| Repository URL | `https://github.com/ThamerLab/ejar-pro` |
| Repository reference | `refs/heads/main` |
| Compose path | `docker-compose.yml` |

**4.** انزل لأسفل لقسم **Environment variables** واضغط **+ Add an environment variable** وأضف:

| Name | Value |
|------|-------|
| `SECRET_KEY` | سلسلة عشوائية طويلة (مثال: `xK9mP2nQ8vL5wR3`) |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور قوية |
| `DB_PATH` | `/data/ejar.db` |

> ⚠️ **مهم:** غيّر `SECRET_KEY` و `ADMIN_PASSWORD` — لا تتركها الافتراضية.

**5.** اضغط **Deploy the stack** وانتظر 30–60 ثانية.

**6.** بعد النشر الناجح يظهر Status: **running** ✅

افتح التطبيق على: `http://SERVER_IP:8000`

---

### الخطوة 3 — أول دخول

افتح `http://SERVER_IP:8000` في المتصفح.

- **اسم المستخدم:** `admin`
- **كلمة المرور:** (ما أدخلته في `ADMIN_PASSWORD`)

بعد الدخول روح **المستخدمون** من القائمة وأنشئ حسابات إضافية إذا لزم.

---

### الخطوة 4 — تحديث التطبيق لاحقاً

عند صدور تحديث جديد على GitHub:

1. Portainer → **Stacks** → **ejar-pro**
2. اضغط **Pull and redeploy**
3. أكّد بـ **Update**

البيانات محفوظة في الـ volume ولن تُمسح. ✅

---

## الطريقة 2 — Docker Compose مباشرة

```bash
git clone https://github.com/ThamerLab/ejar-pro.git
cd ejar-pro
cp .env.example .env
nano .env          # غيّر SECRET_KEY و ADMIN_PASSWORD
docker compose up -d
docker compose logs -f
```

التطبيق يعمل على: `http://localhost:8000`

---

## متغيرات البيئة

| المتغير | الوصف | الافتراضي |
|---------|-------|-----------|
| `SECRET_KEY` | مفتاح تشفير الـ session — **غيّره دائماً** | `change-this...` |
| `ADMIN_USERNAME` | اسم المدير عند أول تشغيل | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور المدير — **غيّرها دائماً** | `admin123` |
| `DB_PATH` | مسار ملف SQLite داخل الحاوية | `/data/ejar.db` |

---

## النسخ الاحتياطي

**من داخل التطبيق:**
القائمة الجانبية ← ⬇️ تصدير البيانات (JSON)

**من الخادم مباشرة:**
```bash
docker cp ejar-pro:/data/ejar.db ./ejar_backup_$(date +%Y%m%d).db
```

**استعادة:**
```bash
docker cp ./ejar_backup_YYYYMMDD.db ejar-pro:/data/ejar.db
docker restart ejar-pro
```

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| الصفحة لا تفتح | `docker logs ejar-pro` |
| خطأ في تسجيل الدخول | تأكد من `ADMIN_PASSWORD` في المتغيرات |
| البيانات اختفت | `docker volume ls` — تأكد أن `ejar_data` موجود |
| المنفذ 8000 مشغول | غيّر `"8000:8000"` لـ `"8080:8000"` في docker-compose.yml |
