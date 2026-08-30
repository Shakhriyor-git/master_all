# Vazifa 06 — Telegram Mini App (React)

## Maqsad

Usta uchun asosiy interfeys. Bot zaxira bo'lib qoladi, kundalik ish shu yerda
bo'ladi. Foydalanuvchi — qo'li iflos, qo'lqopda, quyosh ostida turgan usta.
Har bir ortiqcha bosish tashlab ketish sababi.

## Shart

05-vazifa (A va B) tugagan: kategoriyalar, birliklar, budjet, qaydlar API si ishlaydi.

**Vazifa katta. Uch bosqichda bajar, har biridan keyin TO'XTA va natijani ko'rsat:**

- **A:** backend qo'shimchalari + loyiha skeleti + mavzu tizimi + auth + navigatsiya
- **B:** Asosiy, Tarix, Qo'shish ekranlari
- **C:** Profil, Xizmatlarim, Budjet, Qaydlar, Sozlamalar

---

# A BOSQICH

## A1. Backend qo'shimchalari

### `users` jadvaliga

| Ustun | Tur |
|---|---|
| theme | VARCHAR(10), NOT NULL, default 'auto' | light / dark / auto |
| avatar_path | VARCHAR(300), NULL | yuklangan rasm yo'li |

Alembic migratsiyasi.

### Yangi endpointlar

```
GET   /api/me            joriy foydalanuvchi + statistika
PATCH /api/me            full_name, phone, theme, language
POST  /api/me/avatar     multipart rasm yuklash
DELETE /api/me/avatar    o'chirish, Telegram rasmiga qaytish
```

`GET /api/me` javobi:
```json
{
  "id": 1, "full_name": "Sherzod aka", "username": "sherzod",
  "phone": "+998901234567", "language": "uz", "theme": "auto",
  "avatar_url": "/media/avatars/1_a3f9.jpg",
  "active_projects": 1, "completed_projects": 12
}
```

