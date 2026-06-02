#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deployments/docker-compose.yml"

ok() { echo "OK   $*"; }
warn() { echo "WARN $*"; }
fail() { echo "FAIL $*" >&2; }

overall=0

cd "$ROOT_DIR"

echo "== Git Status =="
git status --short || true

echo
echo "== Ignore Rules =="
if git check-ignore -q deployments/env/backend.env; then
  ok "deployments/env/backend.env is ignored"
else
  fail "deployments/env/backend.env is not ignored"
  overall=1
fi

if git check-ignore -q backups/test.dump && git check-ignore -q backups/test.sql; then
  ok "backup dumps/sql files are ignored"
else
  fail "backup dump/sql ignore rule missing"
  overall=1
fi

echo
echo "== Container Boundary =="
for service in backend frontend; do
  cid="$(docker compose -f "$COMPOSE_FILE" ps -q "$service" || true)"
  if [ -z "$cid" ]; then
    warn "$service container is not running"
    continue
  fi
  mounts="$(docker inspect "$cid" --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}')"
  privileged="$(docker inspect "$cid" --format '{{.HostConfig.Privileged}}')"
  network_mode="$(docker inspect "$cid" --format '{{.HostConfig.NetworkMode}}')"
  pid_mode="$(docker inspect "$cid" --format '{{.HostConfig.PidMode}}')"
  if echo "$mounts" | grep -q "/var/run/docker.sock"; then
    fail "$service has Docker socket mounted"
    overall=1
  else
    ok "$service has no Docker socket"
  fi
  [ "$privileged" = "false" ] && ok "$service not privileged" || { fail "$service privileged=$privileged"; overall=1; }
  [ "$network_mode" != "host" ] && ok "$service not using host network" || { fail "$service uses host network"; overall=1; }
  [ -z "$pid_mode" ] && ok "$service not using host PID" || { fail "$service pid mode=$pid_mode"; overall=1; }
done

worker_cid="$(docker compose -f "$COMPOSE_FILE" ps -q celery_worker || true)"
if [ -n "$worker_cid" ]; then
  worker_mounts="$(docker inspect "$worker_cid" --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}')"
  if echo "$worker_mounts" | grep -q "/var/run/docker.sock"; then
    warn "celery_worker has Docker socket for Containerlab MVP execution"
  else
    warn "celery_worker Docker socket not found; Containerlab execution may fail"
  fi
fi

echo
echo "== Secret Pattern Scan In Tracked Files =="
patterns='github_pat_|sk-[A-Za-z0-9]|AI_API_KEY=.+|JWT_SECRET_KEY=.+|INITIAL_ADMIN_PASSWORD=.+|DEMO_STUDENT_PASSWORD=.+|DEMO_INSTRUCTOR_PASSWORD=.+'
matches="$(git grep -Il -E "$patterns" -- . ':!deployments/env/backend.env.example' || true)"
if [ -n "$matches" ]; then
  warn "secret-like patterns found in tracked files; inspect paths without printing values:"
  echo "$matches"
else
  ok "no secret-like patterns found in tracked files"
fi

exit "$overall"
