# Vazifa 13 — Brigada (sheriklarga to'lovlar)

## Nima bu

Ustaning shaxsiy daftari: "sheriklarimga qancha berdim". Yordamchilar
ilovaga kirmaydi, obyektlarga bog'lanmaydi, hisobotga ta'sir qilmaydi.

Faqat ikkita savolga javob beradi:
- Ushbu odamga jami qancha berdim?
- Qachon va qancha berdim?

`entries`, `payments`, `summary`, PDF — hech biriga tegmaydi. Butunlay
alohida bo'lim.

---

## 1. Backend

### 1.1. Yangi jadval `partners`

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| name | VARCHAR(100), NOT NULL |
| phone | VARCHAR(20), NULL |
| note | VARCHAR(300), NULL |
| deleted_at | TIMESTAMPTZ, NULL |
| created_at | TIMESTAMPTZ |

Index `(user_id, deleted_at)`.

### 1.2. Yangi jadval `partner_payments`

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| partner_id | BIGINT FK → partners.id, CASCADE, NOT NULL |
| amount | NUMERIC(14,2), NOT NULL, CHECK amount > 0 |
| method | VARCHAR(20), NOT NULL — cash/card/transfer |
| note | VARCHAR(300), NULL |
| paid_at | DATE, NOT NULL |
| deleted_at | TIMESTAMPTZ, NULL |
| created_at | TIMESTAMPTZ |

Index `(user_id, partner_id, paid_at DESC)`.

`user_id` ikkala jadvalda ham bor — bu ataylab qilingan. Har bir so'rov
`WHERE user_id = ?` bilan filtrlanadi, boshqa foydalanuvchining ma'lumoti
hech qachon ko'rinmasin.

### 1.3. Endpointlar

```
GET    /api/partners                    ro'yxat + har biriga total_paid
POST   /api/partners                    { name, phone?, note? }
PATCH  /api/partners/{id}               { name?, phone?, note? }
DELETE /api/partners/{id}               soft delete

GET    /api/partners/{id}/payments      to'lovlar tarixi (sanaga qarab)
POST   /api/partners/{id}/payments      { amount, method, paid_at, note? }
PATCH  /api/partner-payments/{id}       { amount?, method?, paid_at?, note? }
DELETE /api/partner-payments/{id}       soft delete
```

**`GET /api/partners` javobi:**

```json
{
  "partners": [
    {
      "id": 1,
      "name": "Otabek",
      "phone": "+998901234567",
      "note": null,
      "total_paid": "1500000",
      "last_payment_at": "2026-08-30"
    }
  ],
  "grand_total": "4200000"
}
```

`total_paid` bitta agregat so'rovda hisoblansin, N+1 qilma.

Egalik tekshiruvi: partner_id foydalanuvchiga tegishli emas bo'lsa 404.

---

## 2. Frontend

### 2.1. Kirish nuqtasi

Profilda `Brigada` qatori — hozir "Tez orada" yozuvi bilan. Uni olib
tashlab, bosiladigan qilib qo'y. `/partners` sahifasiga o'tadi.

### 2.2. Ro'yxat sahifasi `/partners`

```
Brigada

  Jami berilgan: 4 200 000 so'm
  ─────────────────────────────

  ┌──────────────────────────────────┐
  │ [O]  Otabek                      │
  │      +998 90 123 45 67           │
  │      Oxirgi: 30 avg              │
  │                    1 500 000 so'm│
  └──────────────────────────────────┘

  [ + Sherik qo'shish ]
```

- Har karta bosilsa → sherik sahifasi
- Karta chegarasi neytral (`--border`), ichida rangli aksent yo'q —
  bu moliyaviy yozuv emas, oddiy ro'yxat
- Bo'sh holat: "Sheriklaringiz yo'q. Yordamchilarga bergan pullaringizni
  yozib boring." + `+ Sherik qo'shish`

Yuqorida `Jami berilgan` — barcha sheriklarga jami. Qarz emas, tarix
yig'indisi.

### 2.3. Sherik qo'shish varag'i

```
Sherik qo'shish

  Ismi        [ Otabek                 ]
  Telefon     [ +998 __ ___ __ __      ]  ixtiyoriy
  Izoh        [                        ]  ixtiyoriy

  [ Saqlash ]
```

Ism majburiy, qolgani ixtiyoriy.

### 2.4. Sherik sahifasi `/partners/{id}`

```
← Otabek

  ┌──────────────────────────────────┐
  │ Jami berilgan                    │
  │ 1 500 000 so'm                   │
  │ ────────────────                 │
  │ 5 ta to'lov · oxirgi: 30 avg     │
  └──────────────────────────────────┘

  [ + To'lov qo'shish ]

  TO'LOVLAR

  30 avgust
  ┌──────────────────────────────────┐
  │ 500 000 so'm            [Naqd]   │
  │ Shanba uchun                     │
  └──────────────────────────────────┘

  25 avgust
  ┌──────────────────────────────────┐
  │ 300 000 so'm            [Karta]  │
  └──────────────────────────────────┘

  Yuqorida uch nuqta → Tahrirlash / O'chirish
```

Karta bosilganda batafsil varaq: tahrirlash / o'chirish.

### 2.5. To'lov qo'shish varag'i

```
+ To'lov qo'shish (Otabek)

  Summa      [ 500 000              ]
  Sana       [ 30.08.2026           ]
  Usul       [ Naqd ] [ Karta ] [ O'tkazma ]
  Izoh       [ Shanba uchun         ]  ixtiyoriy

  [ Saqlash ]
```

`MoneyInput` ishlatilsin. Sana standart bugun.

### 2.6. Xatti-harakat

- Optimistik yangilanish: to'lov qo'shilishi bilan ro'yxatda ko'rinsin
- Sherik o'chirilsa to'lovlari ham (CASCADE)
- O'chirishdan oldin `WebApp.showConfirm`: "Otabek va uning 5 ta to'lovi
  o'chiriladi"

---

## 3. Nima ko'rsatilmaydi

Bu bo'lim boshqa hech qayerga ta'sir qilmasligi kerak:

- Asosiy ekrandagi "Mijoz qarzi" ga qo'shilmasin
- Tarix ekranida ko'rinmasin
- PDF hisobotlarida chiqmasin
- `GET /api/projects/{id}/summary` ga ta'sir qilmasin

Bu ustaning **shaxsiy** hisobi. Mijozning bunga aloqasi yo'q.

---

## Qabul mezoni

```bash
cd frontend && npm run build && npm run lint
docker compose exec api alembic upgrade head
docker compose exec api ruff check app scripts
```

Qo'lda:

1. Profildan Brigada bosilsa yangi sahifa ochiladi
2. Sherik qo'shiladi, unga to'lov yoziladi
3. Sherik sahifasida jami va tarix ko'rinadi
4. To'lov o'chirilsa jami avtomatik yangilanadi
5. Sherik o'chirilsa to'lovlari ham yo'qoladi
6. Asosiy ekran va Tarix o'zgarmagan — brigada u yerda ko'rinmaydi
7. PDF hisobotida brigada ma'lumoti yo'q

## Nima QILMA

- Yordamchilar uchun login yaratma
- Obyektga bog'lama
- Hisobot va PDF ga qo'shma
- "Sherik qarzi" hisoblama — bu tarix, qarz emas
