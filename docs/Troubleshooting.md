# Troubleshooting

Run commands from the server unless noted otherwise.

## Frontend Blank Page

Check the frontend container:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml ps
docker compose -f deployments/docker-compose.yml logs --tail=100 frontend
```

Rebuild the frontend:

```bash
docker compose -f deployments/docker-compose.yml up -d --build frontend
```

## Login Problem

Confirm backend readiness:

```bash
curl http://10.0.44.2:8000/ready
```

Confirm the account is active from an admin login or reseed the initial admin:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml exec backend python -m app.scripts.seed_admin
```

## Token Problem

The MVP frontend stores the JWT in `localStorage` key `isp_academy_token`.

In the browser console:

```javascript
localStorage.getItem("isp_academy_token")
localStorage.removeItem("isp_academy_token")
```

If `/api/v1/auth/me` returns `401`, log in again.

## CORS Issue

Confirm `CORS_ORIGINS` includes the frontend URL:

```bash
grep CORS_ORIGINS /opt/isp-academy/deployments/env/backend.env
```

Restart backend:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml up -d --build backend
```

## Backend Not Ready

```bash
curl http://10.0.44.2:8000/health
curl http://10.0.44.2:8000/ready
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 backend
```

## Redis Or PostgreSQL Issue

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml ps
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 postgres
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 redis
```

## Celery Worker Issue

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
docker compose -f /opt/isp-academy/deployments/docker-compose.yml restart celery_worker
```

The worker is intentionally privileged in the MVP because it executes Containerlab operations. This is technical debt and must be isolated before production.

## Containerlab Deploy Issue

Check versions and host access:

```bash
containerlab version
docker version
docker ps
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
```

Check lab storage:

```bash
ls -lah /opt/isp-academy/lab-storage
```

## Lab Stuck STARTING

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
docker ps
containerlab inspect --all
```

Destroy the lab from the UI when possible. If manual cleanup is required, verify the lab path stays under `/opt/isp-academy/lab-storage` before deleting anything.

## Verification Stuck RUNNING

Confirm the lab is `RUNNING`, the target node exists, and the worker is running:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
```

Review the verification rule command and expected value from the UI.

## Docker Cleanup Commands

Use cautiously:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml ps
docker ps
docker system df
docker container prune
```

Do not prune volumes unless you have a fresh PostgreSQL and lab storage backup.

## Useful Logs

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml logs --tail=100 frontend
docker compose -f deployments/docker-compose.yml logs --tail=100 backend
docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker
docker compose -f deployments/docker-compose.yml logs --tail=100 postgres
docker compose -f deployments/docker-compose.yml logs --tail=100 redis
```