Avatar: `/data/avatars/` volumiga saqlansin (docker-compose ga named volume qo'sh),
`/media/avatars/` orqali statik berilsin. Maksimum 5 MB, faqat jpg/png/webp,
saqlashdan oldin 512×512 ga siqilsin (Pillow qo'sh — `requirements.txt` ga
`pillow==11.0.0`). Obyekt saqlash (R2) keyingi bosqichda.

`avatar_url` bo'sh bo'lsa frontend Telegram rasmini ishlatadi.

### Katalog uchun ommaviy tahrirlash

Narxlar 0 turgani asosiy muammo. Bitta-bitta tahrirlash uzoq:

```
PATCH /api/price-items/bulk   [{id, default_price}, ...]
```

Bir so'rovda 50 tagacha pozitsiya narxini yangilaydi. Egalik tekshiriladi.

### CORS

`.env` da `CORS_ORIGINS` ga `http://localhost:5173` qo'shilsin.

## A2. Frontend skeleti

**Stack:** Vite + React 18 + TypeScript · TanStack Query · React Router ·
Tailwind CSS · `@twa-dev/sdk` · `framer-motion` (faqat oddiy o'tishlar uchun).

Redux, MUI, Bootstrap ishlatma.

`frontend/` papkasida, repo ildizida. `docker-compose` ga qo'shma — lokalda
`npm run dev` bilan alohida ishlasin, tezroq.

`.env.local`: `VITE_API_URL=http://localhost:8000`

## A3. Mavzu tizimi — diqqat bilan

Ikki mavzu. Foydalanuvchi Sozlamalardan tanlaydi: `light` / `dark` / `auto`
(`auto` — Telegram `colorScheme` iga ergashadi). Tanlov `PATCH /api/me` orqali
serverga saqlanadi.

CSS o'zgaruvchilari, `<html data-theme="light|dark">` atributi bilan almashadi.

**Muhim qoida:** hech qayerda rang qotirilmasin. Har bir rang o'zgaruvchi orqali
o'qilsin. Bitta ekran ham "har doim qora" yoki "har doim oq" bo'lmasin — profil
ekrani ham tanlangan mavzuga bo'ysunadi.

### Kunduzgi (light) — oq va azure blue

```css
--bg:            #F5F6F8
--surface:       #FFFFFF
--surface-2:     #EEF1F5
--primary:       #2563EB
--primary-soft:  #DCE7FD
--on-primary:    #FFFFFF
--text:          #1E293B
--text-muted:    #757681
--text-faint:    #9AA0AA
--accent:        #BC4800
--accent-soft:   #FBE3DA
--success:       #0B5C3E
--success-soft:  #D6F0E4
--danger:        #C0392B
--danger-soft:   #FBE0DC
--border:        #E2E6EC
```

### Tungi (dark) — qora va purple

```css
--bg:            #0B0B10
--surface:       #16161F
--surface-2:     #1F1F2B
--primary:       #8B5CF6
--primary-soft:  #2A1F4A
--on-primary:    #FFFFFF
--text:          #F1F1F5
--text-muted:    #9A9AA8
--text-faint:    #6E6E7C
--accent:        #E2703A
--accent-soft:   #3A2418
--success:       #6FE0B0
--success-soft:  #14382B
--danger:        #E5564A
--danger-soft:   #3A1D1A
--border:        #2A2A38
```

**Tipografika:** Inter. Uch o'lcham:
sarlavha 20px/500 · matn 15px/400 · yorliq 12px/500 `--text-muted`.

**Radius:** kartalar 16px, tugmalar 12px, chip 999px. Soya yo'q — chegara bilan.

**Kontrast tekshiruvi:** har bir matn/fon juftligi ikkala mavzuda ham kamida
4.5:1 bo'lsin. Rangli fondagi matn hech qachon oddiy qora yoki oq bo'lmasin —
o'sha rang oilasining eng to'q yoki eng och tonini ishlat.

## A4. Telegram SDK

- `WebApp.ready()` va `WebApp.expand()` ochilganda
- `WebApp.MainButton` — formalarda asosiy amal ("Saqlash"). O'z tugmangni yasama.
- `WebApp.BackButton` — ichki ekranlarda
- `WebApp.HapticFeedback.impactOccurred('medium')` — har muvaffaqiyatli saqlashda
- `WebApp.showConfirm()` — o'chirishdan oldin
- `WebApp.setHeaderColor` / `setBackgroundColor` — mavzuga moslab

## A5. Auth

Har so'rovda: `Authorization: tma <WebApp.initData>`

`initData` ni frontend o'zi parse qilmasin. Foydalanuvchi ma'lumoti manbai —
faqat `GET /api/me`.

Telegram tashqarisida ochilsa (`initData` bo'sh) — "Bu ilovani Telegram orqali
oching" ekrani. Oq ekran qoldirma.

## A6. Navigatsiya

Pastda 4 ta tab: **Asosiy · Tarix · Profil · Sozlamalar**
O'rtada suzuvchi `+` tugmasi — tez qo'shish.

Faol tab `--primary` bilan belgilanadi.

## A bosqich qabul mezoni

```bash
cd frontend && npm run build && npm run lint
```

Brauzerda `localhost:5173` → "Telegram orqali oching" ekrani.
Mavzu almashtirish ishlaydi (vaqtincha debug tugmasi bilan sinash mumkin).

**TO'XTA, natijani ko'rsat.**

---

# B BOSQICH

## B1. Asosiy (Dashboard)

Yuqorida faol obyekt kartasi (`--primary` fonda): nomi, mijoz, ikki raqam —
**Jami ish haqi** va **Jami xarajat**.

Obyekt bittadan ko'p bo'lsa karta bosilganda tanlash varaqasi (bottom sheet).

Ostida uch blok, har birida oxirgi 3 ta yozuv va "Barchasi" havolasi:
- **Bajarilgan ishlar**
- **Materiallar**
- **Xarajatlar** (bo'sh bo'lsa ko'rsatilmasin)

Har blok ostida punktir tugma: `+ Ish qo'shish` / `+ Material` / `+ Xarajat`.

Eng pastda ikki kichik karta: **Mijoz qarzi** va **Budjet qoldig'i**.
Qarz manfiy bo'lsa "Mijoz avansi" deb yozilsin, minussiz.

## B2. Tarix

Bu ekran alohida e'tibor talab qiladi — usta uni mijozga ko'rsatadi.

**Yuqorida:** loyiha tanlagich + segment filtr `Barchasi · Ishlar · Material · Xarajat`.

**Ro'yxat kun bo'yicha guruhlangan:** `BUGUN · 30 AVGUST`, `KECHA`, `28 AVGUST`...

**Har bir yozuv kartasi quyidagilarni ko'rsatadi:**

```
┌────────────────────────────────────────┐
│ [ikon]  Sement M400          450 000   │
│         10 qop × 45 000 so'm           │
│ ─────────────────────────────────────  │
│ [Mijoz to'ladi] [Naqd]           14:30 │
└────────────────────────────────────────┘
```

- Ikon turi bo'yicha: ish → `ti-tool`, material → `ti-package`, xarajat → `ti-receipt`
- Ikon foni: ish → `--primary-soft`, material → `--accent-soft`, xarajat → `--surface-2`
- Summa rangi: ish → `--primary`, material → `--accent`, xarajat → `--text-muted`
- Chip "Mijoz to'ladi" → `--success-soft`, "Usta to'ladi" → `--surface-2`
- To'lov usuli chipi ikonka bilan: naqd `ti-cash`, karta `ti-credit-card`,
  o'tkazma `ti-building-bank`
- Brak yozuvi: `⚠️ Brak` chipi `--danger-soft`, summa ustidan chizilgan
- Chek bor bo'lsa `ti-photo` ikonkasi

**Kartani bosganda** pastdan varaq ochiladi: to'liq ma'lumot, sotuvchi, izoh,
chek rasmi, `Tahrirlash` va `O'chirish` tugmalari.

**Chapga surilganda** tez o'chirish (tasdiq bilan).

Sahifalash: pastga tushganda avtomatik yuklash (infinite scroll), 20 tadan.

## B3. Qo'shish (`+` tugmasi)

Pastdan varaq ochiladi, uchta katta tugma: **Ish · Material · Xarajat**.

### Ish / Material oqimi — bitta ekranda, qadam-baqadam ochiladi

1. **Kategoriya** — gorizontal chiplar qatori. Bosilganda ostidagi ro'yxat
   filtrlanadi. Kategoriya bitta bo'lsa yashiriladi.
2. **Xizmat** — qidiruv maydoni + ro'yxat. Yozila boshlanganda filtrlanadi.
   Oxirida `+ Yangi qo'shish`.
3. **Miqdor** — katta raqamli maydon, ostida birlik yorlig'i.
   Yon tomonda tez tugmalar: `1` `5` `10` `+1` `−1`.
4. **Material bo'lsa:** kim to'ladi (`Men` / `Mijoz`) → qanday to'ladi
   (`Naqd` / `Karta` / `O'tkazma`) — segment tanlov, ikki qator.
5. **Natija** pastda jonli hisoblanadi: `15 m² × 80 000 = 1 200 000 so'm`
6. Telegram MainButton: `Saqlash`

Narxi 0 bo'lgan xizmat tanlansa — darrov narx so'ralsin, keyin davom etsin.

### Xarajat oqimi

Nomi (tez tugmalar: `Tushlik` `Taksi` `Asbob` `Boshqa`) → summa →
kim to'ladi → qanday to'ladi.

## B4. Raqam kiritish — muhim

Botda `20,000` `20` bo'lib ketgan. Web App'da bu takrorlanmasligi kerak.

**Yechim:** maydonga yozilayotganda avtomatik formatlansin.
Usta `20000` yozadi → ekranda darrov `20 000` chiqadi.

- `inputMode="numeric"` (pul) / `inputMode="decimal"` (miqdor)
- Faqat raqam qabul qilinadi; vergul va nuqta miqdor maydonida kasr ajratuvchi
- Har uch xonaga bo'shliq qo'yiladi, kursor joyida qoladi
- Serverga toza son yuboriladi
- Pul maydonida kasr umuman kiritilmaydi

## B bosqich qabul mezoni

`npm run build` toza. Telegramda ochilib, ish/material/xarajat qo'shiladi,
Tarix'da to'g'ri ko'rinadi.

**TO'XTA, natijani ko'rsat.**

---

# C BOSQICH

## C1. Profil

Yuqorida: avatar (bosilganda o'zgartirish), ism (tahrirlanadi), telefon.
Avatar tanlash: `Telegram rasmim` yoki `Galereyadan yuklash`.

Ikki metrik karta: **Faol obyektlar** / **Tugatilgan**.

Ostida havolalar:
- **Xizmatlarim** (narx katalogi) →
- **Qaydlarim** →
- **Brigada** — `Tez orada` yorlig'i bilan, bosilmaydi

## C2. Xizmatlarim — katalog boshqaruvi

Bu hozir eng yomon holatda, alohida e'tibor bering.

**Birinchi ekran:** yuqorida segment `Ishlar / Materiallar`, ostida
**ikki ustunli kategoriya kartalari**:

```
┌──────────────┐  ┌──────────────┐
│      🏠      │  │      ⚡      │
│    Shift     │  │  Elektrika   │
│  5 xizmat    │  │  6 xizmat    │
│  2 narxsiz   │  │  narx to'liq │
└──────────────┘  └──────────────┘
```

Narxi 0 bo'lgan pozitsiyalar soni `--danger` rangda ko'rsatilsin — usta
qayerda ish qolganini darrov ko'radi.

Oxirida punktir karta: `+ Yangi kategoriya`.

**Kategoriya ochilganda:** xizmatlar ro'yxati. Har qator: nom, birlik, narx.
Narx **inline tahrirlanadi** — bosadi, klaviatura chiqadi, yozadi, keyingisiga
o'tadi. Alohida ekran ochilmaydi.

Yuqorida tugma: `Barcha narxlarni to'ldirish` — narxi 0 bo'lganlarni ketma-ket
so'raydi, `PATCH /api/price-items/bulk` bilan bitta so'rovda saqlaydi.

Har qatorda uchta nuqta: `Tahrirlash` / `Boshqa kategoriyaga` / `O'chirish`.

Oxirida: `+ Yangi xizmat` — nom → birlik (tanlov + `Yangi birlik`) → narx.

## C3. Budjet

Obyekt kartasidan yoki Asosiy ekrandagi budjet kartasidan ochiladi.

Yuqorida uch raqam: **Berilgan · Sarflangan · Qoldiq**.
Qoldiq katta shriftda, manfiy bo'lsa `--danger`.

Tugma: `+ Mijoz pul berdi` → summa → sana → izoh.

Ostida shu budjetdan sarflangan yozuvlar ro'yxati (Tarix bilan bir xil karta
ko'rinishi, faqat `paid_by = client` bo'lganlar).

Bo'sh bo'lsa: "Mijoz hali pul bermagan" + darrov qo'shish tugmasi.

## C4. Qaydlar

Ro'yxat: qadalganlar tepada. Har karta: sarlavha, matnning birinchi qatori,
belgilangan/jami ro'yxat elementi soni.

Ochilganda: sarlavha + matn maydoni (avtomatik saqlanadi, 1 soniya kechikish
bilan) + belgilanadigan ro'yxat. Element qo'shish, belgilash, surib tartiblash.

Loyihaga bog'lash ixtiyoriy.

## C5. Sozlamalar

- **Mavzu:** `Kunduzgi / Tungi / Avtomatik` — segment, darrov qo'llanadi,
  `PATCH /api/me` ga saqlanadi
- **Til:** O'zbekcha (rus tili keyin, hozir o'chirilgan)
- **Bildirishnomalar:** toggle (hozircha faqat UI)
- Pastda: versiya raqami

## Umumiy talablar

**Yuklanish:** skeleton kartalar, spinner emas.

**Bo'sh holat:** "Hali ish qo'shilmagan" + darrov qo'shish tugmasi. Bo'sh ekran yo'q.

**Xato:** "Internet yo'q, qayta urinish" tugmasi bilan. Texnik matn ko'rsatilmasin.

**Optimistik yangilanish:** yozuv saqlanganda ro'yxatda darrov ko'rinsin.
Xato bo'lsa orqaga qaytarilsin va xabar berilsin.

**Animatsiya:** faqat foydali. Varaq pastdan chiqishi, kartaning bosilishda
`scale(0.98)`, ro'yxatga yangi element qo'shilganda qisqa `fade+slide`.
Bezak animatsiya qo'shma — usta uchun tezlik muhimroq.

**Bosish maydoni** minimum 44×44px.

**Ranglar ma'no tashiydi**, lekin faqat rangga tayanma — matn bilan ham
ajratilsin. Quyoshda ekran yomon ko'rinadi.

## C bosqich qabul mezoni

`npm run build` toza. Ikkala mavzuda ham hamma ekran o'qiladi.
Katalogda narx to'ldirish 10 pozitsiya uchun 1 daqiqadan kam vaqt oladi.

## Nima QILMA

- OCR, AI vision, ovoz — keyingi bosqich
- Excel hisobot
- Brigada / rollar
- Mijoz uchun alohida ko'rinish
- Push bildirishnoma mantig'i
- Modellarni o'zgartirma (`users.theme`, `users.avatar_path` dan boshqa)
- Botni o'zgartirma
