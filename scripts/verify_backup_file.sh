#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: bash scripts/verify_backup_file.sh backups/<filename>.dump" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ] && [ -f "$ROOT_DIR/$BACKUP_FILE" ]; then
  BACKUP_FILE="$ROOT_DIR/$BACKUP_FILE"
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "FAIL backup file not found: $1" >&2
  exit 1
fi

echo "OK   backup file exists: $BACKUP_FILE"
echo "Size:"
ls -lh "$BACKUP_FILE" | awk '{print "  " $5 " " $9}'

if command -v file >/dev/null 2>&1; then
  echo "Type:"
  file "$BACKUP_FILE"
else
  echo "WARN file command not available"
fi

if [ ! -s "$BACKUP_FILE" ]; then
  echo "FAIL backup file is empty" >&2
  exit 1
fi

echo "WARN restore should be tested on staging before relying on this backup."
echo "No restore was performed."
