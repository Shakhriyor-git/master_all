# Vazifa 09 — Katalogni tozalash va PDF hisobot

Ikki qism. Ikkinchisi asosiy.

---

# 1-QISM — Standart katalogdan voz kechish

## Sabab

Tayyor katalog amalda chalkashlik keltirdi: 45 ta narxsiz pozitsiya, ustaning
o'z nomlari bilan mos kelmaydi, ro'yxatni tozalash qo'shishdan uzoqroq.

Usta o'zi kiritsin. Kelajakda AI yordamida to'ldirish qo'shiladi.

## 1.1. Seed'ni qisqartirish

`app/services/catalog_seed.py`:

- **Birliklar qoladi** — 13 ta standart birlik (`is_system=true`) seed qilinaveradi.
  Ular umumiy va chalkashlik bermaydi.
- **Kategoriyalar va pozitsiyalar seed qilinmaydi** — butunlay olib tashlansin.

Yangi foydalanuvchi bo'sh katalog bilan boshlaydi.

## 1.2. Mavjud ma'lumotni tozalash

Hozirgi bazada seed qilingan katalog turibdi. Uni o'chirish uchun:

```
DELETE /api/price-items/seeded     — hech qachon ishlatilmagan seed pozitsiyalar
DELETE /api/categories/seeded      — bo'sh qolgan seed kategoriyalar
```

Faqat `entries` yoki `project_prices` da ishlatilmagan pozitsiyalarni o'chirsin —
ishlatilganini tegmasin, aks holda tarix buziladi.

Frontend: `Xizmatlarim` ekranida yuqorida bir martalik banner:

```
Tayyor katalog endi ishlatilmaydi.
Ishlatilmagan 45 ta pozitsiyani o'chirasizmi?   [O'chirish] [Qoldirish]
```

Bosilgach banner boshqa ko'rinmasin (`localStorage` emas — foydalanuvchining
katalogi bo'sh yoki seed pozitsiya qolmagan bo'lsa ko'rsatilmasin).

## 1.3. Bo'sh holat

Katalog bo'sh bo'lsa `Xizmatlarim` da:

```
Katalogingiz bo'sh

Avval kategoriya yarating (masalan: Shift, Elektrika),
keyin ichiga xizmatlaringizni qo'shing.

[ + Yangi kategoriya ]
```

Ish qo'shishda katalog bo'sh bo'lsa — to'g'ridan-to'g'ri "Yangi qo'shish"
formasi ochilsin, bo'sh ro'yxat ko'rsatilmasin.

## 1.4. Ikkita atama xatosi

- Materiallar tabida `N xizmat` deb yozilyapti. `N pozitsiya` bo'lsin.
  Ishlar tabida `N xizmat` qoladi.
- `Yangi xizmat` varaqasi material qo'shishda `Yangi material` deb ochilsin.

## 1.5. Xato: kategoriyalar aralashyapti

Skrinshotda `Materiallar` tabida `Umumiy` (ish kategoriyasi) ko'rinyapti.
`GET /api/categories?kind=` filtri frontendda uzatilmayapti yoki backendda
qo'llanilmayapti — topib tuzat.

---

# 2-QISM — PDF hisobot

## Maqsad

Usta telefonini mijozga uzatib "mana, hammasi shu yerda" deydi. Yoki faylni
yuboradi. Hujjat ishonch uyg'otishi kerak.

**Muhim:** PDF to'g'ridan-to'g'ri bazadan quriladi. LLM ishlatilmasin —
moliyaviy hujjatda bitta xato raqam butun tizimga ishonchni yo'qotadi.

## 2.1. Kutubxona

`reportlab==4.2.5` — sof Python, tizim kutubxonalari kerak emas, 1 GB RAM'da
muammosiz ishlaydi.

`backend/Dockerfile` ga shrift qo'sh (o' va g' harflari to'g'ri chiqishi uchun):

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
```

Shrift yo'li: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` va
`DejaVuSans-Bold.ttf`. `pdfmetrics.registerFont` bilan ro'yxatdan o'tkaz.

## 2.2. Endpoint

```
GET /api/projects/{id}/report.pdf?date_from=&date_to=
```

`Content-Type: application/pdf`,
`Content-Disposition: attachment; filename="Tarovat-145-uy_2026-08-30.pdf"`

Fayl nomida obyekt nomi transliteratsiya qilinsin (bo'shliq → `-`, maxsus
belgilar olib tashlansin).

Sana filtri berilmasa — butun davr.

## 2.3. Hujjat tuzilishi

Kod: `app/services/report_pdf.py`. A4, chetlari 18 mm.

### Sarlavha

```
HISOB-KITOB

Obyekt:   Tarovat 145-uy
Mijoz:    Jasur
Usta:     Shahriyor · +998916600106
Davr:     01.08.2026 — 30.08.2026
Sana:     30.08.2026
```

Ostida ingichka chiziq.

### Bo'lim 1 — Bajarilgan ishlar

