#!/usr/bin/env bash
#
# Prod bazasini zaxiralash.
#
# Xatoni YASHIRMAYDI: pg_dump yiqilsa yoki fayl bo'sh chiqsa — skript
# to'xtaydi, yaroqsiz faylni o'chiradi va exit 1 qaytaradi.
#
set -euo pipefail

# Yo'llar skript papkasiga nisbatan — cron qayerdan chaqirmasin, ishlaydi
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "XATO: .env topilmadi ($(pwd)/.env)" >&2
  exit 1
fi

# POSTGRES_USER / POSTGRES_DB va h.k. .env dan o'qiladi
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_USER:?.env da POSTGRES_USER yo'q}"
: "${POSTGRES_DB:?.env da POSTGRES_DB yo'q}"

STAMP=$(date +%Y%m%d_%H%M)
mkdir -p backups
OUT="backups/db_${STAMP}.sql.gz"

# pipefail yoqilgan — gzip muvaffaqiyatli bo'lsa ham pg_dump'ning xato
# statusi STATUS ga tushadi. set -e ni vaqtincha o'chiramiz: avval
# tozalash, keyin exit 1.
set +e
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT"
STATUS=$?
set -e

# Hajm — BAYT aniqligida (bloklarda emas: 20 baytlik bo'sh gz o'tib ketmasin)
SIZE=$(stat -c%s "$OUT" 2>/dev/null || wc -c < "$OUT" 2>/dev/null || echo 0)

if (( STATUS != 0 )) || (( SIZE < 1024 )); then
  echo "XATO: backup muvaffaqiyatsiz (pg_dump status=$STATUS, hajm=${SIZE} bayt)." >&2
  echo "Yaroqsiz fayl o'chirildi: $OUT" >&2
  rm -f "$OUT"
  exit 1
fi

# Eski zaxiralar (14 kundan oshgan) — faqat yangi backup joyida bo'lsa
find backups -name 'db_*.sql.gz' -mtime +14 -delete

HUMAN=$(numfmt --to=iec --suffix=B "$SIZE" 2>/dev/null || echo "${SIZE} bayt")
echo "Backup OK: $OUT ($HUMAN)"
