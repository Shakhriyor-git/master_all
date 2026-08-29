# Brigada

Qurilish va remont brigadalari uchun ish hamda xarajat hisobini yuritish tizimi.
Telegram bot + Mini App orqali ishlaydi.

## Stack

| Qism | Texnologiya |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Bot | Aiogram 3 |
| Baza | PostgreSQL 16 |
| Frontend | React + Telegram Web App SDK *(keyingi bosqich)* |
| Deploy | Docker Compose, DigitalOcean |

## Lokal ishga tushirish

Kerak: Docker va Docker Compose.

```bash
cp .env.example .env
make up
```

Tekshirish:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

Swagger: http://localhost:8000/docs

## Komandalar

```bash
make up       # ko'tarish
make down     # to'xtatish
make logs     # loglar
make sh       # konteynerga kirish
make db       # psql
make lint     # kod tekshiruvi
```

## Struktura

```
backend/
  app/
    main.py         FastAPI entrypoint
    core/           config, db ulanishi
    api/routes/     HTTP endpointlar
    models/         SQLAlchemy modellar
    schemas/        Pydantic sxemalar
    services/       biznes-logika
    bot/            Aiogram handlerlar
docs/               texnik hujjatlar
```

## Bosqichlar

- [x] 0. Repo skeleti, Docker, health check
- [ ] 1. DB sxemasi va migratsiyalar
- [ ] 2. Telegram initData autentifikatsiya
- [ ] 3. Loyihalar va ishlar CRUD
- [ ] 4. Mini App (React)
- [ ] 5. Excel hisobot
- [ ] 6. Chek OCR
- [ ] 7. Ovozli kiritish
