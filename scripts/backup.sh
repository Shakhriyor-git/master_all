#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
STAMP=$(date +%Y%m%d_%H%M)
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "backups/db_$STAMP.sql.gz"
find backups -name 'db_*.sql.gz' -mtime +14 -delete
echo "Backup: backups/db_$STAMP.sql.gz"
