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

If the frontend container is healthy but the page still fails, check browser devtools for cached assets and confirm `VITE_API_BASE_URL` was correct during the frontend build.

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

Run the full health script:

```bash
cd /opt/isp-academy
bash scripts/check_system_health.sh
```

## Redis Or PostgreSQL Issue

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml ps
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 postgres
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 redis
```

If PostgreSQL is unhealthy, check disk space before restarting:

```bash
df -h
docker system df
```

## Celery Worker Issue

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
docker compose -f /opt/isp-academy/deployments/docker-compose.yml restart celery_worker
```

The worker is intentionally privileged in the MVP because it executes Containerlab operations. This is technical debt and must be isolated before production.

If the worker is not processing jobs, confirm Redis is healthy and that the worker was rebuilt after code changes:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml up -d --build celery_worker
```

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

If `containerlab: command not found`, install Containerlab on the host and confirm `/usr/bin/containerlab` exists because the worker mounts it read-only.

If permission errors mention Docker socket or host networking, confirm only `celery_worker` has `/var/run/docker.sock`, privileged mode, host network, and host PID:

```bash
bash /opt/isp-academy/scripts/security_smoke_check.sh
```

## Lab Stuck STARTING

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
docker ps
containerlab inspect --all
```

Destroy the lab from the UI when possible. If it remains stuck, log in as Admin and open `Lab Runtime`.

Recommended order:

1. Click `Refresh`.
2. Review recent events.
3. Use `Mark failed` if the lab has been transient too long and you only need to unblock DB state.
4. Use `Retry destroy` if runtime resources may still exist.

If manual cleanup is required, verify the lab path stays under `/opt/isp-academy/lab-storage` before deleting anything.

## Lab Stuck DESTROYING

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
containerlab inspect --all
docker ps --filter "name=clab"
```

Do not hard-delete a running or destroying lab record. Open `Lab Runtime` as Admin, use `Refresh`, then `Retry destroy`.

Use `Force destroy demo` only for demo-prefixed labs with typed confirmation `RECOVER_LAB`. Keep cleanup inside `LAB_ROOT`.

## Runtime Ops Page Fails

If `Lab Runtime` returns `403`, confirm the logged-in user has `ADMIN` role. Students and instructors cannot access global runtime operations.

If the page returns `409`, the backend is blocking an unsafe recovery action such as forcing a non-demo lab.

If cleanup is uncertain, the backend skips and warns instead of deleting.

## Topology Diagram Missing

If a template, lab, or AI preview page shows `Could not parse topology`, validate the Containerlab YAML or regenerate the AI preview.

Supported link format:

```yaml
links:
  - endpoints: ["r1:eth1", "r2:eth1"]
```

Unknown endpoints show warnings but should not crash the page. The topology viewer is read-only and does not provide router console access.

## Verification Stuck RUNNING

Confirm the lab is `RUNNING`, the target node exists, and the worker is running:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml logs --tail=100 celery_worker
```

Review the verification rule command and expected value from the UI.

## Delete Blocked

Guarded delete actions return `409` when references or active state make deletion unsafe.

Common cases:

- User has tickets, templates, labs, attempts, or events.
- Ticket has student attempts.
- Template has tickets or lab history.
- Lab is running or linked to an attempt.
- Verification rule has run history.

Use deactivate/archive, or delete dependent demo data in the correct order.

## Docker Cleanup Commands

Use cautiously:

```bash
docker compose -f /opt/isp-academy/deployments/docker-compose.yml ps
docker ps
docker system df
docker container prune
```

Do not prune volumes unless you have a fresh PostgreSQL and lab storage backup.

If Docker disk is full:

```bash
docker system df
du -sh /opt/isp-academy/backups
du -sh /opt/isp-academy/lab-storage
```

Prefer UI lab destroy and verified backups before pruning.

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

## Natural Language Prompt Returns INVALID

Users should type plain English, not JSON. Good examples:

- `Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule.`
- `Create a two-router FRR eBGP lab with one point-to-point link and a BGP neighbor verification rule.`
- `Create a basic Linux lab with one Alpine host named host1 and a uname verification rule.`
- `Create a two-router FRR static routing lab with one point-to-point link and a route verification rule.`

If the preview says the request could not be safely interpreted, use one of the example prompts or add the protocol, node count, and verification goal.

If validation mentions unsupported images, privileged containers, host mounts, external networks, or vendor devices, the request is intentionally blocked by security validation.

## Real Provider Rate Limit Or Invalid Response

OpenRouter/Groq/Gemini free models can return rate limits or incomplete responses. Use mock mode for demos, retry later, or choose a different model. The backend should store an invalid preview with a friendly error rather than exposing provider internals.

## GitHub Push Auth Issue

If HTTPS push fails with username/token prompts, prefer SSH remote:

```bash
git remote set-url origin git@github.com:htoonayaung/ISP_Academy.git
git push
```

Never paste GitHub tokens into chat, docs, screenshots, or shell history.

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
