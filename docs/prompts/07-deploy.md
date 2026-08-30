# Vazifa 07 — DigitalOcean'ga deploy

## Ma'lumot

| | |
|---|---|
| Droplet | `masterspro`, FRA1, Ubuntu 24.04, 1 GB RAM |
| IP | `134.122.75.117` |
| Domen | `134-122-75-117.sslip.io` (bepul, sozlash shart emas) |
| Repo | `github.com/Shakhriyor-git/master_all` |
| Bot | `@masters_pro_bot` |

Bu vazifa ikki qismdan iborat:

- **1-qism — Claude Code:** repoga prod fayllarini qo'shadi
- **2-qism — siz:** serverda komandalarni bajarasiz

---

# 1-QISM — Claude Code uchun

## 1.1. `Caddyfile` (repo ildizida)

```
{$DOMAIN} {
    encode gzip

    handle /api/* {
        reverse_proxy api:8000
    }
    handle /docs* {
        reverse_proxy api:8000
    }
    handle /openapi.json {
        reverse_proxy api:8000
    }
    handle /media/* {
        reverse_proxy api:8000
    }
    handle /tg/* {
        reverse_proxy api:8000
    }

    handle {
        root * /srv/frontend
        try_files {path} /index.html
        file_server
    }

    header {
        Strict-Transport-Security "max-age=31536000"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
}
```

Frontend hali tayyor emas — `/srv/frontend` bo'sh bo'lsa Caddy 404 qaytaradi,
bu normal. API baribir ishlaydi.

## 1.2. `docker-compose.prod.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
    command: >
      postgres
      -c shared_buffers=128MB
      -c max_connections=20
      -c work_mem=4MB
      -c maintenance_work_mem=64MB

  api:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - avatars:/data/avatars
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      DOMAIN: ${DOMAIN}
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./frontend-dist:/srv/frontend:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - api

volumes:
  pgdata:
  avatars:
  caddy_data:
  caddy_config:
```

**Diqqat:** `db` da `ports` yo'q — Postgres tashqariga chiqmaydi.
Alohida `bot` servisi ham yo'q — prodda bot webhook orqali `api` ichida ishlaydi.

## 1.3. Bot webhook rejimi

`app/main.py` da `lifespan` ichida:

- `settings.bot_use_webhook` **true** bo'lsa:
  - Aiogram dispatcher va middleware'lar sozlanadi
  - `POST /tg/{WEBHOOK_SECRET}` route qo'shiladi, `SimpleRequestHandler` orqali
  - Ishga tushganda `bot.set_webhook(f"{PUBLIC_URL}/tg/{WEBHOOK_SECRET}", secret_token=..., drop_pending_updates=True)`
  - To'xtaganda `bot.delete_webhook()`
- **false** bo'lsa hech narsa qilinmaydi (lokalda polling alohida konteynerda)

Telegram `X-Telegram-Bot-Api-Secret-Token` sarlavhasini tekshirish shart —
aks holda istalgan odam soxta update yubora oladi.

Webhook URL'da tasodifiy `WEBHOOK_SECRET` bo'lgani ikkinchi himoya qatlami.

## 1.4. `.env.prod.example`

```
ENV=production
DEBUG=false
SECRET_KEY=<openssl rand -hex 32 bilan yasang>
PUBLIC_URL=https://134-122-75-117.sslip.io
DOMAIN=134-122-75-117.sslip.io

POSTGRES_USER=brigada
POSTGRES_PASSWORD=<openssl rand -hex 24>
POSTGRES_DB=brigada
POSTGRES_HOST=db
POSTGRES_PORT=5432

BOT_TOKEN=<BotFather tokeni>
WEBAPP_URL=https://134-122-75-117.sslip.io
BOT_USE_WEBHOOK=true
WEBHOOK_SECRET=<openssl rand -hex 24>

CORS_ORIGINS=https://134-122-75-117.sslip.io

GEMINI_API_KEY=
GROQ_API_KEY=
```

## 1.5. `scripts/backup.sh`

```bash
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
STAMP=$(date +%Y%m%d_%H%M)
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "backups/db_$STAMP.sql.gz"
find backups -name 'db_*.sql.gz' -mtime +14 -delete
echo "Backup: backups/db_$STAMP.sql.gz"
```

14 kunlik nusxa saqlanadi, eskisi o'chadi.

## 1.6. `Makefile` ga prod komandalar

```
prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f api

