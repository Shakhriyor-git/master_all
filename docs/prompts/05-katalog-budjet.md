# Vazifa 05 — Kategoriyalar, budjet, to'lov usullari va qaydlar

## Kontekst

01–03 tugagan: modellar, auth, CRUD API, ishlaydigan bot.
Bu vazifa sxemani kengaytiradi. Web App (06) shundan keyin yoziladi.

**Vazifa katta. Ikki bosqichda bajar:**

- **A bosqich:** sxema + migratsiya + standart katalog + `summary` qayta yozish
- **B bosqich:** API endpointlar + bot yangilanishi

A tugagach **to'xta**, natijani ko'rsat, tasdiq kutib turib keyin B ga o't.

---

## Asosiy g'oya

Loyihada ikkita mustaqil hisob bor, ular hech qachon qo'shilmaydi:

```
1. ISH HAQI HISOBI  — usta topgan pul
   ishlar + usta to'lagan material − mijoz to'lagan ish haqi = mijoz qarzi

2. MIJOZ BUDJETI    — mijoz xarajat uchun bergan naqd
   berilgan − shu puldan sarflangan = budjet qoldig'i
```

---

# A BOSQICH

## A1. Yangi jadval: `categories`

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| name | VARCHAR(100), NOT NULL |
| kind | VARCHAR(20), NOT NULL — `work` yoki `material` |
| icon | VARCHAR(20), NULL — emoji, karta ko'rinishi uchun |
| sort_order | INTEGER, NOT NULL, default 0 |
| is_active | BOOLEAN, NOT NULL, default true |
| created_at / updated_at | TIMESTAMPTZ |

UNIQUE `(user_id, name, kind)`. Index `(user_id, kind, is_active)`.

## A2. Yangi jadval: `units`

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| code | VARCHAR(20), NOT NULL — bazada saqlanadigan qiymat, masalan `m2` |
| label | VARCHAR(30), NOT NULL — ko'rsatiladigan matn, masalan `m²` |
| is_system | BOOLEAN, default false — standart birlik, o'chirib bo'lmaydi |
| sort_order | INTEGER, default 0 |
| is_active | BOOLEAN, default true |

UNIQUE `(user_id, code)`.

`entries.unit` va `price_items.unit` allaqachon VARCHAR — ular `code` ni saqlaydi.
FK qo'yilmaydi: birlik o'chirilsa ham eski yozuvlar buzilmasligi kerak.

## A3. Yangi jadvallar: `notes` va `note_items`

Usta ish paytida kerakli narsalarni yozib qo'yadi — olinadigan mollar ro'yxati,
mijoz aytgan gap, o'lchamlar.

**`notes`**

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| project_id | BIGINT FK → projects.id, CASCADE, NULL — umumiy qayd bo'lsa NULL |
| title | VARCHAR(200), NOT NULL |
| body | TEXT, NULL — erkin matn |
| is_pinned | BOOLEAN, default false |
| created_at / updated_at / deleted_at | TIMESTAMPTZ |

Index `(user_id, project_id, is_pinned)`.

**`note_items`** — belgilanadigan ro'yxat (xarid ro'yxati uchun)

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| note_id | BIGINT FK → notes.id, CASCADE, NOT NULL |
| text | VARCHAR(300), NOT NULL |
| is_done | BOOLEAN, default false |
| sort_order | INTEGER, default 0 |

Qayd faqat matn (`body`), yoki belgilanadigan ro'yxat (`note_items`), yoki
ikkalasi birga bo'lishi mumkin. Alohida `kind` ustuni kerak emas.

## A4. `price_items` ga qo'shimcha

| Ustun | Tur |
|---|---|
| category_id | BIGINT FK → categories.id, ON DELETE SET NULL, NULL |

## A5. `entries` ga qo'shimcha

| Ustun | Tur | Izoh |
|---|---|---|
| is_billable | BOOLEAN, NOT NULL, default true | mijozga hisoblanadimi |
| is_rework | BOOLEAN, NOT NULL, default false | brak / qayta qilingan ish |
| payment_method | VARCHAR(20), NULL | `cash` / `card` / `transfer` |
| vendor | VARCHAR(200), NULL | qayerdan olindi — "Qurilish bozori" |

