# AI-Powered ISP Academy MVP

Phase 2 implements simple authentication and role-based user management.

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
- pytest tests for foundation, auth, users, and permissions.

Excluded:

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

Phase 2 creates the `users` table and `user_role` enum.

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

## Security Boundary

The API container has no Docker socket mount and does not execute shell commands or Containerlab. Containerlab integration is intentionally deferred to Phase 4 and must run only through the Celery worker and a dedicated adapter.
