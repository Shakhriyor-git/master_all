# Vazifa 10 — To'lov maqsadi, qo'lda kiritish, AI kiritish va UI yangilash

Oltita qism. 1 va 2 xato tuzatish — avval shular.

---

# 1. To'lov maqsadi ishlamayapti

**Muammo:** barcha to'lovlar `Xarajat uchun` bo'lib saqlanyapti. Hisobotda
`Mijoz to'lagan ish haqi — 0` turibdi, holbuki mijoz ish haqi uchun ham
avans beradi.

**Tuzatish:** `To'lov qo'shish` oqimining **birinchi qadami** maqsad tanlash
bo'lsin, summadan oldin:

```
Pul nima uchun?
[ 💵 Ish haqi uchun ]   [ 🧾 Xarajat uchun ]
```

- `Ish haqi uchun` → `purpose: "labor"` → mijoz qarzini kamaytiradi
- `Xarajat uchun` → `purpose: "budget"` → budjetni to'ldiradi

Standart qiymat qo'yilmasin, usta ataylab tanlasin.

Tarix va Asosiy ekrandagi to'lov kartalarida maqsad chipi to'g'ri
ko'rsatilsin. Budjet ekranida faqat `purpose=budget` bo'lganlar chiqsin.

Backendda `purpose` allaqachon qabul qilinadi — muammo faqat frontendda,
lekin tekshirib chiqing: `POST /api/projects/{id}/payments` ga nima
yuborilyapti.

---

# 2. Tayyor katalog qaytariladi

09-vazifadagi qaror bekor qilinadi.

- `catalog_seed.py` da kategoriyalar va pozitsiyalar seed qilinishi
  **tiklansin** — yangi foydalanuvchi to'liq katalog bilan boshlasin
- `Xizmatlarim` ekranidagi `Tayyor katalog endi ishlatilmaydi…` banneri
  **butunlay olib tashlansin**
- `DELETE /api/price-items/seeded` va `DELETE /api/categories/seeded`
  endpointlari olib tashlansin

`Materiallar` tabida `N pozitsiya` yozuvi qoladi, `Ishlar` da `N xizmat` —
bu to'g'ri edi.

---

# 3. Qo'lda kiritish rejimi

**Sabab:** ba'zan usta katalogdagi hech narsaga bog'lamasdan, shunchaki
"nima oldim va qancha" deb yozishni xohlaydi.

`Add.tsx` da xizmat/pozitsiya ro'yxatining **eng tepasida**, qidiruv
maydoni ostida:

```
✏️  Qo'lda kiritish
```

Bosilganda quyidagi forma:

| Maydon | Holati |
|---|---|
| Nomi | majburiy |
| Miqdor | ixtiyoriy, bo'sh bo'lsa `1` |
| Birlik | ixtiyoriy, bo'sh bo'lsa `summa` |
| Summa | majburiy (`MoneyInput`) |
| Kim to'ladi | majburiy — `Men` / `Mijoz` |
| Qanday to'ladi | majburiy — `Naqd` / `Karta` / `O'tkazma` |
| Sana | standart bugun |
| Izoh | ixtiyoriy |

**Muhim:** bu yozuv katalogga **qo'shilmaydi**. `price_items` ga hech narsa
yozilmasin, `project_price_id` bo'sh qolsin.

Formaning pastida ixtiyoriy belgi: `☐ Katalogga ham qo'shilsin` — standart
holda o'chirilgan. Belgilansa, yozuv bilan birga `price_item` ham yaratiladi.

`Miqdor` to'ldirilsa, `Summa` ni birlik narxi sifatida emas, **jami** deb
tushunilsin: `unit_price = summa / miqdor`.

Xuddi shu rejim ish qo'shishda ham bo'lsin.

---

# 4. AI orqali matn bilan kiritish

**Maqsad:** usta yozadi — `oboy kley oldim 500 gram 30 000 mijoz to'ladi
kartadan` — tizim yozuvni to'ldirib beradi.

## 4.1. Kirish nuqtasi

`Add.tsx` ning eng tepasida, kategoriya chiplaridan oldin:

