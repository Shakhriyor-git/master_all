# Vazifa 12 — Navbar, hisobot tugmasi va musiqa

---

## 1. Navbar sakrashi — asl sabab

Oldingi tuzatish yordam bermadi, chunki muammo panelda emas, **sahifa
tuzilishida**.

### Hozir nima bo'lyapti

Sahifaning o'zi scroll qilinadi (`body` scroll), navbar esa `fixed` yoki
oqim oxirida turadi. Telegram Mini App'da viewport balandligi doimiy emas:

- Ilova ochilganda Telegram sarlavhasi yig'iladi/yoyiladi
- `100vh` mobil brauzerda haqiqiy ko'rinadigan balandlikdan katta
- Tab almashganda scroll 0 ga qaytadi, viewport qayta hisoblanadi

Natijada navbar bir zumga siljiydi — "sakrash" shundan.

### Yechim — app shell tuzilishi

**Sahifa umuman scroll qilinmasin.** Faqat ichki konteyner scroll bo'lsin.

```
index.css:
html, body, #root {
  height: 100%;
  overflow: hidden;
  overscroll-behavior: none;
}
```

`AppLayout` shunday bo'lsin:

```
<div className="flex flex-col" style={{ height: 'var(--tg-vh)' }}>
  <main className="flex-1 overflow-y-auto overscroll-contain">
    {children}
  </main>
  <BottomNav />   {/* flex-none, h-[62px] */}
</div>
```

- `main` — yagona scroll qiluvchi element
- `BottomNav` — `position: fixed` **emas**, oddiy flex qo'shni. Fixed
  bo'lmagani uchun viewport o'zgarsa ham siljimaydi
- `WebApp.expand()` ochilganda chaqirilsin

### `--tg-vh` o'zgaruvchisi

`lib/telegram.ts` da:

```
function syncViewport() {
  const h = WebApp.viewportStableHeight || window.innerHeight;
  document.documentElement.style.setProperty('--tg-vh', h + 'px');
}
syncViewport();
WebApp.onEvent('viewportChanged', syncViewport);
window.addEventListener('resize', syncViewport);
```

`viewportStableHeight` ishlatilsin, `viewportHeight` emas — birinchisi
klaviatura ochilganda o'zgarmaydi.

