# DEPLOYMENT.md — دليل النشر

## 1. Docker Compose (الأسرع)

```bash
# 1. استنسخ المشروع
git clone https://github.com/YOUR_USERNAME/ejar-pro.git
cd ejar-pro

# 2. اضبط المتغيرات
cp .env.example .env
nano .env   # غيّر SECRET_KEY و ADMIN_PASSWORD

# 3. شغّل
docker compose up -d

# 4. تحقق
docker compose logs -f
```

التطبيق يعمل على: `http://SERVER_IP:8000`

---

## 2. Portainer (Stack)

1. افتح Portainer → **Stacks** → **Add stack**
2. اسم الـ stack: `ejar-pro`
3. اختر **Repository** والصق رابط الـ GitHub repo
4. أضف المتغيرات في **Environment variables**:

| المتغير | القيمة |
|---------|--------|
| `SECRET_KEY` | سلسلة عشوائية طويلة |
| `ADMIN_PASSWORD` | كلمة مرور قوية |
| `ADMIN_USERNAME` | admin |

5. اضغط **Deploy the stack**

---

## 3. متغيرات البيئة

| المتغير | الوصف | الافتراضي |
|---------|-------|-----------|
| `SECRET_KEY` | مفتاح تشفير الـ session — **غيّره** | `change-this...` |
| `ADMIN_USERNAME` | اسم المدير الأول | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور المدير — **غيّرها** | `admin123` |
| `DB_PATH` | مسار ملف SQLite | `/data/ejar.db` |

---

## 4. البيانات والنسخ الاحتياطي

البيانات في Docker Volume اسمه `ejar_data`.

```bash
# نسخ احتياطي
docker cp ejar-pro:/data/ejar.db ./backup_$(date +%Y%m%d).db

# أو من داخل التطبيق
# الشريط الجانبي → ⬇️ تصدير البيانات (JSON)
```

---

## 5. التحديث

```bash
git pull
docker compose build
docker compose up -d
```

البيانات محفوظة في الـ volume ولن تُمسح.
