# Vazifa 01 — Ma'lumotlar bazasi qatlami

## Kontekst

Bu loyiha — qurilish brigadalari uchun ish va xarajat hisobi. Telegram bot + Mini App.
Repo skeleti allaqachon mavjud: FastAPI, async SQLAlchemy 2.0, PostgreSQL 16, Docker Compose.

Mavjud fayllar:
- `backend/app/core/config.py` — Pydantic Settings, `settings.database_url` tayyor
- `backend/app/core/db.py` — `engine`, `SessionLocal`, `Base`, `get_db` tayyor
- `backend/app/main.py` — FastAPI app, health router ulangan
- `backend/app/models/` — bo'sh, faqat `__init__.py`

**Muhim:** mavjud fayllarni qayta yozma. `db.py` dagi `Base` ni ishlat, yangi `Base` yaratma.

## Nima qilish kerak

1. SQLAlchemy modellarini yozish (quyidagi sxema bo'yicha)
2. Alembic'ni sozlash (async rejimda)
3. Birinchi migratsiyani generatsiya qilish va sinash
4. Test uchun kichik seed skripti

## Sxema

Barcha jadvallarda: `id BIGSERIAL PRIMARY KEY`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`.
Pul — `Numeric(14, 2)`. Hech qayerda `Float` ishlatilmasin.
Vaqt — har doim `TIMESTAMP WITH TIME ZONE`.

### users

| Ustun | Tur | Izoh |
|---|---|---|
| telegram_id | BIGINT, UNIQUE, NOT NULL | BIGINT majburiy, Telegram ID int32 dan oshadi |
| full_name | VARCHAR(200), NOT NULL | |
| username | VARCHAR(64), NULL | Telegram username, @ siz |
| phone | VARCHAR(32), NULL | |
| language | VARCHAR(8), NOT NULL, default 'uz' | |
| is_active | BOOLEAN, NOT NULL, default true | |
| updated_at | TIMESTAMPTZ, onupdate=now() | |

### projects — obyektlar

| Ustun | Tur | Izoh |
|---|---|---|
| user_id | BIGINT FK → users.id, ON DELETE CASCADE, NOT NULL | egasi (usta) |
| title | VARCHAR(200), NOT NULL | masalan "Chilonzor 12-uy, 45-xonadon" |
| address | VARCHAR(500), NULL | |
| client_name | VARCHAR(200), NULL | |
| client_phone | VARCHAR(32), NULL | |
| client_telegram_id | BIGINT, NULL | keyinchalik mijozga read-only ko'rinish uchun |
| status | VARCHAR(20), NOT NULL, default 'active' | active / paused / completed / archived |
| note | TEXT, NULL | |
| started_at | DATE, NULL | |
| closed_at | DATE, NULL | |
| updated_at | TIMESTAMPTZ, onupdate=now() | |
| deleted_at | TIMESTAMPTZ, NULL | soft delete |

Index: `(user_id, status)`.

### price_items — ustaning shaxsiy katalogi

| Ustun | Tur | Izoh |
|---|---|---|
| user_id | BIGINT FK → users.id, ON DELETE CASCADE, NOT NULL | |
| name | VARCHAR(200), NOT NULL | "Shpatlyovka" |
| kind | VARCHAR(20), NOT NULL | work / material |
| unit | VARCHAR(20), NOT NULL | m2, m3, dona, qop, metr, kg, soat, komplekt |
| default_price | NUMERIC(14,2), NOT NULL, default 0 | |
| is_active | BOOLEAN, NOT NULL, default true | |
| updated_at | TIMESTAMPTZ, onupdate=now() | |

Index: `(user_id, is_active)`.
Constraint: `UNIQUE (user_id, name, kind)`.

### project_prices — loyihaga kelishilgan narx (katalogdan NUSXA)

Bu jadval loyihaning eng muhim qismi. Yangi obyekt ochilganda kerakli pozitsiyalar
`price_items` dan shu yerga nusxalanadi. Keyin katalogda narx o'zgarsa ham,
eski loyiha hisoboti o'zgarmaydi.

| Ustun | Tur | Izoh |
|---|---|---|
| project_id | BIGINT FK → projects.id, ON DELETE CASCADE, NOT NULL | |
| price_item_id | BIGINT FK → price_items.id, ON DELETE SET NULL, NULL | manba; bir martalik pozitsiya uchun NULL |
| name | VARCHAR(200), NOT NULL | nusxa olingan nom |
| kind | VARCHAR(20), NOT NULL | work / material |
| unit | VARCHAR(20), NOT NULL | |
| price | NUMERIC(14,2), NOT NULL | shu loyihada kelishilgan narx |
| is_active | BOOLEAN, NOT NULL, default true | |
| updated_at | TIMESTAMPTZ, onupdate=now() | |

Index: `(project_id, kind)`.

### entries — ishlar va materiallar

| Ustun | Tur | Izoh |
|---|---|---|
| project_id | BIGINT FK → projects.id, ON DELETE CASCADE, NOT NULL | |
| project_price_id | BIGINT FK → project_prices.id, ON DELETE RESTRICT, NULL | |
| created_by_user_id | BIGINT FK → users.id, ON DELETE SET NULL, NULL | hozircha har doim usta |
| kind | VARCHAR(20), NOT NULL | work / material |
| name | VARCHAR(200), NOT NULL | yozuv paytidagi nom (snapshot) |
| unit | VARCHAR(20), NOT NULL | |
| quantity | NUMERIC(12,3), NOT NULL | |
| unit_price | NUMERIC(14,2), NOT NULL | |
| amount | NUMERIC(14,2), GENERATED ALWAYS AS (quantity * unit_price) STORED | |
| paid_by | VARCHAR(20), NOT NULL, default 'master' | master / client — faqat material uchun ma'noli |
| entry_date | DATE, NOT NULL, default CURRENT_DATE | ish qilingan sana |
| note | TEXT, NULL | |
| receipt_file_id | VARCHAR(255), NULL | Telegram file_id yoki R2 key |
| source | VARCHAR(20), NOT NULL, default 'manual' | manual / voice / ocr |
| updated_at | TIMESTAMPTZ, onupdate=now() | |
| deleted_at | TIMESTAMPTZ, NULL | soft delete |

Index: `(project_id, entry_date)`, `(project_id, kind)`.
CHECK: `quantity > 0`, `unit_price >= 0`.

`amount` uchun SQLAlchemy'da `Computed("quantity * unit_price", persisted=True)` ishlat.

### payments — mijozdan olingan pullar

| Ustun | Tur | Izoh |
|---|---|---|
| project_id | BIGINT FK → projects.id, ON DELETE CASCADE, NOT NULL | |
| created_by_user_id | BIGINT FK → users.id, ON DELETE SET NULL, NULL | |
| amount | NUMERIC(14,2), NOT NULL | |
| method | VARCHAR(20), NOT NULL, default 'cash' | cash / card / transfer |
| paid_at | DATE, NOT NULL, default CURRENT_DATE | |
| note | TEXT, NULL | |
| updated_at | TIMESTAMPTZ, onupdate=now() | |
| deleted_at | TIMESTAMPTZ, NULL | |

Index: `(project_id, paid_at)`.
CHECK: `amount > 0`.

## Konventsiyalar

- SQLAlchemy 2.0 uslubi: `Mapped[...]` va `mapped_column(...)`. Eski `Column()` sintaksisi emas.
- Har bir model alohida faylda: `app/models/user.py`, `project.py`, `price.py`, `entry.py`, `payment.py`.
- `app/models/__init__.py` da hammasini import qil — Alembic autogenerate ularni ko'rishi uchun.
- `created_at` / `updated_at` uchun `TimestampMixin` yoz, takrorlama.
- `deleted_at` uchun `SoftDeleteMixin` yoz.
- Enum qiymatlar uchun Python tomonda `enum.StrEnum` klasslari bo'lsin (`EntryKind`, `Unit`, `PaidBy`, `ProjectStatus`, `PaymentMethod`, `EntrySource`), lekin bazada `VARCHAR` sifatida saqlansin — Postgres ENUM ishlatma, keyin migratsiya qiyin bo'ladi.
- Relationship'lar `lazy="raise"` bilan — tasodifiy N+1 so'rovlarning oldini oladi.
- Type hint'lar hamma joyda.
- Izohlar o'zbek tilida, qisqa.

## Alembic

- `backend/alembic/` ichida, `alembic.ini` `backend/` da.
- **Async** konfiguratsiya (`asyncpg` ishlatiladi) — `env.py` da `async_engine_from_config` va `connection.run_sync`.
- `env.py` da `settings.database_url` dan URL olsin, `alembic.ini` ga parolni yozma.
- `target_metadata = Base.metadata`, `app.models` import qilingan bo'lsin.
- Migratsiya fayli nomi: `alembic/versions/` da, `revision` avtomatik.
- `compare_type=True` va `compare_server_default=True` yoqilsin.

## Seed

`backend/scripts/seed.py` — bitta test usta, bitta loyiha, 5-6 ta narx pozitsiyasi
(shpatlyovka m2, plitka yotqizish m2, bo'yash m2, sement qop, gips qop, quyma pol m2),
2-3 ta entry va bitta payment yaratsin. Idempotent bo'lsin — qayta ishga tushirsa dublikat yaratmasin.

## Qabul mezonlari

Quyidagilar ishlashi shart:

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
docker compose exec api ruff check app
```

Va `docker compose exec db psql -U brigada -d brigada -c "\dt"` da 6 ta jadval ko'rinsin.

## Nima QILMA

- API endpoint yozma — bu keyingi vazifa.
- Pydantic sxemalar yozma — keyingi vazifa.
- Bot handlerlar yozma.
- Mavjud `config.py`, `db.py`, `main.py` ni o'zgartirma (faqat kerak bo'lsa `main.py` ga hech narsa qo'shma).
- `requirements.txt` ga yangi paket qo'shma — hammasi bor.
- Test yozma, hozircha kerak emas.
