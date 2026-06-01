# AI-Powered ISP Academy MVP

Phase 8 adds AI Lab Builder v1 on top of the current MVP: backend, lab engine, verification engine, minimal frontend, documentation, backup guidance, and admin/instructor-only AI preview approval.

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
- AI Lab Builder v1 preview, validation, and approval into inactive lab templates.
- Demo, admin, instructor, student, troubleshooting, and backup/restore docs.

Not included yet:

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
3. Admin or instructor generates an AI Lab Builder preview, or manually creates a lab template.
4. Review AI validation, approve the preview into an inactive lab template, then activate/edit the template if needed.
5. Validate the template.
6. Create a ticket from the template.
7. Add hints and instructor-only hidden solution.
8. Publish the ticket.
9. Create verification rules.
10. Student logs in.
11. Student opens the published ticket.
12. Student starts an attempt.
13. Student opens the linked lab.
14. Student starts the lab and waits for `RUNNING`.
15. Student runs verification.
16. Student opens the verification run result.
17. Student destroys the lab.

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

## AI Lab Builder V1

AI Lab Builder is disabled by default. Enable it only when an AI provider is configured, or use the `mock` provider for local/demo testing:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=mock
AI_API_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_TOKENS=4000
```

Open the frontend as Admin or Instructor:

- `http://10.0.44.2:3000/ai-lab-builder`
- `http://10.0.44.2:3000/ai-lab-builder/previews`

Phase 8 behavior:

- AI output is stored only as a preview first.
- Backend validation is mandatory.
- Approval creates an inactive `LabTemplate`.
- Approval does not create, start, inspect, stop, or destroy a lab.
- Students cannot access AI Lab Builder routes or menus.

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
- AI Lab Builder v1 has a simple OpenAI-compatible provider abstraction and mock provider only.
- AI-generated FRR startup configs are previewed, not automatically wired into full lab deployment.
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
- [AI Lab Builder Guide](docs/AiLabBuilderGuide.md)
- [Architecture](docs/Architecture.md)
- [Security Rules](docs/SecurityRules.md)
