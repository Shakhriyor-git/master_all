# Vazifa 02 — Telegram autentifikatsiya va API

## Shart

01-vazifa tugagan bo'lishi kerak: modellar, Alembic, seed ishlaydi.

## Nima qilish kerak

1. Telegram `initData` tekshiruvi (HMAC-SHA256)
2. Pydantic sxemalar
3. CRUD endpointlar: loyihalar, narxlar, yozuvlar, to'lovlar
4. Balans endpointi

## 1. Autentifikatsiya — eng muhim qism

Telegram Mini App frontenddan `initData` degan qatorni yuboradi. Uning ichida
foydalanuvchi ma'lumotlari va bot tokeni bilan imzolangan `hash` bo'ladi.

**Qoida:** frontenddan kelgan `user_id` ga HECH QACHON ishonilmaydi. Faqat
`initData` imzosi tekshirilgandan keyin, uning ichidan chiqqan `user.id` ishlatiladi.
Bu buzilsa, istalgan odam boshqa ustaning butun moliyaviy ma'lumotini ko'radi.

`app/core/security.py`:

```python
def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict
```

Algoritm:
1. `init_data` ni `urllib.parse.parse_qsl(init_data, strict_parsing=True)` bilan ajrat
2. `hash` ni ajratib ol, qolganini alifbo tartibida `key=value` qilib `\n` bilan birlashtir
3. `secret_key = hmac_sha256(key=b"WebAppData", msg=bot_token)`
4. `computed = hmac_sha256(key=secret_key, msg=data_check_string).hexdigest()`
5. `hmac.compare_digest(computed, received_hash)` — oddiy `==` ishlatma
6. `auth_date` ni tekshir: hozirgi vaqtdan `max_age_seconds` dan eski bo'lsa rad et
7. `user` maydonini JSON sifatida parse qilib qaytar

Xato bo'lsa `InvalidInitDataError` ko'tar (o'z exception klassing).

`app/api/deps.py`:

```python
async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User
```

- `Authorization: tma <init_data>` formatini kutadi
- Imzoni tekshiradi, `telegram_id` bo'yicha `User` topadi
- Topilmasa yangi yaratadi (birinchi kirishda avtomatik ro'yxatdan o'tish)
- Yaroqsiz bo'lsa `401`

Qo'shimcha dependency: `get_owned_project(project_id, user)` — loyiha shu
foydalanuvchiniki ekanini tekshiradi, aks holda `404` (`403` emas — begona odamga
loyiha borligini ham bildirmaymiz).

## 2. Sxemalar (`app/schemas/`)

Har bir model uchun: `XxxCreate`, `XxxUpdate` (hamma maydon optional), `XxxRead`.
`model_config = ConfigDict(from_attributes=True)`.
Pul maydonlari `Decimal`, `float` emas.
`quantity > 0`, `amount > 0` uchun `Field(gt=0)`.

## 3. Endpointlar

Barchasi `/api` prefiksi bilan, `get_current_user` talab qiladi.

### Loyihalar — `app/api/routes/projects.py`
```
GET    /api/projects                 ro'yxat (status bo'yicha filtr, deleted_at IS NULL)
POST   /api/projects                 yaratish
GET    /api/projects/{id}            bitta
PATCH  /api/projects/{id}            tahrirlash
DELETE /api/projects/{id}            soft delete
GET    /api/projects/{id}/summary    balans (pastda)
```

### Narxlar — `app/api/routes/prices.py`
```
GET    /api/price-items                          ustaning katalogi
POST   /api/price-items
PATCH  /api/price-items/{id}
DELETE /api/price-items/{id}                     is_active=false

GET    /api/projects/{id}/prices                 loyihadagi narxlar
POST   /api/projects/{id}/prices                 qo'shish (price_item_id yoki qo'lda)
POST   /api/projects/{id}/prices/import          katalogdan ommaviy nusxalash
PATCH  /api/projects/{id}/prices/{price_id}      narxni o'zgartirish
```

`import` endpointi: `{"price_item_ids": [1,2,3]}` qabul qiladi, har biri uchun
`ProjectPrice` yaratadi va `default_price` ni `price` ga nusxalaydi. Allaqachon
mavjud bo'lganlarni o'tkazib yuboradi (dublikat yaratmaydi).

### Yozuvlar — `app/api/routes/entries.py`
```
GET    /api/projects/{id}/entries    filtr: kind, date_from, date_to
POST   /api/projects/{id}/entries
PATCH  /api/entries/{id}
DELETE /api/entries/{id}             soft delete
```

`POST` da: `project_price_id` berilsa, `name` / `unit` / `unit_price` shundan
nusxalanadi (frontend yuborgan narxga ishonilmaydi). Berilmasa — qo'lda kiritilgan
bir martalik yozuv, `name` / `unit` / `unit_price` majburiy.

`project_price_id` boshqa loyihaga tegishli bo'lsa — `400`.

### To'lovlar — `app/api/routes/payments.py`
```
GET    /api/projects/{id}/payments
POST   /api/projects/{id}/payments
PATCH  /api/payments/{id}
DELETE /api/payments/{id}            soft delete
```

## 4. Balans — `app/services/summary.py`

`GET /api/projects/{id}/summary` quyidagini qaytarsin:

```json
{
  "works_total": "3400000.00",
  "materials_by_master": "850000.00",
  "materials_by_client": "200000.00",
  "paid_total": "2000000.00",
  "client_owes": "2250000.00",
  "entries_count": 24,
  "last_entry_date": "2026-08-28"
}
```

Formula:
```
client_owes = works_total + materials_by_master - paid_total
```

`materials_by_client` balansga kirmaydi — mijoz o'zi to'lagan, faqat ma'lumot uchun.

Bitta SQL agregat so'rovda hisoblansin, Python'da tsikl bilan emas.
`deleted_at IS NOT NULL` yozuvlar hisobga kirmasin.

## Konventsiyalar

- Barcha DB so'rovlari `select()` bilan, async.
- Xatolar `HTTPException` orqali, xabar o'zbek tilida.
- Router'lar `main.py` ga `app.include_router(...)` bilan ulansin.
- `deleted_at IS NULL` filtri hamma o'qish so'rovlarida bo'lsin.
- Ruff toza o'tsin.

## Qabul mezonlari

```bash
docker compose exec api ruff check app
```

Swagger'da (http://localhost:8000/docs) hamma endpoint ko'rinsin.

Va qo'lda test: `scripts/test_auth.py` yozilsin — soxta `initData` yasaydi
(bot tokeni bilan to'g'ri imzolangan), uni `/api/projects` ga yuboradi va
`200` olishini tekshiradi. Imzoni buzib, `401` kelishini ham tekshiradi.

## Nima QILMA

- Frontend yozma.
- Bot handler yozma.
- Excel hisobot yozma.
- OCR / voice yozma.
- Modellarni o'zgartirma (agar jiddiy sabab bo'lsa — avval mendan so'ra).
