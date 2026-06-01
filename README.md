# AI-Powered ISP Academy MVP

Phase 4 implements the Containerlab lab engine for MVP lab instances.

## Current Scope

Included:

- FastAPI application setup.
- PostgreSQL async SQLAlchemy connection.
- Alembic migration environment.
- Redis readiness check.
- Celery app with Redis broker/backend.
- Docker Compose for backend, PostgreSQL, Redis, and Celery worker.
- User model.
- Argon2 password hashing.
- JWT access tokens.
- Admin, Instructor, and Student roles.
- User management APIs.
- Lab template CRUD and safety validation.
- Lab instance lifecycle APIs.
- Worker-only Containerlab deploy, inspect, and destroy operations.
- Lab nodes and lab event history.
- pytest tests for foundation, auth, users, lab templates, labs, lifecycle, and adapter safety.

Excluded:

- Tickets.
- Verification.
- AI Lab Builder.
- AI Mentor.
- Frontend.
- Business database tables.

## Run With Docker Compose

```bash
cd /opt/isp-academy/deployments
cp env/backend.env.example env/backend.env
docker compose up -d --build
```

## Run Alembic

```bash
cd /opt/isp-academy/deployments
docker compose exec backend alembic upgrade head
```

Phase 4 creates `users`, `lab_templates`, `lab_instances`, `lab_nodes`, and `lab_events`.

## Seed Initial Admin

```bash
cd /opt/isp-academy/deployments
docker compose exec backend python -m app.scripts.seed_admin
```

## Run Tests

```bash
cd /opt/isp-academy/deployments
docker compose exec backend pytest
```

## API Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/system/info
```

## Auth Checks

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"INITIAL_ADMIN_PASSWORD"}'
```

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Lab Checks

```bash
curl -X POST http://localhost:8000/api/v1/labs \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template_id":"LAB_TEMPLATE_ID"}'
```

```bash
curl -X POST http://localhost:8000/api/v1/labs/LAB_ID/start \
  -H "Authorization: Bearer ACCESS_TOKEN"

curl http://localhost:8000/api/v1/labs/LAB_ID/status \
  -H "Authorization: Bearer ACCESS_TOKEN"

curl http://localhost:8000/api/v1/labs/LAB_ID/nodes \
  -H "Authorization: Bearer ACCESS_TOKEN"

curl -X POST http://localhost:8000/api/v1/labs/LAB_ID/destroy \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Security Boundary

The API container has no Docker socket mount and does not execute shell commands or Containerlab. It must not run privileged, use host networking, or use host PID mode.

Containerlab operations run only through the Celery worker and `ContainerlabAdapter`. For this single-server MVP, the worker has controlled host access because Containerlab needs Docker socket and host network visibility:

- `celery_worker` has `/var/run/docker.sock`.
- `celery_worker` runs privileged.
- `celery_worker` uses host network and host PID mode.
- `backend` API has none of those privileges.

This worker privilege model is MVP-only technical debt. Before any broader deployment, isolate the lab executor further and replace broad worker privileges with a narrower host-side execution boundary.
