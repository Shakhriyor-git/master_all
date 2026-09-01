# Vazifa 11 — Dizaynni ilovaga ko'chirish

## Manba

`docs/design/masters-pro-dizayn.html` — barcha ekranlarning tayyor maketi,
kunduzgi va tungi mavzuda. **Aniq qiymatlar (rang, o'lcham, bo'shliq) o'sha
fayldan olinsin**, bu yerda faqat mantiq tushuntiriladi.

Faylni `docs/design/` ga qo'yaman. Boshlashdan oldin uni o'qib chiq.

Tartib: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Har biri mustaqil, ketma-ket qil.

---

## 1. Navigatsiya sakrashi (xato)

**Muammo:** tab almashganda panel tepaga-pastga sakraydi. Telefonda sezilarli,
keng ekranda yo'q.

**Sabab:** faol tabda ikonka o'lchami yoki og'irligi o'zgaradi, panel balandligi
qayta hisoblanadi.

**Yechim:**

- Panel balandligi **62px qat'iy** (`h-[62px]`), hech qanday holatda o'zgarmaydi
- Ikonka o'lchami **23px doim**, `size` prop o'zgarmasin
- Faqat rang o'zgaradi: `--text-faint` → `--primary`, `transition-colors 150ms`
- Faol tabda `filled` variant, nofaolda `outline` — **ikkalasining o'lchami bir xil**
- Yorliq shrifti 10px, og'irligi o'zgarmaydi
- Ikonkaga hech qanday `scale`, `translate`, `spring` animatsiya qo'llanmasin
- Oldingi vazifadagi `layoutId="nav-indicator"` sirg'aluvchi chiziq **olib tashlansin**

**`+` tugmasi:**
- 52px doira, `--primary` fon
- `translateY(-14px)` — paneldan tepaga chiqadi
- Soya: `0 4px 14px` primary rangning 35% shaffofligi bilan
- Bosilganda faqat `scale(0.94)`, 100ms

`safe-area-inset-bottom` panel ostiga `padding` sifatida qo'shilsin, balandlikka emas.

---

## 2. Rang tokenlari — yozuv chegaralari

