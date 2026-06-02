#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deployments/docker-compose.yml"
LAB_ROOT="${LAB_ROOT:-/opt/isp-academy/lab-storage}"

echo "== Containerlab Labs =="
if command -v containerlab >/dev/null 2>&1; then
  containerlab inspect --all || true
else
  echo "WARN containerlab command not found"
fi

echo
echo "== Docker clab Containers =="
docker ps --filter "name=clab" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}" || true

echo
echo "== Lab Storage =="
if [ -d "$LAB_ROOT" ]; then
  du -sh "$LAB_ROOT" || true
  if [ -d "$LAB_ROOT/instances" ]; then
    find "$LAB_ROOT/instances" -mindepth 1 -maxdepth 1 -type d | wc -l | awk '{print "instances directories: " $1}'
  else
    echo "instances directories: 0"
  fi
else
  echo "WARN lab root not found: $LAB_ROOT"
fi

echo
echo "== Backend Lab Status Counts =="
if docker compose -f "$COMPOSE_FILE" ps -q postgres >/dev/null 2>&1; then
  docker compose -f "$COMPOSE_FILE" exec -T postgres sh -c '
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
      select status, count(*) from lab_instances group by status order by status;
    " 2>/dev/null || echo "WARN lab_instances table unavailable"
  '
else
  echo "WARN postgres container unavailable"
fi

echo
echo "No cleanup was performed."
echo "Use the Admin UI Runtime Ops page or /api/v1/admin/runtime/labs/status for confirmation-protected recovery."