`kind` ga uchinchi qiymat: **`expense`** — ovqat, transport, asbob ijarasi.
Bunda `quantity = 1`, `unit = 'summa'`, `unit_price` = xarajat summasi.

`payment_method` faqat `material` va `expense` uchun to'ldiriladi.

**Server tomonda majburlanadigan qoidalar** (faqat UI da emas):

- `is_rework = true` → `is_billable` majburan `false`
- `kind = 'expense'` va `paid_by = 'master'` → `is_billable` majburan `false`
  (ustaning o'z ovqat/transport xarajati hech qachon mijozga yozilmaydi)
- `kind = 'work'` → `payment_method` va `vendor` majburan `NULL`

## A6. `payments` ga qo'shimcha

| Ustun | Tur | Izoh |
|---|---|---|
| purpose | VARCHAR(20), NOT NULL, default 'labor' | `labor` yoki `budget` |

- `labor` — mijoz ish haqi uchun to'ladi, qarzni kamaytiradi
- `budget` — mijoz xarajat uchun naqd berdi, budjetni to'ldiradi

Index `(project_id, purpose, paid_at)`.
Migratsiyada mavjud qatorlar `'labor'` bo'lib qoladi — bu to'g'ri.

## A7. Standart katalog

Yangi foydalanuvchi birinchi marta `/start` bosganda katalog avtomatik
to'ldirilsin. Usta keraksizini o'chiradi, yangisini qo'shadi.

`app/services/catalog_seed.py` da ma'lumot, `UserMiddleware` da yangi
foydalanuvchi yaratilganda chaqiriladi. Idempotent bo'lsin.

**Narxlar `0` qo'yiladi** — usta o'zi belgilaydi. Taxminiy narx yozilsa,
eskirib mijoz bilan janjalga sabab bo'ladi.

### Birliklar (hammasi `is_system = true`)

`m2` m² · `m3` m³ · `dona` dona · `qop` qop · `metr` metr · `kg` kg ·
`litr` litr · `soat` soat · `kunlik` kunlik · `tochka` tochka ·
`komplekt` komplekt · `rulon` rulon · `summa` summa

`summa` — `expense` yozuvlari uchun, tanlov ro'yxatida ko'rsatilmasin.

### Ish kategoriyalari

**🏠 Shift** — Gipsokarton yopishtirish `m2` · Gulli gipsokarton `m2` ·
Shift shpatlyovka `m2` · Shift emulsiya `m2` · Natyajnoy potolok `m2`

**🧱 Devor** — Shtukaturka `m2` · Shpatlyovka `m2` · Bo'yash `m2` ·
Oboy yopishtirish `m2` · Dekorativ pardoz `m2`

**⬜ Pol** — Quyma pol (styajka) `m2` · Laminat yotqizish `m2` ·
Plintus o'rnatish `metr`

**◻️ Kafel** — Devorga kafel `m2` · Polga kafel `m2` · Zatirka `m2`

**⚡ Elektrika** — Tochka (rozetka/vklyuchatel) `tochka` · Shtroba ochish `metr` ·
Sim tortish `metr` · Karobka bog'lash `dona` · Lyustra o'rnatish `dona` ·
Shitok yig'ish `dona`

**🚿 Santexnika** — Unitaz o'rnatish `dona` · Rakovina o'rnatish `dona` ·
Dush kabina `dona` · Quvur tortish `metr` · Radiator o'rnatish `dona`

**🔨 Demontaj** — Devor buzish `m2` · Eski kafel ko'chirish `m2` ·
Chiqindi chiqarish `kunlik`

**📋 Umumiy** — Kunlik ish `kunlik` · Yordamchi ishchi `kunlik`

### Material kategoriyalari

**🪣 Aralashmalar** — Sement `qop` · Gips `qop` · Shpatlyovka `qop` ·
Grunt `litr` · Qum `m3`

**◻️ Kafel mollari** — Kafel `m2` · Yopishtiruvchi `qop` · Zatirka `kg` ·
Krestik `komplekt`

**⚡ Elektr mollari** — Sim `metr` · Rozetka `dona` · Vklyuchatel `dona` ·
Karobka `dona` · Avtomat `dona`

**🚿 Santexnika mollari** — Quvur `metr` · Kran `dona` · Fitting `dona`

**🎨 Bo'yoq** — Emulsiya `litr` · Bo'yoq `litr` · Valik `dona`

## A8. `summary` xizmatini qayta yozish

`app/services/summary.py` javob tuzilishi butunlay o'zgaradi:

```json
{
  "labor": {
    "works_total":         "2400000.00",
    "materials_by_master": "350000.00",
    "paid_labor":          "2000000.00",
    "client_owes":         "750000.00",
    "rework_total":        "180000.00",
    "expenses_by_master":  "120000.00"
  },
  "budget": {
    "given":            "1000000.00",
    "spent_materials":  "520000.00",
    "spent_expenses":   "120000.00",
    "spent_total":      "640000.00",
    "balance":          "360000.00"
  },
  "meta": { "entries_count": 24, "last_entry_date": "2026-08-28" }
}
```

Formulalar:

```
works_total          = Σ entries[kind=work, is_billable=true]
rework_total         = Σ entries[kind=work, is_rework=true]      (ma'lumot uchun)
materials_by_master  = Σ entries[kind=material, paid_by=master, is_billable=true]
expenses_by_master   = Σ entries[kind=expense,  paid_by=master]  (ma'lumot uchun)
paid_labor           = Σ payments[purpose=labor]

client_owes = works_total + materials_by_master − paid_labor

given           = Σ payments[purpose=budget]
spent_materials = Σ entries[kind=material, paid_by=client]
spent_expenses  = Σ entries[kind=expense,  paid_by=client]
balance         = given − spent_materials − spent_expenses
```

Hamma joyda `deleted_at IS NULL`. Bitta agregat so'rovda hisoblansin.
`client_owes` manfiy bo'lishi mumkin (mijoz avans bergan) — xizmat raqamni
o'zgartirmasin, matn tayyorlash UI vazifasi.

## A bosqich qabul mezoni

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
docker compose exec api ruff check app scripts
```

`scripts/test_summary.py` yozilsin, quyidagi ssenariy bilan:

| # | Yozuv | Summa |
|---|---|---|
| 1 | Ish (oddiy) | 2 400 000 |
| 2 | Ish (brak, `is_rework`) | 180 000 |
| 3 | Material, usta puliga, karta | 350 000 |
| 4 | Material, mijoz puliga, naqd | 520 000 |
| 5 | Xarajat (ovqat), usta puliga | 120 000 |
| 6 | Xarajat (transport), mijoz puliga | 120 000 |
| 7 | To'lov `labor` | 2 000 000 |
| 8 | To'lov `budget` | 1 000 000 |

Kutilgan: `client_owes = 750 000`, `budget.balance = 360 000`.
Brak ham, ustaning ovqati ham qarzga kirmasligi alohida tekshirilsin.

**Shu yerda TO'XTA va natijani ko'rsat.**

---

# B BOSQICH

## B1. Kategoriyalar API

```
GET    /api/categories?kind=work     ro'yxat + har birida xizmatlar soni
POST   /api/categories               {name, kind, icon}
PATCH  /api/categories/{id}
DELETE /api/categories/{id}          is_active=false
```

`GET` javobida har bir kategoriya uchun `items_count` bo'lsin — Web App'da
karta ko'rinishida "Elektrika · 6 ta xizmat" deb ko'rsatiladi.

Kategoriya o'chirilganda ichidagi `price_items` o'chmasin — ular
`category_id = NULL` bo'lib "Kategoriyasiz" guruhiga tushsin.

## B2. Birliklar API

```
GET    /api/units                    is_active bo'lganlar
POST   /api/units                    {code, label}
DELETE /api/units/{id}               is_active=false; is_system=true bo'lsa 400
```

## B3. Katalog (Narxlarim) API

```
GET    /api/price-items?category_id=&kind=&q=
POST   /api/price-items              {category_id, name, kind, unit, default_price}
PATCH  /api/price-items/{id}         narx yoki nomni o'zgartirish
DELETE /api/price-items/{id}         is_active=false
```

`GET` javobida `category_name` va `unit_label` ham bo'lsin — frontend
qo'shimcha so'rov yubormasin.

## B4. Narxni loyihaga yangilash

Katalogdagi narx o'zgarganda **eski loyihalar o'zgarmaydi** — bu ataylab shunday.
Lekin usta xohlasa yangilay olsin:

```
POST /api/projects/{id}/prices/{price_id}/sync
```

`project_prices.price` ni katalogdagi joriy `default_price` ga tenglashtiradi.
Javobda eski va yangi narx qaytsin, UI tasdiq so'rashi uchun.

**Mavjud `entries` o'zgarmaydi** — ular yozilgan paytdagi narxni saqlaydi.
Faqat bundan keyingi yozuvlar yangi narx bilan ketadi.

## B5. Yozuvlar API kengaytirish

```
GET  /api/projects/{id}/entries?kind=&date_from=&date_to=&paid_by=&page=
POST /api/projects/{id}/entries      + is_rework, payment_method, vendor
```

`GET` javobida har bir yozuv uchun to'liq ma'lumot: sana, nom, kategoriya,
miqdor, birlik yorlig'i, birlik narxi, summa, kim to'lagan, qanday to'langan,
sotuvchi, chek bor-yo'qligi, brak belgisi.

Web App'dagi batafsil oyna aynan shu javobdan quriladi — qo'shimcha
so'rov kerak bo'lmasin.

Yangi: `DELETE /api/projects/{id}/entries/last` — oxirgi yozuvni bekor qilish
(soft delete, faqat eng oxirgi 1 ta; 5 daqiqadan eski bo'lsa 400).

## B6. To'lovlar API

```
POST /api/projects/{id}/payments     + purpose (labor | budget)
GET  /api/projects/{id}/payments?purpose=
```

## B7. Qaydlar API

```
GET    /api/notes?project_id=            ro'yxat, pinned birinchi
POST   /api/notes                        {project_id?, title, body?, items?}
GET    /api/notes/{id}                   items bilan birga
PATCH  /api/notes/{id}                   title, body, is_pinned
DELETE /api/notes/{id}                   soft delete

POST   /api/notes/{id}/items             {text}
PATCH  /api/notes/{id}/items/{item_id}   {text?, is_done?, sort_order?}
DELETE /api/notes/{id}/items/{item_id}
```

## B8. Bot yangilanishi

Botni qayta yozma, faqat shu joylarni moslashtir:

- **Ish/material qo'shish** — avval kategoriya, keyin xizmat. Kategoriya bitta
  bo'lsa qadam o'tkazib yuborilsin.
- **Material qo'shishda** — kim to'ladi, keyin qanday to'ladi
  (`[💵 Naqd] [💳 Karta] [🏦 O'tkazma]`).
- **Yangi tugma `[🧾 Xarajat]`** — obyekt kartasida. Nomi → summa →
  kim to'ladi → qanday to'ladi.
- **To'lovda** avval maqsad: `[💵 Ish haqi uchun] [🧾 Xarajat uchun]`.
- **Yangi tugma `[↩️ Oxirgini bekor qilish]`**.
- **Hisobot** ikki blokka bo'linsin (ish haqi hisobi / mijoz budjeti).
- **Manfiy qarz hech qachon ko'rsatilmasin:** `> 0` → "Mijoz qarzi",
  `< 0` → "Mijoz avansi" (minussiz, ostida "kelgusi ishlardan yechiladi"),
  `= 0` → "Hisob-kitob teng".
- Brak yozuvlari `⚠️` bilan, "mijozga yozilmadi" izohi bilan.
- **Qaydlar botga qo'shilmasin** — ular Web App'da bo'ladi.

## B bosqich qabul mezoni

```bash
docker compose exec api ruff check app scripts
docker compose logs bot          # xatosiz polling
```

Swagger'da barcha yangi endpointlar ko'rinsin.

---

## Nima QILMA

- Web App / React yozma — bu 06-vazifa.
- OCR, ovoz, Excel yozma.
- Brigada / rollar qo'shma.
- Mavjud endpointlarning nomini o'zgartirma, faqat kengaytir.
- Botga qaydlar bo'limini qo'shma.
