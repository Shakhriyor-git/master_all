# Vazifa 08 — Sinovdan keyingi tuzatishlar

Ilova serverda ishlayapti, haqiqiy sinovdan o'tdi. Quyidagi beshta narsa aniqlandi.

Tartib: 1 va 2 shoshilinch (xato), 3 va 4 muhim (UX), 5 kichik.

---

## 1. Qaydlar darhol yangilanmaydi

**Muammo:** qayd elementini qo'shish yoki o'chirishda ekran o'zgarmaydi.
Orqaga chiqib qayta kirgandagina yangi holat ko'rinadi.

**Sabab:** TanStack Query keshi mutatsiyadan keyin yangilanmayapti.

**Tuzatish** — `hooks/useNotes.ts` dagi barcha mutatsiyalar uchun:

- `onMutate` da optimistik yangilanish: kesh darhol o'zgaradi
- `onError` da orqaga qaytarish (`context` bilan)
- `onSettled` da `invalidateQueries`

Bu quyidagilarga qo'llanilsin:
- element qo'shish / o'chirish / belgilash / tartibini o'zgartirish
- qayd sarlavhasi va matni (autosave)
- `is_pinned` o'zgarishi
- qaydni o'chirish

Belgilash (`is_done`) ayniqsa muhim — usta do'konda turib bosadi, javob
darhol ko'rinishi kerak.

Xuddi shu tekshiruv boshqa ekranlarda ham o'tkazilsin: katalogda narx
tahrirlash, obyekt yaratish, yozuv o'chirish. Qayerda `invalidateQueries`
yo'q bo'lsa — qo'shilsin.

---

## 2. Mijoz to'lovlari Tarixda ko'rinmaydi

**Muammo:** mijoz pul bergani hech qayerda ko'rinmaydi. Faqat summada
hisoblanadi, lekin "qachon, qancha, qanday" — yo'q.

**Tuzatish — backend.** Yangi endpoint:

```
GET /api/projects/{id}/timeline?kind=&date_from=&date_to=&page=
```

`entries` va `payments` ni birlashtirib, sanaga qarab teskari tartibda qaytaradi.
Har element `kind` maydoni bilan ajratiladi:

```json
{
  "items": [
    {
      "type": "entry", "id": 12, "kind": "material",
      "name": "Sement", "quantity": "5", "unit_label": "qop",
      "unit_price": "130000", "amount": "650000",
      "paid_by": "client", "payment_method": "card",
      "is_rework": false, "has_receipt": false,
      "entry_date": "2026-08-30", "created_at": "..."
    },
    {
      "type": "payment", "id": 3, "purpose": "budget",
      "amount": "1000000", "method": "cash",
      "note": "Avans", "paid_at": "2026-08-29", "created_at": "..."
    }
  ],
  "page": 1, "pages": 3, "total": 47
}
```

`kind` filtri qiymatlari: `work` · `material` · `expense` · `payment`.
Filtrsiz hammasi.

Bitta SQL da `UNION ALL` bilan, keyin `ORDER BY created_at DESC` va
sahifalash. Ikki alohida so'rov qilib Python'da birlashtirma —
sahifalash buziladi.

**Tuzatish — frontend.** `History.tsx`:

- Segment filtrga beshinchi variant: `To'lovlar`
- To'lov kartasi yozuv kartasidan **vizual farq qilsin**: ikonka `ti-cash-banknote`,
  fon `--success-soft`, summa `--success` rangda va oldida `+` belgisi
- To'lov kartasida: maqsad chipi (`Ish haqi uchun` / `Xarajat uchun`),
  usul chipi, izoh bo'lsa u ham
- Bosilganda batafsil varaq: tahrirlash va o'chirish

Asosiy ekranga ham to'rtinchi blok qo'shilsin: **Mijoz to'lovlari**,
oxirgi 3 tasi va `+ To'lov qo'shish` tugmasi.

---

## 3. Budjet qoldig'i yozuv qo'shishda ko'rinsin

**Muammo:** usta material qo'shayotganda "Mijoz" ni tanlaydi, lekin mijozning
puli qancha qolganini bilmaydi. Balans faqat keyin, hisobotda ko'rinadi.

**Tuzatish** — `Add.tsx` da, `Men / Mijoz` segmenti ostida:

`Mijoz` tanlangan bo'lsa jonli qator chiqsin:

```
Mijoz budjeti: 1 000 000 → 350 000 so'm qoladi
```

Chapda hozirgi qoldiq, o'ngda shu yozuvdan keyingi qoldiq.

Agar natija manfiy bo'lsa:

```
⚠️ Budjetdan 150 000 so'm oshib ketadi
```

`--danger` rangda, lekin **saqlashga to'sqinlik qilmasin** — mijoz naqd
qo'shimcha bergan bo'lishi mumkin, usta keyin kiritadi.

Budjet `0` bo'lsa: `Mijoz hali pul bermagan` + `Qo'shish` havolasi
(Budjet ekraniga olib boradi).

Xuddi shu qator **xarajat** oqimida ham bo'lsin.

Qoldiq `GET /api/projects/{id}/summary` dagi `budget.balance` dan olinadi.

---

## 4. Botni soddalashtirish

**Sabab:** endi Mini App bor. Botdagi ko'p qadamli inline oqimlar ortiqcha va
noqulay — bu haqiqiy sinovda tasdiqlandi.

**Qoladi:**

- `/start` — salomlashish + asosiy menyu
- `📋 Obyektlarim` — ro'yxat. Obyekt bosilganda **faqat o'qish uchun** karta:
  nom, mijoz, ish haqi, material, to'langan, qarz, budjet qoldig'i.
  Ostida bitta tugma: **`📱 Ilovada ochish`** (`web_app` tugmasi).
- `➕ Yangi obyekt` — nom → mijoz (o'tkazish mumkin) → saqlash → karta
- `❓ Yordam` — qisqa matn + ilovani ochish tugmasi

**O'chiriladi:**

- Ish / Material / Xarajat qo'shish oqimlari
- To'lov qo'shish
- Narxlar (katalog) boshqaruvi
- Oxirgini bekor qilish
- Hisobot (obyekt kartasida raqamlar bor, yetadi)

Tegishli handler, state va klaviatura fayllari **butunlay o'chirilsin** —
ishlatilmaydigan kod qoldirma. `states.py` da faqat `NewProject` qoladi.

Obyekt kartasidagi `web_app` tugmasi `settings.webapp_url` dan quriladi.

`/setcommands` uchun yangi ro'yxat (BotFather'ga men qo'lda kiritaman):
```
start - Boshlash
obyektlar - Obyektlarim
yordam - Yordam
```

---

## 5. Obyektni faol / tugagan qilish

**Muammo:** obyekt statusini o'zgartirish imkoni yo'q.

**Tuzatish** — Asosiy ekrandagi obyekt kartasi bosilganda ochiladigan
`ProjectPicker` varaqasida har bir obyekt yonida uch nuqta menyusi:

- `Tahrirlash` — nom, mijoz, telefon, manzil
- `Tugatildi` / `Qayta faollashtirish` — `status` ni `completed` ↔ `active`
- `O'chirish` — tasdiq bilan, soft delete

Varaqada ikki bo'lim: **Faol** va **Tugatilgan** (yig'ilgan holda, bosilganda ochiladi).

Tugatilgan obyekt Asosiy ekranda avtomatik tanlanmaydi, lekin Tarix va
Hisobotda ko'rish mumkin.

`PATCH /api/projects/{id}` allaqachon `status` ni qabul qiladi —
backend o'zgarishi kerak emas.

---

## Qabul mezoni

```bash
cd frontend && npm run build && npm run lint
docker compose exec api ruff check app scripts
docker compose logs bot          # xatosiz
```

Qo'lda tekshiriladi:

1. Qaydda element belgilansa — darhol o'zgaradi, orqaga chiqish shart emas
2. Tarixda mijoz to'lovi yashil `+` bilan ko'rinadi
3. Material qo'shishda `Mijoz` tanlansa — qoldiq jonli hisoblanadi
4. Botda faqat to'rt tugma qoladi, obyekt kartasida `Ilovada ochish` ishlaydi
5. Obyektni `Tugatildi` qilib, keyin qaytarish mumkin

## Nima QILMA

- OCR, ovoz, Excel — keyingi bosqich
- Brigada / rollar
- Yangi migratsiya (5 uchun sxema o'zgarmaydi; 2 uchun ham yangi jadval kerak emas)
