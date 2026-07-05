#!/usr/bin/env sh
# Consistent SQLite backup from the running compose stack (safe under WAL).
# Usage: ./scripts/backup.sh  → backups/habitflow-YYYYmmdd-HHMMSS.db
set -eu

STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backups

docker compose exec -T api python -c "
import sqlite3
src = sqlite3.connect('/srv/app/data/habitflow.db')
dst = sqlite3.connect('/srv/app/data/backup.db')
src.backup(dst)
dst.close(); src.close()
print('snapshot created')
"
docker compose cp api:/srv/app/data/backup.db "backups/habitflow-$STAMP.db"
docker compose exec -T api rm -f /srv/app/data/backup.db
echo "backups/habitflow-$STAMP.db"
