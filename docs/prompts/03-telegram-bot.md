# Vazifa 03 — Telegram bot (Mini App'siz ishlaydigan MVP)

## Maqsad

Usta faqat bot orqali to'liq ishlay olsin: obyekt ochsin, ish va material yozsin,
to'lov qayd qilsin, hisobotni ko'rsin. Mini App keyingi bosqichda — hozir kerak emas.

## Shart

02-vazifa tugagan: modellar, auth, CRUD API, `summary` xizmati ishlaydi.

## Arxitektura

Bot API bilan HTTP orqali gaplashmasin — **bevosita bazaga yozsin**, xuddi shu
kodbazadagi modellar va `app/services/summary.py` orqali. Ortiqcha tarmoq qatlami kerak emas.

Ikki rejim:

- **Lokal (hozir):** polling. HTTPS domen kerak emas.
- **Prod (keyin):** webhook, FastAPI ichida. Hozir faqat tayyorlab qo'y, yoqma.

`settings.bot_use_webhook` shuni boshqaradi. Lokalda `false`.

### Fayllar

```
app/bot/
  __init__.py
  loader.py        Bot, Dispatcher, MemoryStorage
  middlewares.py   DbSessionMiddleware, UserMiddleware
  keyboards.py     ReplyKeyboard va InlineKeyboard yasovchi funksiyalar
  states.py        FSM holatlari
  utils.py         summa formatlash, sana formatlash
  handlers/
    __init__.py    router'larni yig'adi
    start.py
    projects.py
    entries.py
    payments.py
    reports.py
    prices.py
  polling.py       lokal ishga tushirish nuqtasi
```

### docker-compose.yml ga qo'shimcha

Yangi `bot` servisi, faqat lokal uchun:

```yaml
  bot:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/code
    command: python -m app.bot.polling
```

## Middleware

**DbSessionMiddleware** — har bir update uchun `SessionLocal()` ochadi,
`data["session"]` ga qo'yadi, oxirida yopadi.

**UserMiddleware** — `event.from_user.id` bo'yicha `User` topadi, yo'q bo'lsa
yaratadi (`full_name`, `username` Telegram'dan olinadi), `data["user"]` ga qo'yadi.

Bu yerda `initData` tekshiruvi **kerak emas** — Telegram bot API'dan kelgan
`from_user` allaqachon ishonchli. `initData` faqat Mini App uchun.

## Oqimlar

### /start

Foydalanuvchini ro'yxatdan o'tkazadi, salomlashadi va asosiy menyuni ko'rsatadi.

Asosiy menyu — ReplyKeyboard (pastdagi doimiy tugmalar):
```
[ 📋 Obyektlarim ]  [ ➕ Yangi obyekt ]
[ 💰 Narxlarim  ]  [ ❓ Yordam      ]
```

### Yangi obyekt

FSM: `title` → `client_name` (o'tkazib yuborish mumkin) → saqlash → obyekt kartasi.

Har qadamda "Bekor qilish" tugmasi bo'lsin.

### Obyektlarim

Faol obyektlar ro'yxati, har biri inline tugma. Bosilganda obyekt kartasi:

```
🏠 Chilonzor 12-uy, 45-xonadon
Mijoz: Aziz aka

Ishlar:      2 080 000 so'm
Material:      540 000 so'm
To'langan:   2 000 000 so'm
─────────────────────
Qarz:           80 000 so'm
```

Ostida inline tugmalar:
```
[ 🔨 Ish qo'shish ] [ 🧱 Material ]
[ 💵 To'lov      ] [ 📊 Hisobot  ]
[ ⚙️ Narxlar     ] [ ✅ Yopish   ]
```

### Ish qo'shish

FSM:
1. Loyihadagi `project_prices` dan `kind='work'` larni inline tugma qilib ko'rsat.
   Oxirida `[ ➕ Boshqa ish ]` tugmasi.
2. Tanlansa — miqdorni so'ra ("Necha m²?"). Vergul ham nuqta ham qabul qilinsin.
3. Tasdiqlash ekrani: `Shpatlyovka — 11 m² × 25 000 = 275 000 so'm`
   `[ ✅ Saqlash ] [ ❌ Bekor ]`
4. Saqlangach obyekt kartasiga qaytadi.

`[ ➕ Boshqa ish ]` tanlansa: nom → birlik (inline tanlov) → narx → miqdor →
`ProjectPrice` yaratiladi va `Entry` yoziladi.

Material ham xuddi shunday, faqat qo'shimcha qadam: **kim to'ladi?**
`[ Men to'ladim ] [ Mijoz to'ladi ]` → `paid_by`.

### To'lov

FSM: summa → usul (`[Naqd] [Karta] [O'tkazma]`) → saqlash.

### Hisobot

`summary` xizmatini chaqiradi va matn ko'rinishida yuboradi:
umumiy raqamlar + oxirgi 10 ta yozuv sanasi bilan.

### Narxlarim

Ustaning katalogi (`price_items`). Ko'rish, qo'shish, o'chirish (`is_active=false`).
Yangi obyekt ochilganda katalogdan nusxalash taklif qilinsin.

## Muhim tafsilotlar

**Summa formatlash.** `2080000` → `2 080 000 so'm`. Ajratuvchi — oddiy bo'shliq.
`utils.py` da bitta `fmt_money()` funksiyasi bo'lsin, hamma joyda shu ishlatilsin.

**Miqdor kiritish.** Usta `11,5` ham `11.5` ham yozishi mumkin. Ikkalasi qabul
qilinsin. Raqam bo'lmasa — "Faqat raqam kiriting, masalan: 11.5" deb qayta so'ra.

**Bekor qilish.** Har bir FSM oqimida `/bekor` komandasi va tugma ishlasin,
holat tozalanib asosiy menyuga qaytsin.

**Xatolar.** Kutilmagan xato bo'lsa foydalanuvchiga "Xatolik yuz berdi, qaytadan
urinib ko'ring" deb yozsin, log'ga to'liq traceback chiqsin. Stack trace hech
qachon foydalanuvchiga ko'rinmasin.

**Uzun ro'yxatlar.** Obyekt yoki narx 10 tadan oshsa, sahifalash qo'sh
(`[◀️] 1/3 [▶️]`).

## Konventsiyalar

- Aiogram 3 router'lari, `Dispatcher` ga `include_router` bilan ulanadi.
- FSM uchun `MemoryStorage` (MVP uchun yetadi; qayta ishga tushganda holat yo'qoladi — bu maqbul).
- Barcha matnlar o'zbek tilida, `utils.py` yoki alohida `texts.py` da to'plangan bo'lsin.
- `deleted_at IS NULL` filtri hamma o'qishda.
- Emoji faqat tugmalarda va sarlavhalarda, matn ichida ko'p ishlatma.
- Ruff toza o'tsin.

## Qabul mezonlari

```bash
docker compose up -d
docker compose logs -f bot     # "Start polling" ko'rinsin, xatosiz
docker compose exec api ruff check app scripts
```

Keyin Telegramda botni ochib qo'lda sinaladi:
1. `/start` → menyu chiqadi
2. Yangi obyekt yaratiladi
3. Narx qo'shiladi, ish yoziladi
4. To'lov qayd qilinadi
5. Hisobotdagi qarz qo'lda hisoblangan bilan mos keladi

## Nima QILMA

- Mini App / React yozma.
- Webhook'ni yoqma (kodini tayyorla, lekin lokalda polling ishlasin).
- OCR, ovoz, Excel yozma.
- Modellarni o'zgartirma. Yangi ustun kerak bo'lsa — avval mendan so'ra.
- Mavjud API endpointlarni buzma.
