#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENTS_DIR="$ROOT_DIR/deployments"
BACKUP_DIR="$ROOT_DIR/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="$BACKUP_DIR/isp_academy_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

cd "$DEPLOYMENTS_DIR"
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$OUTPUT_FILE"

if [ ! -s "$OUTPUT_FILE" ]; then
  echo "Backup file was created but is empty: $OUTPUT_FILE" >&2
  exit 1
fi

echo "Database backup written to: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE" | awk '{print "Backup size: " $5}'
