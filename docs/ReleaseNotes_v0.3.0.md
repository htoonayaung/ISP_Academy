# Release Notes v0.3.0

## Release Name

ISP Academy MVP Demo Release

## Version Suggestion

`v0.3.0-demo-ready`

## Included Features

- FastAPI backend foundation.
- PostgreSQL, Redis, Celery, Alembic, and pytest.
- JWT authentication with Argon2 password hashing.
- Roles: `ADMIN`, `INSTRUCTOR`, `STUDENT`.
- Admin user management.
- Lab template CRUD with Containerlab YAML safety validation.
- Containerlab-only lab lifecycle through Celery worker execution.
- Lab instances, lab nodes, and lab events.
- Ticket system with hidden solution protection.
- Student ticket attempts.
- Verification rules, verification runs, and per-rule results.
- React, TypeScript, TailwindCSS frontend.
- Role-aware navigation.
- Admin-only Demo Setup Wizard.
- Polished browser student demo flow.
- AI Lab Builder v1 with mock provider and provider abstraction.
- AI preview approval into inactive LabTemplate.
- Backup and restore helper scripts.
- Demo, admin, instructor, student, troubleshooting, AI, and release docs.

## Excluded Features

- AI Mentor.
- Web terminal.
- SSH command runner.
- Advanced topology editor.
- Certification.
- XP, badges, or leaderboard.
- Advanced analytics.
- Multi-tenancy.
- Production SSO.
- Kubernetes.
- High availability.
- Auto-deploy from AI prompt.

## Known Technical Debt

- JWT is stored in browser `localStorage`.
- HTTP is used unless HTTPS is configured externally.
- `celery_worker` has privileged host access for Containerlab.
- `celery_worker` mounts `/var/run/docker.sock`.
- `celery_worker` uses host network and host PID mode.
- AI Lab Builder real provider quality testing is pending.
- AI-generated startup configs are previewed but not fully wired into every lab deployment path.
- No automated frontend test suite yet.
- No production-grade observability or audit trail yet.

## Security Boundary

- Frontend container has no Docker socket access.
- API container has no Docker socket access.
- API container must not execute Containerlab.
- Containerlab operations run only through `celery_worker`.
- Students cannot access Demo Setup.
- Students cannot access AI Lab Builder.
- Students cannot see `hidden_solution`.
- AI output is untrusted.
- Backend validation is mandatory before AI-generated templates can be approved.
- AI preview approval creates an inactive LabTemplate and does not deploy a lab.
- No real AI keys, JWT secrets, or runtime secrets should be committed.

## Demo Accounts Note

Demo accounts are for internal testing and presentation rehearsal only.

- Do not publish real demo passwords.
- Change demo passwords before any public demo.
- Rotate the admin password if it was shared during rehearsal.
- Keep demo credentials out of Git, docs, screenshots, and chat.

## Backup And Restore Note

Create a database backup before tagging or presenting:

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
```

Restore only to the intended environment:

```bash
cd /opt/isp-academy
bash scripts/restore_database.sh backups/<filename>.dump
```

Backups under `backups/*.dump` and `backups/*.sql` are gitignored.

## Upgrade And Deployment Note

Recommended deployment command:

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml up -d --build
docker compose -f deployments/docker-compose.yml exec backend alembic upgrade head
```

Verify after deployment:

```bash
docker compose -f deployments/docker-compose.yml ps
curl http://10.0.44.2:8000/ready
curl -I http://10.0.44.2:3000
```

## Rollback Note

Rollback plan:

1. Confirm the target Git commit or release tag.
2. Stop active demo labs from the UI.
3. Back up the current database.
4. Check out the previous commit or tag.
5. Rebuild containers.
6. Restore database only if schema/data rollback is required.

Example:

```bash
cd /opt/isp-academy
git checkout <previous-commit-or-tag>
docker compose -f deployments/docker-compose.yml up -d --build
```

Avoid restoring a database dump unless you have confirmed the target environment and accepted data loss from newer changes.