prod-migrate:
	docker compose -f docker-compose.prod.yml exec api alembic upgrade head

prod-backup:
	bash scripts/backup.sh
```

## 1.7. `.github/workflows/deploy.yml`

`main` ga push bo'lganda:

1. Frontend'ni **GitHub Actions ichida** build qiladi (`npm ci && npm run build`)
   — serverda emas, 1 GB RAM yetmaydi
2. `dist/` ni serverdagi `~/master_all/frontend-dist/` ga `rsync` bilan yuboradi
3. SSH orqali: `git pull`, `docker compose -f docker-compose.prod.yml up -d --build`,
   `alembic upgrade head`
4. `curl -f https://$DOMAIN/api/health` bilan tekshiradi, xato bo'lsa workflow yiqiladi

Secrets: `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `DOMAIN`.

`frontend/` papkasi mavjud bo'lmasa build qadamini o'tkazib yuborsin —
hozir A bosqichda u endi paydo bo'lyapti.

## 1.8. `.gitignore` ga

```
.env.prod
backups/
frontend-dist/
```

## Nima QILMA

- Lokal `docker-compose.yml` ni o'zgartirma — u dev uchun qoladi
- Botni qayta yozma, faqat webhook rejimini qo'sh
- Modellarga tegma

---

# 2-QISM — siz serverda bajarasiz

Bularni **1-qism tugagach** bajaring.

## 2.1. Serverga kirish va boshlang'ich sozlash

```bash
ssh root@134.122.75.117
```

```bash
apt update && apt upgrade -y

# 2 GB swap — 1 GB RAM da majburiy
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Oddiy foydalanuvchi
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Firewall
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
```

## 2.2. Docker

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy
```

## 2.3. Repo va sozlama

```bash
su - deploy
git clone https://github.com/Shakhriyor-git/master_all.git
cd master_all
cp .env.prod.example .env
nano .env
```

`.env` da to'ldiring. Maxfiy qiymatlarni server ichida yasang:

```bash
openssl rand -hex 32    # SECRET_KEY
openssl rand -hex 24    # POSTGRES_PASSWORD
openssl rand -hex 24    # WEBHOOK_SECRET
```

`BOT_TOKEN` — BotFather'dan olganingiz.

## 2.4. Ishga tushirish

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml logs -f caddy
```

Caddy loglarida sertifikat olingani ko'rinishi kerak (30-60 soniya).

Tekshiring:

```bash
curl https://134-122-75-117.sslip.io/api/health
```

## 2.5. Webhook tekshiruvi

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

`"url"` to'ldirilgan va `"last_error_message"` bo'sh bo'lishi kerak.

Telegramda `@masters_pro_bot` ga `/start` yuboring.

## 2.6. Kunlik backup

```bash
crontab -e
```

Qo'shing:

```
0 3 * * * cd /home/deploy/master_all && bash scripts/backup.sh >> backups/cron.log 2>&1
```

## 2.7. BotFather'da Mini App

Frontend tayyor bo'lgach:

```
/setmenubutton
@masters_pro_bot
https://134-122-75-117.sslip.io
Ochish
```

## 2.8. GitHub Actions uchun kalit

Kompyuteringizda:

```cmd
type %USERPROFILE%\.ssh\id_ed25519
```

To'liq matnni GitHub → repo → Settings → Secrets and variables → Actions →
`SSH_KEY` ga joylang. Yana: `SSH_HOST=134.122.75.117`, `SSH_USER=deploy`,
`DOMAIN=134-122-75-117.sslip.io`.

---

## Qabul mezoni

- `https://134-122-75-117.sslip.io/api/health` → `{"status":"ok","env":"production"}`
- `/docs` ochilmaydi (prodda o'chirilgan)
- Botga `/start` javob beradi
- `getWebhookInfo` da xato yo'q
- `bash scripts/backup.sh` fayl yaratadi
- `free -h` da swap ko'rinadi
