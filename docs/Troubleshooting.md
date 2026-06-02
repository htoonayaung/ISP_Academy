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

## Management Action Fails

If a management action returns `403`, confirm the current role is allowed:

- Only Admin can deactivate/reactivate users and reset passwords.
- Instructors can manage only their own templates, tickets, verification rules, and related attempts.
- Students cannot see staff action buttons and cannot call staff endpoints.

If an action returns `409`, it is usually a safety guard:

- The current admin cannot deactivate itself.
- A ticket cannot be published unless its lab template is active.
- A lab cannot start, stop, or destroy from an unsafe lifecycle state.

Use deactivate/archive instead of hard delete for normal cleanup.

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

# AI Lab Builder Provider Troubleshooting

## Mock Provider

Use mock mode for demos and normal development:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=mock
AI_MODEL=mock
```

If preview creation fails in mock mode, check backend logs and confirm the backend service was restarted after changing `deployments/env/backend.env`.

## Real Provider Confirmation

When `AI_PROVIDER` is not `mock` and `AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true`, preview creation requires explicit confirmation from the UI or API payload:

```json
{
  "prompt": "Create a basic Linux lab with one Alpine host named host1.",
  "confirm_real_provider_usage": true
}
```

If confirmation is missing, the API returns:

```text
Real AI provider usage requires explicit confirmation.
```

## Provider Status

Admin users can check safe provider status at:

```text
GET /api/v1/ai-lab-builder/provider/status
```

The response never includes `AI_API_KEY`. It returns only `has_api_key` and a host-only base URL.

## Daily Preview Limit

For real providers, `AI_DAILY_PREVIEW_LIMIT_PER_USER` limits preview creation per user per day. Mock mode is intended for demos and avoids accidental quota usage.

# Demo Setup Troubleshooting

## Demo Setup Disabled

If Demo Setup returns disabled, check:

```bash
grep DEMO_SETUP_ENABLED /opt/isp-academy/deployments/env/backend.env
```

Set `DEMO_SETUP_ENABLED=true` and restart backend.

## Duplicate Demo Data

Demo setup is idempotent. It should report existing demo records instead of duplicating them. If duplicate-looking data appears, check slugs/usernames start with `demo_` or `demo-`.

## Demo Reset Blocked

If reset is blocked due to running demo labs, destroy those demo labs from the UI first. Reset does not destroy running labs unless explicitly supported and confirmed.

## Demo Account Login Issue

If demo passwords were generated, they are shown only in the setup response. Run reset and setup again if you lost generated demo credentials.