| Sana | Ish nomi | Miqdor | Birlik narxi | Summa |
|---|---|---|---|---|

Kategoriya bo'yicha guruhlangan, har guruh ostida oraliq jami.
Brak yozuvlari alohida, kulrang rangda, `(brak — hisobga kirmadi)` izohi bilan
va umumiy summaga qo'shilmasin.

Bo'lim oxirida: **Ishlar jami: 2 400 000 so'm**

### Bo'lim 2 — Materiallar

Ikki kichik jadval, alohida:

**2.1. Usta hisobidan** — mijozga hisoblanadi
**2.2. Mijoz hisobidan** — mijoz budjetidan chiqdi

Ustunlar: sana, nomi, miqdor, birlik narxi, summa, to'lov usuli.

Har birining ostida oraliq jami.

### Bo'lim 3 — Xarajatlar

Faqat `paid_by = client` bo'lganlar chiqsin (ovqat, transport va h.k.).
Ustaning shaxsiy xarajatlari mijozga aloqasi yo'q, hujjatga kirmasin.

Ustunlar: sana, nomi, summa, to'lov usuli.

### Bo'lim 4 — Mijoz to'lovlari

| Sana | Maqsad | Usul | Summa |
|---|---|---|---|

`Maqsad`: `Ish haqi uchun` yoki `Xarajat uchun`.

### Bo'lim 5 — Yakuniy hisob

Ikki blok, yonma-yon yoki ketma-ket, aniq ajratilgan:

```
1. ISH HAQI HISOBI
   Bajarilgan ishlar              2 400 000
   Usta to'lagan material          + 350 000
   Mijoz to'lagan ish haqi       − 2 000 000
   ─────────────────────────────────────────
   MIJOZ QARZI                      750 000 so'm

2. MIJOZ BUDJETI
   Mijoz bergan                   1 000 000
   Material (mijoz hisobidan)     − 520 000
   Xarajatlar                     − 120 000
   ─────────────────────────────────────────
   BUDJET QOLDIG'I                  360 000 so'm
```

Ikki blok **hech qachon qo'shilmasin** — bu tizimning asosiy qoidasi.

Qarz manfiy bo'lsa: `MIJOZ AVANSI` deb yozilsin, minussiz.
Budjet qoldig'i manfiy bo'lsa: `BUDJETDAN OSHDI` deb, qizil rangda.

### Kolontitul

Har sahifa pastida: `Masters Pro · sahifa N / M`

## 2.4. Formatlash qoidalari

- Summalar: `2 400 000` — har uch xonaga bo'shliq, `so'm` faqat jami qatorlarda
- Sanalar: `30.08.2026`
- Miqdor: kasr bo'lsa vergul bilan — `11,5 m²`
- Bo'sh bo'lim **umuman chiqmasin** — sarlavhasi ham
- Jadval satrlari navbatma-navbat och fon bilan (o'qishni osonlashtiradi)
- Faqat qora, kulrang va bitta urg'u rangi. Rangli PDF bosmada yomon chiqadi.

## 2.5. Yuborish

**Mini App:** Hisobot ekranida `📄 PDF yuklab olish` tugmasi. Sana oralig'i
tanlangan bo'lsa u ham uzatiladi. Yuklash `Telegram.WebApp.openLink` orqali.

**Bot:** obyekt kartasiga tugma qo'shilsin — `📄 Hisobot (PDF)`.
Bosilganda PDF yasab, fayl sifatida yuboradi:

```
Tarovat 145-uy — hisob-kitob
30.08.2026 holatiga
```

Bu 08-vazifada botni soddalashtirish qoidasidan istisno — hisobotni
Telegram orqali darhol mijozga yuborish juda qulay.

## 2.6. Ishlash

1 GB RAM'da PDF yasash bloklovchi amal. `run_in_threadpool` da bajarilsin,
aks holda boshqa so'rovlar kutib qoladi.

500 yozuvli hisobot 3 soniyadan tez tayyor bo'lsin.

## Qabul mezoni

```bash
docker compose exec api ruff check app scripts
cd frontend && npm run build && npm run lint
```

`scripts/test_report.py` yozilsin: seed ma'lumot bilan PDF yasab,
`/tmp/report_test.pdf` ga saqlasin va sahifa sonini chiqarsin.
Men uni ko'chirib ko'zdan kechiraman.

Qo'lda tekshiriladi:
1. Botdan PDF kelsin, ochilsin, o'zbekcha harflar to'g'ri chiqsin
2. Yakuniy hisobdagi raqamlar Mini App'dagi bilan bir xil bo'lsin
3. Bo'sh obyekt uchun PDF yasalsa — yiqilmasin, "yozuv yo'q" deb chiqsin

## Nima QILMA

- LLM / Gemini ishlatma — raqamlar bazadan
- Excel qilma, hozircha faqat PDF
- Modellarga tegma, yangi migratsiya kerak emas
- Brigada / rollar qo'shma
