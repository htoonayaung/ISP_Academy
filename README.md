# AI-Powered ISP Academy MVP

Phase 7.5 packages the current MVP for demos: backend, lab engine, verification engine, minimal frontend, documentation, and backup guidance.

## Current MVP Status

Completed:

- FastAPI backend foundation.
- PostgreSQL, Redis, Celery, Alembic, and pytest.
- Authentication with JWT access tokens and Argon2 password hashing.
- Roles: `ADMIN`, `INSTRUCTOR`, `STUDENT`.
- Lab template CRUD and safety validation.
- Containerlab-only lab lifecycle through worker-only execution.
- Ticket system with hidden solution protection.
- Basic verification rules and verification runs.
- Minimal React, TypeScript, TailwindCSS frontend.
- Role-aware navigation and demo-ready browser workflow.
- Demo, admin, instructor, student, troubleshooting, and backup/restore docs.

Not included yet:

- AI Lab Builder.
- AI Mentor.
- Web terminal.
- Certification, leaderboard, or analytics.
- Kubernetes, HA, or multi-tenant enterprise features.

## URLs

- Frontend: `http://10.0.44.2:3000`
- Backend API: `http://10.0.44.2:8000`
- Swagger: `http://10.0.44.2:8000/docs`

## Quick Start

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml up -d --build
docker compose -f deployments/docker-compose.yml ps
```

Run migrations:

```bash
docker compose -f deployments/docker-compose.yml exec backend alembic upgrade head
```

Seed the initial admin:

```bash
docker compose -f deployments/docker-compose.yml exec backend python -m app.scripts.seed_admin
```

## Demo Flow

1. Admin logs in.
2. Admin creates instructor and student accounts.
3. Admin or instructor creates a lab template.
4. Validate the template.
5. Create a ticket from the template.
6. Add hints and instructor-only hidden solution.
7. Publish the ticket.
8. Create verification rules.
9. Student logs in.
10. Student opens the published ticket.
11. Student starts an attempt.
12. Student opens the linked lab.
13. Student starts the lab and waits for `RUNNING`.
14. Student runs verification.
15. Student opens the verification run result.
16. Student destroys the lab.

Full checklist: [docs/DemoGuide.md](docs/DemoGuide.md)

## Test Commands

Backend tests:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml run --rm backend pytest
```

Frontend build:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml build frontend
```

Readiness:

```bash
curl http://10.0.44.2:8000/health
curl http://10.0.44.2:8000/ready
curl http://10.0.44.2:8000/api/v1/system/info
```

## Backup

Database backup:

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
```

Restore:

```bash
cd /opt/isp-academy
bash scripts/restore_database.sh backups/isp_academy_YYYYmmdd_HHMMSS.dump
```

See [docs/BackupRestore.md](docs/BackupRestore.md).

## Git Tag Suggestion

After verifying the demo:

```bash
cd /opt/isp-academy
git tag phase-7.5-demo-ready
```

Review staged files before pushing. Do not commit real secrets or real environment files.

## Security Boundary

The API container must not have Docker socket access, privileged mode, host network, host PID, or direct Containerlab execution.

Containerlab operations run only through `celery_worker`. For this single-server MVP, the worker has controlled host access because Containerlab requires Docker and host network visibility.

MVP-only worker technical debt:

- `celery_worker` has `/var/run/docker.sock`.
- `celery_worker` runs privileged.
- `celery_worker` uses host network and host PID mode.

Before broader deployment, replace this with a narrower lab executor boundary.

## Known Technical Debt

- JWT is stored in browser `localStorage`.
- HTTP is used unless HTTPS is configured externally.
- `celery_worker` has privileged host access for Containerlab.
- No AI Lab Builder yet.
- No AI Mentor yet.
- No production hardening yet.
- No automated frontend test suite yet.
- No web terminal yet.

## Documentation

- [Demo Guide](docs/DemoGuide.md)
- [Admin Guide](docs/AdminGuide.md)
- [Instructor Guide](docs/InstructorGuide.md)
- [Student Guide](docs/StudentGuide.md)
- [Troubleshooting](docs/Troubleshooting.md)
- [Backup And Restore](docs/BackupRestore.md)
- [Architecture](docs/Architecture.md)
- [Security Rules](docs/SecurityRules.md)
