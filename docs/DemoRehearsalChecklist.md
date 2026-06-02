# Demo Rehearsal Checklist

Use this checklist before a live MVP presentation. The goal is to prove the browser demo path without Swagger or curl: Admin Demo Setup, Student Demo Flow, AI Lab Builder mock preview, verification, and cleanup.

## A. Pre-Demo Checks

Run these on the server:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml ps
curl http://10.0.44.2:8000/ready
curl -I http://10.0.44.2:3000
bash scripts/backup_database.sh
```

Expected:

- `backend`, `frontend`, `postgres`, `redis`, and `celery_worker` are running.
- `/ready` returns PostgreSQL and Redis ready.
- Frontend returns HTTP 200.
- A backup file is created under `backups/`.

Confirm demo setup readiness:

1. Open `http://10.0.44.2:3000`.
2. Log in as Admin.
3. Open `Demo Setup`.
4. Confirm the page shows `Demo Ready`.

## B. Docker Service Checks

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml ps
docker compose -f deployments/docker-compose.yml logs --tail=50 backend
docker compose -f deployments/docker-compose.yml logs --tail=50 frontend
docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker
```

Expected:

- Backend has no repeated 500 errors.
- Frontend serves the latest bundle.
- Celery worker is connected to Redis and ready.

## C. Backend Health Checks

```bash
curl http://10.0.44.2:8000/health
curl http://10.0.44.2:8000/ready
curl http://10.0.44.2:8000/api/v1/system/info
```

Expected:

- `/health` returns service status.
- `/ready` confirms PostgreSQL and Redis connectivity.
- System info shows enabled foundation components.

## D. Frontend Access Check

Open:

```text
http://10.0.44.2:3000
```

Expected:

- Login page loads.
- No blank screen.
- Browser console has no critical uncaught errors.

Acceptable for the MVP:

- React Router future warnings.
- HTTP password warning for internal HTTP testing.

## E. Admin Demo Setup Flow

1. Log in as Admin.
2. Open `Demo Setup`.
3. Confirm `Demo Ready`.
4. If not ready, click `Run Demo Setup`.
5. Do not reset demo data unless rehearsal requires a clean start.
6. If resetting, type `RESET_DEMO_DATA` and confirm only after all demo labs are destroyed.

Show these items during the demo:

- Demo users exist.
- Demo Basic Linux Lab exists and is active.
- Demo Linux Verification Ticket exists and is published.
- Demo uname verification rule exists.

## F. Admin Content Flow

Briefly open these pages:

1. `Lab Templates`
2. Demo Basic Linux Lab
3. `Tickets`
4. Demo Linux Verification Ticket
5. Verification rules for the demo ticket
6. `AI Lab Builder`
7. `AI Lab Builder` previews

Keep the explanation short: the MVP supports manual templates and AI preview-first generation, but does not auto-deploy AI output.

## G. Student Demo Flow

1. Log out from Admin.
2. Log in as `demo_student`.
3. Confirm Student sidebar shows only:
   - Dashboard
   - Tickets
   - My Attempts
   - My Labs
4. On Dashboard, click `Start Demo Ticket`.
5. Confirm hidden solution is not visible.
6. Click `Start Attempt`.
7. Confirm Attempt Detail shows the five-step guide.
8. Click `Open Lab`.
9. Click `Start`.
10. Wait until the lab status is `RUNNING`.
11. Return to the attempt.
12. Click `Run Verification`.
13. Wait until the result shows `PASSED`.
14. Open the lab again.
15. Click `Destroy`.
16. Confirm the status reaches `DESTROYED`.
17. Log out.

## H. AI Lab Builder Mock Preview Flow

Use Admin or Instructor:

1. Open `AI Lab Builder`.
2. Confirm provider is configured for mock demo behavior.
3. Generate a preview from a simple Linux/BGP prompt.
4. Review generated YAML, validation, and preview details.
5. Explain that approval creates an inactive LabTemplate.
6. Do not auto-deploy.
7. Do not add real AI keys during a live demo.

## I. Lab Cleanup Check

After the student flow:

```bash
cd /opt/isp-academy
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

Expected:

- No running demo lab containers remain.
- Platform containers remain running.

If a demo lab container remains, destroy it from the lab detail page first. Use Containerlab cleanup manually only as an emergency operator action.

## J. Browser Console Check

Open browser developer tools and confirm there are no critical errors:

- No `Uncaught Error`.
- No `Uncaught in promise`.
- No CORS errors.
- No `Cannot read properties of undefined`.
- No validation crash messages.
- No 401 loop.

## K. What To Say During The Demo

- This is a single-server MVP for 20 to 50 users, not an enterprise deployment.
- Containerlab execution is isolated to the Celery worker.
- API and frontend containers do not have Docker socket access.
- Student users see only published tickets, own attempts, and own labs.
- Hidden solutions are staff-only.
- AI Lab Builder is preview-first and validation-first.
- AI output is untrusted and never auto-deployed.
- Worker host access is an MVP technical debt to reduce before broader production use.

## L. What Not To Click During The Demo

- Do not click Demo Reset unless intentionally rehearsing reset.
- Do not change real provider AI settings.
- Do not enter or show API keys.
- Do not expose `backend.env`.
- Do not show real admin passwords.
- Do not start multiple labs repeatedly without cleanup.
- Do not use shell/containerlab commands for normal student demo flow.

## M. Fallback Plan If Containerlab Lab Start Fails

1. Stay in the browser and explain that the lab worker performs all Containerlab operations.
2. Open the lab events table and show sanitized lifecycle events.
3. Check worker logs:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker
```

4. Confirm Docker and Containerlab are available:

```bash
docker ps
containerlab version
```

5. If needed, destroy the failed lab from the UI.
6. Start a fresh attempt only after cleanup.
7. Continue the demo with AI Lab Builder preview and architecture/security explanation if live lab runtime cannot recover quickly.
