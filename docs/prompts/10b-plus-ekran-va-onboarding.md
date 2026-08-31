# Vazifa 10b — "+" ekrani (AI + chek) va birinchi kirish tanishuvi

10-vazifaning ustiga ikkita aniqlik. Kelishilgan: OCR va AI matn kiritish
"+" ekranida, uch tugmadan oldin bo'ladi.

---

## 1. AI va chek "+" ekranida

Hozir "+" bosilganda faqat uchta tugma bor: **Ish**, **Material**, **Xarajat**.
AI matn maydoni va chek o'qish oqimlar ichida qolib ketgan — usta ularni
topmaydi.

"+" ekranining **eng tepasiga**, uch tugmadan **oldin**:

```
┌──────────────────────────────────────┐
│ ✨ Yozing…                        📷 │
│    "sement 5 qop 650 ming mijoz naqd" │
└──────────────────────────────────────┘

────────────── yoki ──────────────

[ 🔧 Ish ]
[ 📦 Material ]
[ 🧾 Xarajat ]
```

- Matn maydoniga yozib yuborsa → `POST /api/projects/{id}/ai-parse`
- O'ngdagi kamera ikonkasi → chek surati → `POST /api/projects/{id}/receipt-scan`
- Ikkalasi ham natijani **tasdiqlash kartasida** ko'rsatadi (10-vazifa
  3-bo'limdagi qo'lda kiritish formasi, oldindan to'ldirilgan)

Yozuvning turi (ish / material / xarajat) javobdagi `kind` dan olinadi —
usta oldindan tanlashi shart emas.

Uchta tugma **qoladi**: AI ishlamasa yoki usta ataylab qo'lda tanlamoqchi
bo'lsa.

---

## 2. Birinchi kirishda tanishuv

Yangi foydalanuvchi ilovani birinchi marta ochganda **ism va telefon**
so'ralsin — hisobotda va PDF da ular kerak.

### Backend

`users.full_name` Telegram'dan keladi, `phone` bo'sh bo'ladi. Yangi maydon:

| Ustun | Tur |
|---|---|
| onboarded | BOOLEAN, NOT NULL, default `false` |

Alembic migratsiyasi. `GET /api/me` javobiga `onboarded` qo'shilsin.

### Frontend

`onboarded = false` bo'lsa — boshqa hech qanday ekran ochilmasdan oldin
**tanishuv ekrani**:

```
Xush kelibsiz!

Ismingiz      [ Shahriyor            ]   (Telegram'dan to'ldirilgan)
Telefon       [ +998 __ ___ __ __    ]

Bu ma'lumotlar hisobotlarda ko'rsatiladi.

[ Davom etish ]
```

- Ism majburiy, telefon majburiy
- Telefon: `+998` bilan boshlanadi, keyin 9 raqam
- `Davom etish` → `PATCH /api/me { full_name, phone, onboarded: true }`
- Keyin Asosiy ekranga o'tadi

### Bot

`/start` bosilganda `phone` bo'sh bo'lsa — `request_contact` tugmasi bilan
raqam so'ralsin: **`📱 Raqamni yuborish`**. Yuborilsa saqlanadi va
`onboarded = true` bo'ladi. **`Keyinroq`** tugmasi ham bo'lsin —
majburlamaydi, lekin har `/start` da qayta so'raydi.