`theme.css` ga sakkizta yangi o'zgaruvchi qo'shilsin (aniq qiymatlar maketda,
8-bo'lim "Rang xaritasi"):

```
--border-work, --border-material, --border-expense,
--border-payment, --bg-payment
```

Yozuv kartasi (`EntryCard`, `TimelineEntryCard`) chegarasi turiga qarab:

| Tur | Chegara | Fon |
|---|---|---|
| Ish | `--border-work` | `--surface` |
| Material | `--border-material` | `--surface` |
| Xarajat | `--border-expense` | `--surface` |
| Mijoz to'lovi | `--border-payment` | `--bg-payment` |

Chegara **1px**, radius 13px. Kartalar orasida 8px bo'shliq.

`lib/entryVisual.ts` da bu xaritalash markazlashtirilsin — har komponentda
takrorlanmasin.

---

## 3. Asosiy ekran

Maketning 2-bo'limi.

**Yuqorida:** obyekt tanlagich (kichik "Obyekt" yorlig'i + nom + `▾`),
o'ngda bildirishnoma ikonkasi (hozircha bosilmaydi yoki olib tashlansin).

**Gradient karta — bitta katta raqam:**
- Yorliq: `Mijoz qarzi` (manfiy bo'lsa `Mijoz avansi`, minussiz)
- Raqam 34px, 600, `tabular-nums`, `letter-spacing: -0.02em`
- Ostida `so'm` 12px
- Ajratuvchi chiziq, keyin ikkita kichik raqam: `Ishlar` va `To'langan`
- O'ng yuqorida shaffof doira (blob), `overflow: hidden`
- **Naqsh yo'q** — u faqat Profilda

**Tez amallar qatori:** to'rtta tugma — Ish, Material, Xarajat, To'lov.
Har biri to'g'ridan-to'g'ri tegishli oqimni ochadi (`/add?type=work` va h.k.),
tur tanlash ekrani orqali emas.

**So'nggi yozuvlar:** uchta bo'lim (ishlar/materiallar/xarajatlar) o'rniga
**bitta ro'yxat**, aralash, sanaga qarab. 5 tagacha. Ikonka rangi turini aytadi.
O'ngda `Barchasi` → `/history`.

Eski `Bajarilgan ishlar` / `Materiallar` / `Xarajatlar` / `Mijoz to'lovlari`
bo'limlari va ularning `+ qo'shish` tugmalari olib tashlansin —
tez amallar qatori ularni almashtiradi.

`Hisobot (PDF)` tugmasi qoladi, so'nggi yozuvlar ostiga tushsin.

---

## 4. Tarix

Maketning 3-bo'limi.

- Segment filtr: `Barchasi · Ishlar · Material · Xarajat · To'lovlar`
- Kun sarlavhasi: `BUGUN · 1 SENTABR` — 11px, `--text-faint`, harflar orasi 0.04em
- Kartalar 2-bo'limdagi rang xaritasi bo'yicha
- To'lov kartasida ikkita chip: maqsad va usul
- Material/xarajatda usul chipi
- Brak yozuvida `⚠️ Brak` chipi, summa ustidan chizilgan
- Vaqt o'ng pastda, 10px

Kun sarlavhasi scroll paytida yopishib tursin (`position: sticky`).

---

## 5. Qo'shish ekranlari — birlashtirish

Maketning 4-bo'limi. **Ish, material va xarajat uchun bitta komponent.**
Hozir ular turlicha ko'rinadi — bu tuzatiladi.

**Tanlash bosqichi:**
1. Sarlavha: `Ish qo'shish` / `Material qo'shish` / `Xarajat qo'shish`
2. AI matn maydoni — chegara `--primary`, chapda `sparkles`, o'ngda kamera
   (material) yoki mikrofon o'rniga hozircha kamera (ish uchun ham chek bo'lishi mumkin)
3. Ostida izoh: `Yozing yoki chekni suratga oling`
4. Ajratuvchi: `— yoki tanlang —`
5. Kategoriya chiplari, gorizontal scroll, faol chip `--primary`
6. Qidiruv maydoni
7. Ro'yxat kartasi:
   - Birinchi qator: `✏️ Qo'lda kiritish`, fon `--primary-soft`, matn `--primary`
   - Keyin pozitsiyalar: nom chapda, `narx · birlik` o'ngda
   - Narxsiz bo'lsa `narxsiz · birlik`, `--danger` rangda
   - Oxirgi qator: `+ Yangi xizmat` / `+ Yangi material`

**To'ldirish bosqichi:**
1. Tepada tanlangan pozitsiya: ikonka + nom + `kategoriya · birlik`
2. `Miqdor` — katta maydon (22px), ostida tez tugmalar `1 5 10 +1 −1`
3. `Bir <birlik> narxi` — 18px maydon
4. `Qanday to'landi` — segment: Naqd / Karta / O'tkazma
5. **Natija bloki** — `--primary-soft` fonda, ustida `5 qop × 130 000 so'm`,
   ostida `650 000 so'm` 24px 600
6. Telegram MainButton: `Saqlash`

Xarajat oqimida `Miqdor` va `Bir birlik narxi` o'rniga bitta `Summa` maydoni.

---

## 6. Xizmatlarim — katalog

Maketning 5-bo'limi.

**Kategoriya kartalari:**
- Ikonka 38px, 11px radius, kategoriya rangida tinted fon
- Nom 14px/500, ostida `N xizmat` yoki `N pozitsiya`
- **Progress chizig'i** 3px: narxlangan / jami nisbati
  - 100% → `--success`
  - 1-99% → `--success` (agar >50%) yoki `--danger`
  - 0% → `--danger`
- Ostida matn: `3 / 5 narxlangan` yoki `Narx to'liq`
- Qizil `N narxsiz` yozuvi olib tashlansin

**`+ Yangi kategoriya`** — punktir ramka, butun kenglikda, `--primary` rangda.

**Kategoriya ichi:**
- Tepada ikonka + nom + `6 xizmat · 5 narxsiz`
- `✨ Barcha narxlarni to'ldirish` tugmasi — chegara `--primary`
- Ro'yxat: nom + birlik chapda, narx o'ngda
- Narx bosilganda **o'sha joyda tahrirlanadi** — qator foni `--primary-soft`
  bo'ladi, raqam ostida chiziq paydo bo'ladi, klaviatura ochiladi
- Enter → keyingi narxsiz qatorga o'tadi
- Narxi yo'q bo'lsa `narx yo'q` `--danger` rangda

### 6.1. Ikonka tizimi — emoji o'rniga

Maketning 7-bo'limi: 16 ta ikonka, har biri o'z rangi bilan.

`categories.icon` ustuni endi ikonka nomini saqlaydi (`stack-2`, `bolt`, ...).
Ustun turi o'zgarmaydi (`VARCHAR`), lekin mavjud emojilar ko'chirilishi kerak.

**Migratsiya — moslik jadvali:**

```
🏠 → stack-2      🧱 → wall         ⬜ → layout-grid   ◻️ → checkbox
⚡ → bolt         🚿 → droplet      🔨 → hammer        📋 → tool
🪣 → bucket       🎨 → brush        📦 → package
```

Ro'yxatda yo'q emoji → `tool` (standart).

`frontend/src/lib/categoryIcons.ts` — ikonka nomi → komponent va rang xaritasi.
Nomi topilmasa `tool` va kulrang ishlatilsin, yiqilmasin.

**Yangi kategoriya varaqasi:** ikonka to'ri (maketdagi 7-bo'lim ko'rinishida),
tepada qidiruv maydoni. Tanlangan ikonka `--primary` chegara bilan belgilanadi.

---

## 7. Profil

Maketning 6-bo'limi.

**Gradient sarlavha kafel naqshi bilan** — SVG `<pattern>`, 17×17 katak,
oq chiziq 20% shaffoflikda, 0.9px qalinlik.

Naqsh **faqat shu ekranda**. Asosiy ekrandagi gradient kartada naqsh yo'q.

- Avatar 84px, oq halqa ichida (3px `rgba(255,255,255,.3)`)
- Ism 20px/600, telefon 12px
- `✏️ Tahrirlash` — shaffof pill tugma
- **Statistika kartaning pastki qatoriga birikkan**: ikkita ustun,
  gradientning bir oz to'qroq tonida. Alohida oq kartalar olib tashlansin

**Mening sahifalarim:** havolalar yonma-yon, har biri kichik karta bo'lib.
Oxirida 46px kenglikdagi `+` tugmasi. Havola yo'q bo'lsa faqat `+` turadi.

**Ro'yxat:** Xizmatlarim / Qaydlarim / Brigada — har birida 34px tinted ikonka,
ostida izoh (`28 pozitsiya · 6 narxsiz`, `2 ta ro'yxat`).

`items_count` va narxsizlar soni `GET /api/price-items` dan hisoblansin yoki
`GET /api/me` javobiga qo'shilsin — qo'shimcha so'rov qilinmasin.

---

## 8. Qolgan tuzatishlar

**a) PDF da chek tarkibi ko'rinmayapti.** Material hisobotida har qatorning
ostida, `entries.note` bo'lsa — 7.5pt kulrang, chapdan 8mm surilgan,
sahifada to'g'ri bo'linadigan holda.

**b) Sozlamalardagi `Bildirishnomalar` toggle'i olib tashlansin** — u hech
narsa qilmaydi.

