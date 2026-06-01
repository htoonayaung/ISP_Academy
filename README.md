# AI-Powered ISP Academy MVP

Phase 7 implements the minimal React frontend MVP on top of the Phase 6 backend.

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
- Ticket management linked to lab templates.
- Student ticket attempts that create LabInstances in `CREATED` state.
- Instructor-defined verification rules for tickets.
- Student verification runs against own running lab attempts.
- Verification results with safe pass/fail output.
- Minimal React, TypeScript, TailwindCSS frontend.
- Login/logout using JWT access tokens.
- Role-aware navigation for Admin, Instructor, and Student users.
- Frontend pages for users, lab templates, labs, tickets, attempts, verification rules, and verification runs.
- Docker Compose for backend, frontend, PostgreSQL, Redis, and Celery worker.
- pytest tests for foundation, auth, users, lab templates, labs, tickets, verification, lifecycle, and adapter safety.

Excluded:

- AI Lab Builder.
- AI Mentor.
- Production-grade frontend session hardening.
- Advanced UI workflows such as lab console streaming, drag-and-drop topology editing, and analytics.

## Run With Docker Compose

```bash
cd /opt/isp-academy/deployments
cp env/backend.env.example env/backend.env
docker compose up -d --build
```

Frontend is served on:

```text
http://10.0.44.2:3000
```

Backend API is served on:

```text
http://10.0.44.2:8000
```

## Run Alembic

```bash
cd /opt/isp-academy/deployments
docker compose exec backend alembic upgrade head
```

The backend migrations create `users`, `lab_templates`, `lab_instances`, `lab_nodes`, `lab_events`, `tickets`, `ticket_attempts`, `verification_rules`, `verification_runs`, and `verification_results`.

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

## Ticket Checks

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lab_template_id": "LAB_TEMPLATE_ID",
    "title": "Basic ISP Troubleshooting",
    "description": "Find and fix the reported issue.",
    "student_instructions": "Use the lab topology and diagnose the fault.",
    "hints": "Start with interface and routing status.",
    "hidden_solution": "Instructor-only solution text.",
    "status": "DRAFT"
  }'
```

```bash
curl -X POST http://localhost:8000/api/v1/tickets/TICKET_ID/publish \
  -H "Authorization: Bearer ACCESS_TOKEN"

curl http://localhost:8000/api/v1/tickets \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"

curl -X POST http://localhost:8000/api/v1/tickets/TICKET_ID/start \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"

curl http://localhost:8000/api/v1/my/attempts \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

## Verification Checks

```bash
curl -X POST http://localhost:8000/api/v1/tickets/TICKET_ID/verification-rules \
  -H "Authorization: Bearer ADMIN_OR_OWNER_INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Check node output",
    "target_node": "host1",
    "command": "echo ok",
    "parser_type": "SIMPLE_TEXT",
    "assertion_type": "CONTAINS",
    "expected_value": "ok",
    "timeout_seconds": 5,
    "is_active": true
  }'
```

```bash
curl -X POST http://localhost:8000/api/v1/my/attempts/ATTEMPT_ID/verify \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"

curl http://localhost:8000/api/v1/my/attempts/ATTEMPT_ID/verification-runs \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"

curl http://localhost:8000/api/v1/my/verification-runs/RUN_ID \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
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