Telegram tashqarisida (`initData` bo'sh) `window.innerHeight` ga tushadi.

### Scroll pozitsiyasi

Tab almashganda `main` ning `scrollTop` 0 ga qaytsin, lekin **animatsiyasiz**
(`behavior: 'auto'`). Silliq scroll sakrash effektini kuchaytiradi.

### Tekshiruv

Telefonda tabni 10 marta almashtiring — navbar bir piksel ham qimirlamasin.
Uzun ro'yxatdan qisqa ekranga o'tganda ham.

---

## 2. Hisobot tugmasi joyi

Hozir eng pastda, ro'yxatdan keyin — usta uni topmaydi.

**Gradient kartadan darhol keyin**, tez amallar qatoridan **oldin** joylashsin.

Ko'rinishi hozirgidek qoladi (oq karta, `📄 Hisobot (PDF)`), faqat joyi
o'zgaradi.

---

## 3. Musiqa pleyeri

Bildirishnoma qo'ng'irog'i o'rniga musiqa tugmasi. Usta ish paytida
o'zining musiqasini qo'yadi.

### 3.1. Backend

**`users` jadvaliga:**

| Ustun | Tur |
|---|---|
| music_enabled | BOOLEAN, NOT NULL, default false |

**Yangi jadval `user_tracks`:**

| Ustun | Tur |
|---|---|
| id | BIGSERIAL PK |
| user_id | BIGINT FK → users.id, CASCADE, NOT NULL |
| filename | VARCHAR(200), NOT NULL — diskdagi nom |
| original_name | VARCHAR(200), NOT NULL — foydalanuvchi ko'radigan nom |
| size_bytes | INTEGER, NOT NULL |
| sort_order | INTEGER, default 0 |
| created_at | TIMESTAMPTZ |

Index `(user_id, sort_order)`.

**Endpointlar:**

```
GET    /api/me/tracks              ro'yxat + jami hajm + qolgan joy
POST   /api/me/tracks              multipart, bitta fayl
DELETE /api/me/tracks/{id}
```

**Cheklovlar:**
- Format: `audio/mpeg` (mp3), `audio/mp4` (m4a), `audio/ogg`
- **Foydalanuvchiga jami 15 MB** — necha ta fayl bo'lishi muhim emas
- Limitdan oshsa `400` va tushunarli xabar:
  `Joy yetarli emas. Bo'sh: 3.2 MB, fayl: 5.1 MB`
- Bitta fayl maksimum 15 MB

**Saqlash:** `/data/music/{user_id}/` — avatarlar kabi named volume.
`docker-compose.prod.yml` ga `music:/data/music` qo'shilsin.
`/media/music/` orqali statik beriladi.

Fayl nomi tasodifiy yasalsin (`secrets.token_hex(8) + kengaytma`) —
foydalanuvchi nomini yo'lga qo'yish xavfli.

**`GET /api/me` javobiga** `music_enabled` qo'shilsin.

### 3.2. Sozlamalar ekrani

Yangi bo'lim — `Mavzu` va `Til` orasiga:

```
Musiqa

  [ Ko'rsatilsin ]  ◯━━●        (toggle → music_enabled)

  Yuklangan: 8.4 MB / 15 MB
  ▓▓▓▓▓▓▓▓▓░░░░░░

  ♪  Yalla — Ozod qush          3.1 MB   🗑
  ♪  Sherali Jorayev            2.8 MB   🗑
  ♪  Bolalik                    2.5 MB   🗑

  [ + Musiqa yuklash ]
```

- Toggle o'chirilgan bo'lsa ro'yxat ko'rinadi, lekin Asosiy ekranda tugma yo'q
- Yuklash tugmasi `<input type="file" accept="audio/*">`
- Yuklanayotganda progress ko'rsatilsin
- O'chirishda `WebApp.showConfirm`
- Joy tugagan bo'lsa yuklash tugmasi o'chirilgan holatda va sabab yozilgan

### 3.3. Asosiy ekrandagi tugma

`music_enabled = true` va kamida bitta trek bo'lsa — qo'ng'iroq o'rnida
musiqa tugmasi (30px doira, `--primary-soft` fon):

| Holat | Ikonka |
|---|---|
| To'xtagan | `ti-player-play-filled` |
| Chalinayotgan | `ti-player-pause-filled` |

Chalinayotganda ikonka atrofida yumshoq pulsatsiya (2s davriy, `opacity`
0.6→1). Bu yagona takrorlanuvchi animatsiya bo'ladi.

**Xatti-harakat:**
- **Bir marta bosish** — chalinadi. Chalinayotgan bo'lsa to'xtaydi (pauza)
- **Ikki marta tez bosish** (300ms ichida) — joriy trek boshidan qayta chalinadi
- Trek tugasa — ro'yxatdagi keyingisi. Oxirgisidan keyin birinchisiga qaytadi
- **Uzoq bosish** — trek tanlash varag'i ochiladi

`music_enabled = false` yoki trek yo'q bo'lsa tugma umuman ko'rsatilmasin.

### 3.4. Texnik tafsilotlar

- Bitta `<audio>` element, `AudioContext` ilova darajasida (`MusicProvider`)
- Ekran almashganda musiqa **to'xtamasin** — provider `AppLayout` da bo'lsin
- `audio.preload = "none"` — trafik tejash uchun, faqat bosilganda yuklansin
- Yuklanayotganda tugmada spinner
- Xato bo'lsa (fayl topilmadi, format qo'llab-quvvatlanmaydi) — tugma
  jimgina to'xtasin, xato xabari chiqmasin
- Telegram audio chalayotgan bo'lsa u to'xtaydi — bu normal, brauzer o'zi hal qiladi

---

## Qabul mezoni

```bash
cd frontend && npm run build && npm run lint
docker compose exec api alembic upgrade head
docker compose exec api ruff check app scripts
```

Qo'lda:

1. **Tab 10 marta almashtirilsa navbar qimirlamaydi** — bu asosiysi
2. Hisobot tugmasi gradient kartadan keyin turadi
3. Sozlamalarda musiqa yuklanadi, 15 MB limiti ishlaydi
4. Asosiy ekranda tugma bosilganda chalinadi, yana bosilganda to'xtaydi
5. Ikki marta bosilganda boshidan chalinadi
6. Ekran almashganda musiqa uzilmaydi
7. Toggle o'chirilsa tugma yo'qoladi

## Nima QILMA

- Musiqani botga qo'shma
- Playlist, shuffle, tovush balandligi boshqaruvi — hozircha kerak emas
- Modellarga boshqa o'zgarish kiritma
