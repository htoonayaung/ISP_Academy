# AI-Powered ISP Academy MVP

Phase 1 implements the backend foundation only.

## Phase 1 Scope

Included:

- FastAPI application setup.
- PostgreSQL async SQLAlchemy connection.
- Alembic migration environment.
- Redis readiness check.
- Celery app with Redis broker/backend.
- Docker Compose for backend, PostgreSQL, Redis, and Celery worker.
- pytest tests for foundation endpoints.

Excluded:

- Authentication.
- User model.
- Lab templates.
- Lab instances.
- Containerlab adapter.
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

Phase 1 has no business tables, so migrations should complete without creating application tables.

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

## Security Boundary

The API container has no Docker socket mount and does not execute shell commands or Containerlab. Containerlab integration is intentionally deferred to Phase 4 and must run only through the Celery worker and a dedicated adapter.