**c) `.env.prod.example`** ga qo'shilsin:
```
GEMINI_MODEL=gemini-3.5-flash-lite
```

**d) `backup.sh`** dagi hajm tekshiruvi bayt aniqligida bo'lsin
(`stat -c%s` yoki `find -size -1024c`), `-size -1k` emas — u bloklarda
o'lchaydi va 20 baytlik faylni o'tkazib yuboradi.

**e) AI chaqiruv vaqti logga yozilsin:**
```
AI parse: 1.8s | in=340 tok | out=95 tok | model=gemini-3.5-flash-lite
```
Sekinlashsa sababini bilish uchun.

---

## Qabul mezoni

```bash
cd frontend && npm run build && npm run lint
docker compose exec api alembic upgrade head
docker compose exec api ruff check app scripts
```

Qo'lda tekshiriladi:

1. Tab almashganda navigatsiya **sakramaydi**
2. Tarixda to'rt xil yozuv to'rt xil chegara rangida
3. Asosiy ekranda bitta katta raqam, to'rtta tez tugma ishlaydi
4. Ish va material qo'shish ekranlari **bir xil ko'rinadi**
5. Katalogda emoji o'rniga ikonka, progress chizig'i to'g'ri
6. Profilda kafel naqshi ko'rinadi, boshqa ekranlarda yo'q
7. Ikkala mavzuda ham hamma matn o'qiladi

## Nima QILMA

- Ovoz funksiyasi
- Brigada / rollar
- Yangi AI imkoniyatlari
- Botga tegma
- `summary` mantiqini o'zgartirma — faqat ko'rinish
