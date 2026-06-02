#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deployments/docker-compose.yml"
BACKEND_URL="${BACKEND_URL:-http://10.0.44.2:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://10.0.44.2:3000}"

ok() { echo "OK   $*"; }
fail() { echo "FAIL $*" >&2; }

overall=0

echo "== Docker Compose Services =="
if docker compose -f "$COMPOSE_FILE" ps; then
  ok "docker compose ps completed"
else
  fail "docker compose ps failed"
  overall=1
fi

echo
echo "== Backend Health =="
if curl -fsS "$BACKEND_URL/health" >/dev/null; then
  ok "backend /health"
else
  fail "backend /health"
  overall=1
fi

if curl -fsS "$BACKEND_URL/ready" >/dev/null; then
  ok "backend /ready"
else
  fail "backend /ready"
  overall=1
fi

echo
echo "== Frontend =="
if curl -fsSI "$FRONTEND_URL" >/dev/null; then
  ok "frontend HTTP"
else
  fail "frontend HTTP"
  overall=1
fi

echo
echo "== Containerlab =="
if containerlab version >/dev/null 2>&1; then
  containerlab version
  ok "containerlab available"
else
  fail "containerlab command not found or not executable"
  overall=1
fi

exit "$overall"
