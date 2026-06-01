#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: bash scripts/restore_database.sh <backup-file.dump>" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENTS_DIR="$ROOT_DIR/deployments"
BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  if [ -f "$ROOT_DIR/$BACKUP_FILE" ]; then
    BACKUP_FILE="$ROOT_DIR/$BACKUP_FILE"
  else
    echo "Backup file not found: $1" >&2
    exit 1
  fi
fi

cd "$DEPLOYMENTS_DIR"
cat "$BACKUP_FILE" | docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

echo "Database restored from: $BACKUP_FILE"