```
┌────────────────────────────────────────┐
│ ✨  Yozing yoki ayting…                │
│    "sement 5 qop 650 ming mijoz naqd"  │
└────────────────────────────────────────┘
```

Bitta matn maydoni. Yozib Enter bosadi yoki yon tomondagi tugmani bosadi.

## 4.2. Endpoint

```
POST /api/projects/{id}/ai-parse
{ "text": "oboy kley oldim 500 gram 30 000 mijoz to'ladi kartadan" }
```

Javob:

```json
{
  "kind": "material",
  "name": "Oboy kley",
  "quantity": "500",
  "unit": "gram",
  "amount": "30000",
  "paid_by": "client",
  "payment_method": "card",
  "matched_price_item_id": null,
  "confidence": "high"
}
```

## 4.3. Prompt

Kontekst sifatida beriladi: loyihaning `project_prices` (id va nom),
foydalanuvchining faol birliklari (`code` ro'yxati).

```
Sen qurilish ustasining yordamchisisan. Usta o'zbek tilida (rus so'zlari
aralash bo'lishi mumkin) nima qilgani yoki nima olganini yozadi.
Uni tuzilgan yozuvga aylantir.

Faqat JSON qaytar, markdown va izohsiz:

{
  "kind": "work | material | expense",
  "name": "...",
  "quantity": "raqam yoki null",
  "unit": "birlik kodi yoki null",
  "amount": "JAMI summa, faqat raqam",
  "paid_by": "master | client | null",
  "payment_method": "cash | card | transfer | null",
  "matched_price_item_id": null,
  "confidence": "high | low"
}

Qoidalar:
- amount har doim JAMI summa. Usta bir birlik narxini aytsa,
  miqdorga ko'paytir.
- kind: bajarilgan ish bo'lsa "work", sotib olingan mol bo'lsa
  "material", ovqat/transport/ijara bo'lsa "expense".
- unit: quyidagi kodlardan birini tanla. Mos kelmasa aytilgan
  so'zni o'zini yoz.
- Katalogda mos pozitsiya bo'lsa matched_price_item_id ga uning
  id sini yoz, bo'lmasa null.
- Aytilmagan narsani o'ylab topma — null qoldir.
- Tushunmasang: {"error": "sabab"}

BIRLIKLAR: m2, m3, dona, qop, metr, kg, litr, soat, kunlik, tochka, ...
KATALOG:
12 — Sement
15 — Oboy kley
```

## 4.4. Serverda tekshirish

- `amount` `Decimal` ga o'giriladi, `<= 0` bo'lsa `confidence: low`
- `quantity` bo'lsa `unit_price = amount / quantity`, aks holda
  `quantity = 1`, `unit_price = amount`
- `matched_price_item_id` **shu foydalanuvchiniki ekani tekshiriladi** —
  model o'ylab topgan id qabul qilinmasin, `null` ga aylantirilsin
- `unit` foydalanuvchining birliklarida bo'lmasa ham qabul qilinadi
  (birlik maydoni erkin matn), lekin katalogga qo'shilmaydi

## 4.5. Natija

Tasdiqlash kartasi chiqadi — 3-bo'limdagi qo'lda kiritish formasi,
lekin **oldindan to'ldirilgan**. Usta ko'radi, kerak bo'lsa tuzatadi,
`Saqlash` bosadi.

To'liq avtomatik saqlanmaydi. Sabab: "500 gram 30 000" iborasida 30 000
jami summami yoki birlik narximi — model ba'zan adashadi. Bitta bosish
arzon, noto'g'ri yozuvni keyin topish qimmat.

`confidence: low` bo'lsa tepada sariq chiziq: `⚠️ Tekshirib chiqing`.

Model tushunmasa (`error`) — bo'sh qo'lda kiritish formasi ochiladi,
yozilgan matn `Nomi` maydoniga qo'yiladi.

---

# 5. Chek o'qish (OCR)

4-bo'limdagi bilan **bir xil xizmat**, faqat kirish rasm.

## 5.1. Kirish nuqtasi

Material oqimida, AI matn maydoni yonida kamera ikonkasi.
`<input type="file" accept="image/*" capture="environment">`.

## 5.2. Endpoint

```
POST /api/projects/{id}/receipt-scan   (multipart)
```

Javob:

```json
{
  "vendor": "Qurilish bozori",
  "receipt_date": "2026-08-29",
  "amount": "850000",
  "confidence": "high",
  "note_text": "Sement M400 5 qop × 130 000\nGips 3 qop × 45 000"
}
```

## 5.3. Oqim

1. jpg/png/webp, maksimum 8 MB. Frontendda `canvas` bilan 1400 px ga
   siqiladi, JPEG 0.85
2. Pillow bilan serverda ham qayta siqiladi (himoya uchun)
3. Gemini'ga yuboriladi
4. **Rasm diskka yozilmaydi**, xotirada ishlanadi va tashlab yuboriladi

Prompt sodda — katalogga moslash yo'q, chunki bitta chek bitta yozuv
bo'ladi:

```
Rasmda O'zbekistondagi qurilish do'koni cheki bor. Matn o'zbek, rus
yoki aralash.

Faqat JSON qaytar:
{
  "vendor": "do'kon nomi yoki null",
  "receipt_date": "YYYY-MM-DD yoki null",
  "amount": "JAMI summa, faqat raqam",
  "confidence": "high | low",
  "items": [{"name": "...", "quantity": "...", "unit": "...",
             "unit_price": "...", "amount": "..."}]
}

- Chekda jami summa yozilgan bo'lsa o'shani ol. Yo'q bo'lsa mollarni qo'sh.
- Rasm chek emas yoki o'qib bo'lmasa: {"error": "sabab"}
- Taxmin qilma, ishonching past bo'lsa confidence: "low"
```

`note_text` serverda `items` dan yig'iladi:
`Nom miqdor birlik × narx`, qatorlar `\n` bilan.

## 5.4. Tasdiqlash

Qo'lda kiritish formasi, to'ldirilgan holda:

- `Nomi` → chekda bitta mol bo'lsa o'sha nom, ko'p bo'lsa `Qurilish mollari`
- `Summa` → `amount`
- `Sana` → `receipt_date`
- `Izoh` → `note_text` (tahrirlanadi)
- `vendor` alohida maydonda

## 5.5. Xato

```
Chekni o'qib bo'lmadi.
Yorug'roq joyda, tekis qilib qayta suratga oling.

[ Qayta urinish ]   [ Qo'lda kiritish ]
```

---

# 6. AI uchun umumiy sozlash

`app/services/ai_parse.py` — matn va rasm uchun bitta modul.

`.env`:

```
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
AI_DAILY_LIMIT=50
```

`requirements.txt`: `google-genai==1.38.0`

## Kunlik limit

Yangi kichik jadval:

```
ai_usage(id, user_id FK, day DATE, count INT)
UNIQUE (user_id, day)
```

Matn va rasm birga hisoblanadi. Limitdan oshsa `429` va xabar:
`Bugungi AI limiti tugadi (50). Qo'lda kiritishingiz mumkin.`

## Boshqa qoidalar

- Chaqiruv faqat backendda — API kalit hech qachon frontendga tushmasin
- `run_in_threadpool`, timeout 25 soniya
- Xato bo'lsa traceback logda, foydalanuvchiga umumiy xabar
- Javob JSON emas bo'lsa yoki parse bo'lmasa → `422`

---

# 7. UI yangilash

Interfeys hozir juda quruq. Quyidagilar qo'shilsin, lekin **o'lchov bilan** —
usta uchun tezlik chiroylikdan muhimroq.

## 7.1. Ikonkalar

Hozirgi ikonkalar bir xil va yupqa. `@tabler/icons-react` dan **to'ldirilgan
(filled)** variantlarga o'tilsin, o'lcham 22-24 px.

Pastki navigatsiyada faol tab ikonkasi to'ldirilgan, nofaollari chiziqli.

Kategoriya kartalaridagi emoji qoladi — u issiqroq ko'rinadi.

## 7.2. Gradientlar

Faqat **ikki joyda**, boshqa hech qayerda:

- **Asosiy ekrandagi obyekt kartasi:**
  light: `linear-gradient(135deg, #2563EB, #4F8AF5)`
  dark: `linear-gradient(135deg, #8B5CF6, #A78BFA)`
- **Profil sarlavhasi** — xuddi shu gradient, pastga qarab shaffoflashadi

Tugmalarda, oddiy kartalarda, fonda gradient bo'lmasin.

## 7.3. Animatsiyalar

`framer-motion` bilan, hammasi 150-250 ms:

- **Ekran o'tishi:** o'ngdan chapga sirg'alish (12 px + fade)
- **Ro'yxat:** kartalar ketma-ket chiqadi, har biriga 30 ms kechikish,
  faqat birinchi yuklanishda
- **Bosish:** `scale(0.97)`, 100 ms
- **Raqamlar:** Asosiy ekrandagi katta summalar 400 ms da sanab chiqadi
  (`0 → 660 000`). Faqat asosiy karta va yakuniy hisob raqamlarida,
  ro'yxatdagi har bir summada emas
- **Yangi yozuv:** ro'yxatga qo'shilganda yashil fon bilan yonib o'chadi
- **Varaq (bottom sheet):** pastdan chiqadi, orqa fon xiralashadi

**Cheklovlar:** `prefers-reduced-motion` hurmat qilinsin.
Doimiy takrorlanuvchi (loop) animatsiya faqat yuklanish indikatorida.
Aylanuvchi, sakrab turuvchi, pulsatsiya qiluvchi bezaklar bo'lmasin.

## 7.4. Profil ekrani

Qayta ishlansin:

```
┌────────────────────────────────┐
│   [gradient fon]               │
│        ( avatar )              │
│        Shahriyor               │
│     +998 91 660 01 06          │
│        Tahrirlash              │
└────────────────────────────────┘

   ┌────────┐   ┌────────┐
   │   1    │   │   0    │
   │  Faol  │   │Tugadi  │
   └────────┘   └────────┘

MENING SAHIFALARIM
  📷  Instagram          ›
  ✈️  Telegram kanal     ›
  + Havola qo'shish

  🔧  Xizmatlarim        ›
  📝  Qaydlarim          ›
  👥  Brigada    Tez orada
```

Avatar gradient halqa ichida, 88 px.

## 7.5. Ijtimoiy havolalar

`users` jadvaliga ustun:

| Ustun | Tur |
|---|---|
| social_links | JSONB, NOT NULL, default `'[]'` |

Format: `[{"label": "Instagram", "url": "https://instagram.com/..."}]`
Maksimum 5 ta.

`PATCH /api/me` orqali tahrirlanadi. Alembic migratsiyasi kerak.

**Frontend:** `Havola qo'shish` bosilganda varaq ochiladi — turi tanlanadi
(Instagram, Telegram, YouTube, Veb-sayt, Boshqa) va manzil kiritiladi.
Har havolada uzun bosish yoki uch nuqta → `Tahrirlash` / `O'chirish`.

Havola bosilganda `Telegram.WebApp.openLink` bilan ochiladi.

`url` serverda tekshirilsin: `https://` bilan boshlanishi shart,
maksimum 300 belgi.

---

## Qabul mezoni

```bash
docker compose exec api alembic upgrade head
docker compose exec api ruff check app scripts
cd frontend && npm run build && npm run lint
```

Qo'lda:

1. To'lov qo'shishda maqsad so'raladi, `Ish haqi uchun` tanlansa
   hisobotdagi `Mijoz to'lagan ish haqi` o'zgaradi
2. `Qo'lda kiritish` bilan yozuv qo'shiladi, katalogga qo'shilmaydi
3. `sement 5 qop 650 ming mijoz naqd` yozilsa to'g'ri to'ldiriladi
4. Chek surati o'qiladi, jami summa to'g'ri chiqadi
5. Profilda Instagram havolasi qo'shiladi va ochiladi
6. Animatsiyalar sezilarli, lekin ko'zni charchatmaydi

## Nima QILMA

- Ovoz bilan bog'liq hech narsa — keyingi bosqich
- Rasmni saqlama
- Botga tegma
- Gradientni ikki joydan boshqasiga qo'yma
