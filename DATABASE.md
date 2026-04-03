# DATABASE.md — مخطط قاعدة البيانات

**النوع:** SQLite — ملف واحد في `/data/ejar.db`

---

## الجداول

### `users`
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | Integer PK | تلقائي |
| username | String UNIQUE | اسم الدخول |
| full_name | String | الاسم الكامل |
| hashed_pw | String | bcrypt hash |
| role | String | `admin` / `viewer` |
| is_active | Boolean | تعطيل بدون حذف |
| created_at | DateTime | تاريخ الإنشاء |

### `properties` → `units` → `contracts` → `payments`

العلاقات:
```
properties
    │ 1:∞
  units ──────────── 1 عقد نشط كحد أقصى
    │ 1:∞
contracts ◄── tenants
    │ 1:∞
payments
    │ 1:∞
receipt_tokens
```

### `payments` — أهم جدول
| العمود | الوصف |
|--------|-------|
| status | `pending` / `paid` / `partial` / `overdue` |
| amount_due | المبلغ الكامل المستحق |
| amount_paid | المدفوع فعلاً (يتراكم عند الدفع الجزئي) |
| deleted | حذف ناعم — يحفظ الأثر المحاسبي |
| receipt_number | `RV-YYYY-NNN` — يُولَّد عند أول دفع |

### `app_settings`
```
key          | value
-------------|---------------------------
templates    | JSON (reminder/escalation/receipt)
telegram     | JSON (bot_token/chat_id/alerts)
receipt_seq  | رقم تسلسلي للإيصالات
*_seq        | أرقام تسلسلية للـ IDs
```

---

## قواعد الأعمال (محمية في الـ API)

| القاعدة | الكود |
|---------|-------|
| التأخر يبدأ بعد يوم | `days_diff(due_date, today) >= 1` |
| لا دفع زائد | `amount_paid > remaining → 400` |
| لا عقدان نشطان | `get_active_contract(unit_id) → 400` |
| توكن الإيصال | `secrets.token_hex(24)` — 10 أيام |
