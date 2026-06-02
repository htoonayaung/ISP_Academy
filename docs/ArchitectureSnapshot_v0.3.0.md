# Architecture Snapshot v0.3.0

This snapshot documents the current demo-ready MVP architecture for `v0.3.0-demo-ready`.

## Component Diagram

```text
Browser
  |
  | HTTP
  v
Frontend container
  |
  | REST API with JWT
  v
Backend API container
  |        |
  |        +--> PostgreSQL
  |        |
  |        +--> Redis
  |
  +--> Celery task queue via Redis
             |
             v
       Celery worker container
             |
             | controlled MVP host access
             v
       Docker + Containerlab on single server
             |
             v
       Lab files under /opt/isp-academy/lab-storage
```

## Frontend

- React.
- TypeScript.
- TailwindCSS.
- Runs as a Docker Compose service on port `3000`.
- Uses `VITE_API_BASE_URL` to call the backend.
- Stores JWT in `localStorage` as an MVP tradeoff.
- Has no Docker socket access.
- Has no Containerlab access.

## Backend API

- FastAPI.
- Async SQLAlchemy.
- Alembic migrations.
- Pydantic settings.
- Runs as a Docker Compose service on port `8000`.
- Provides REST APIs for auth, users, lab templates, labs, tickets, verification, AI preview, and demo setup.
- Does not mount `/var/run/docker.sock`.
- Does not run privileged.
- Does not use host network or host PID.
- Does not execute Containerlab directly.

## PostgreSQL

- Stores application state.
- Exposed only on `127.0.0.1:5432` from Docker Compose.
- Current major business data lives here.

## Redis

- Used for Celery broker and result backend.
- Exposed only on `127.0.0.1:6379` from Docker Compose.

## Celery Worker

- Executes lab lifecycle and verification tasks.
- Only service with Containerlab/Docker host access.
- MVP-only host access:
  - privileged mode
  - host network
  - host PID
  - `/var/run/docker.sock`
  - `containerlab` binary mount
  - `docker` binary mount

This boundary is acceptable for the current single-server MVP but must be reduced before broader production use.

## Containerlab Host Access

Containerlab operations are worker-only:

- create/start lab
- inspect lab
- stop lab
- destroy lab
- verification command execution against lab-owned nodes only

The API container never executes Containerlab and never receives arbitrary SSH targets from users.

## Lab Storage Path

```text
/opt/isp-academy/lab-storage
```

Generated lab files must remain inside lab-specific directories under this path. Path traversal and cleanup outside `LAB_ROOT` are not allowed.

## Security Boundary

- API: no Docker socket, no privileged mode, no host network, no host PID.
- Frontend: no Docker socket, no privileged mode, no host network, no host PID.
- Worker: controlled MVP-only Docker and Containerlab access.
- Students cannot access Demo Setup.
- Students cannot access AI Lab Builder.
- Students cannot see hidden ticket solutions.
- AI output is untrusted.
- AI Lab Builder has no auto-deploy path.
- No production network integration.
- Lab commands target lab-owned nodes only.

## Current Major Models

- `users`
- `lab_templates`
- `lab_instances`
- `lab_nodes`
- `lab_events`
- `tickets`
- `ticket_attempts`
- `verification_rules`
- `verification_runs`
- `verification_results`
- `ai_lab_builder_previews`

## Deployment Shape

- Single organization.
- Single server.
- Docker Compose.
- Containerlab-only lab engine.
- MVP target: 20 to 50 users, 5 to 10 concurrent students, 5 to 20 running labs.
