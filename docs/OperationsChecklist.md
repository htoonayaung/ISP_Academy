# Operations Checklist

Run commands from `/opt/isp-academy` unless noted otherwise.

## Daily Checks

```bash
docker compose -f deployments/docker-compose.yml ps
bash scripts/check_system_health.sh
du -sh /opt/isp-academy/lab-storage
du -sh /opt/isp-academy/backups
```

Confirm:

- Backend and frontend are healthy.
- PostgreSQL and Redis are healthy.
- Celery worker is running.
- Disk usage is not growing unexpectedly.

## Weekly Checks

```bash
bash scripts/security_smoke_check.sh
bash scripts/check_lab_runtime_state.sh
docker system df
bash scripts/backup_database.sh
latest="$(ls -t backups/*.dump | head -n 1)"
bash scripts/verify_backup_file.sh "$latest"
```

Copy important backups off the server.

## Before Demo

```bash
docker compose -f deployments/docker-compose.yml ps
bash scripts/check_system_health.sh
bash scripts/security_smoke_check.sh
bash scripts/backup_database.sh
```

Also confirm:

- Demo Setup page reports ready.
- AI provider status is expected.
- No unexpected running labs exist.
- Browser can open the frontend.

## After Demo Cleanup

```bash
bash scripts/check_lab_runtime_state.sh
docker ps --filter "name=clab"
du -sh /opt/isp-academy/lab-storage
```

Destroy demo labs from the UI. If a demo lab is stuck, open `Lab Runtime` as Admin and use `Refresh` first, then `Retry destroy` or `Force destroy demo` only when eligible. Do not manually delete outside `LAB_ROOT`.

Use `Cleanup demo runtime` only after verifying it is restricted to demo-prefixed destroyed or failed artifacts.

## Log Checks

```bash
docker compose -f deployments/docker-compose.yml logs --tail=100 frontend
docker compose -f deployments/docker-compose.yml logs --tail=100 backend
docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker
docker compose -f deployments/docker-compose.yml logs --tail=100 postgres
docker compose -f deployments/docker-compose.yml logs --tail=100 redis
```

## Backup Checks

```bash
bash scripts/backup_database.sh
ls -lh backups/
bash scripts/verify_backup_file.sh backups/<filename>.dump
```

Database backups do not include `backend.env`, AI keys, JWT secret, Docker images, or lab runtime files.

## AI Provider Check

Open AI Lab Builder as Admin and review Provider Status. It must never display the API key value.

## Router Console Check

For a running FRR lab, open Lab Detail, click a router node, and run:

```text
show ip route
```

Confirm unsafe commands are blocked and that backend/frontend still have no Docker socket by running:

```bash
bash scripts/security_smoke_check.sh
```

## Git Safety Before Commit

```bash
git status --short
bash scripts/security_smoke_check.sh
```

Never commit secrets, backup dumps, screenshots containing keys, or runtime `.env` files.
