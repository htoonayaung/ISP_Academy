# AI-Powered ISP Academy MVP

The current MVP is demo-ready and Phase 11B topology viewing is in place for safer internal use and controlled external demos.

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
- AI Lab Builder v1 preview, validation, natural-language prompt robustness, and approval into inactive lab templates.
- Admin-only Demo Setup Wizard for repeatable MVP demos.
- Phase 9B polished browser demo flow for the student ticket, lab, verification, and destroy journey.
- Phase 9C management CRUD and operational cleanup.
- Phase 10 production hardening scripts and operations documentation.
- Phase 11A Lab Runtime Cleanup and Admin Operations.
- Phase 11B read-only Topology Diagram Viewer.
- Phase 11C Router Console Access MVP for lab-owned running nodes.
- Demo rehearsal and release freeze documentation for `v0.3.0-demo-ready`.
- Demo, admin, instructor, student, troubleshooting, and backup/restore docs.

Not included yet:

- AI Mentor.
- Web terminal.
- Certification, leaderboard, analytics.
- Advanced topology editor.

## URLs

- Frontend: `http://10.0.44.2:3000`
- Backend API: `http://10.0.44.2:8000`
- Swagger: `http://10.0.44.2:8000/docs`

## Current Demo-Ready Release

Recommended tag:

```text
v0.3.0-demo-ready
```

Release docs:

- [Demo Rehearsal Checklist](docs/DemoRehearsalChecklist.md)
- [Release Notes v0.3.0](docs/ReleaseNotes_v0.3.0.md)
- [Architecture Snapshot v0.3.0](docs/ArchitectureSnapshot_v0.3.0.md)
- [Release Checklist](docs/ReleaseChecklist.md)

Quick demo path:

```text
Admin Demo Setup -> Student Demo Flow -> AI Lab Builder Preview
```

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

## Manual Lab Template Demo Flow

1. Admin logs in.
2. Admin creates instructor and student accounts.
3. Admin or instructor creates a lab template.
4. Admin or instructor validates the template.
5. Admin or instructor creates a ticket from the template.
6. Admin or instructor adds hints and instructor-only hidden solution.
7. Admin or instructor publishes the ticket.
8. Admin or instructor creates verification rules.
9. Student logs in.
10. Student opens the published ticket.
11. Student starts an attempt.
12. Student opens the linked lab.
13. Student starts the lab and waits for `RUNNING`.
14. Student runs verification.
15. Student opens the verification run result.
16. Student destroys the lab.

## AI Lab Builder Demo Flow

1. Admin or instructor opens AI Lab Builder.
2. Admin or instructor describes the lab in plain English and generates a preview.
3. Admin or instructor reviews validation status, generated Containerlab YAML, generated configs, and verification rule previews.
4. Admin or instructor approves the preview.
5. Approval creates an inactive `LabTemplate`.
6. Admin or instructor edits or activates the template if needed.
7. Admin or instructor validates the template.
8. Continue with the manual ticket, verification rule, student attempt, lab start, verification, and lab destroy flow.

Full checklist: [docs/DemoGuide.md](docs/DemoGuide.md)
Release rehearsal checklist: [docs/DemoRehearsalChecklist.md](docs/DemoRehearsalChecklist.md)

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

## Phase 10 Production Hardening

Phase 10 adds operational checks, security smoke checks, backup verification, reverse proxy preparation, and password rotation guidance without adding new product features.

Run:

```bash
cd /opt/isp-academy
bash scripts/check_system_health.sh
bash scripts/security_smoke_check.sh
bash scripts/check_lab_runtime_state.sh
```

Backup verification:

```bash
bash scripts/backup_database.sh
latest="$(ls -t backups/*.dump | head -n 1)"
bash scripts/verify_backup_file.sh "$latest"
```

Phase 10 docs:

- [Operations Checklist](docs/OperationsChecklist.md)
- [Reverse Proxy Guide](docs/ReverseProxyGuide.md)
- [Password Rotation Guide](docs/PasswordRotationGuide.md)
- [Backup And Restore](docs/BackupRestore.md)

## Phase 11A Lab Runtime Operations

Admins can open `http://10.0.44.2:3000/admin/runtime` to inspect and safely recover runtime lab problems.

Runtime Ops includes:

- Lab status counts by lifecycle state.
- Stuck `STARTING`, `STOPPING`, and `DESTROYING` candidates.
- Demo lab summary.
- Orphan runtime directory reporting.
- Recent lab lifecycle and recovery events.
- Confirmation-protected recovery actions.

Recovery actions:

- `Refresh` queues worker-side inspection and does not delete anything.
- `Mark failed` changes DB state only for stuck transient labs.
- `Retry destroy` queues the existing safe destroy task.
- `Force destroy demo` is restricted to demo-prefixed labs and requires `RECOVER_LAB`.
- `Cleanup demo runtime` is restricted to demo-prefixed destroyed or failed runtime artifacts and requires `CLEANUP_DEMO_RUNTIME`.

Security boundary:

- Backend API still has no Docker socket and does not execute Containerlab.
- Frontend has no Docker socket.
- Only `celery_worker` executes Containerlab/Docker operations.
- Runtime cleanup skips uncertain or non-demo active resources.

## Phase 11B Topology Diagram Viewer

Lab topology diagrams are read-only visual aids for understanding labs before and after deployment.

Supported topology sources:

- LabTemplate Containerlab YAML.
- LabInstance topology with cached runtime node status and management IP when available.
- AI Lab Builder preview topology before approval.

Behavior:

- Clicking a node opens a detail panel.
- The diagram is read-only.
- There is no drag/drop editing.
- There is no router console, SSH runner, or web terminal in this phase.
- Students can see only topology for active templates and their own labs.
- Students cannot access AI Lab Builder preview topology.

## Phase 11C Router Console Access MVP

Running lab pages now include a lab-node-scoped console panel for supported nodes.

Supported:

- FRR nodes through worker-mediated `vtysh`.
- Limited Linux read-only commands when available.
- Quick commands such as `show ip route`, `show ip ospf neighbor`, `show bgp summary`, and `show running-config`.

Security boundary:

- Commands run only inside the selected lab node container.
- Users cannot pass container names.
- Students can use only their own running lab nodes.
- Backend and frontend still have no Docker socket.
- Docker exec happens only in `celery_worker`.
- No SSH exposure, full web terminal, PTY, host shell, Docker command access, or Containerlab command access is added.

## AI Lab Builder V1

AI Lab Builder v1 is included in Phase 8. Phase 8.6 lets users type plain-language requests instead of JSON. The backend internally interprets common requests into a complete LabPlan, validates it, and only then creates a preview.

Supported simple prompts:

- Two-router FRR OSPF area 0 lab.
- Two-router FRR eBGP lab.
- Basic Linux uname verification lab.
- Simple static routing lab.

The current MVP demo server can use the `mock` provider:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=mock
AI_API_BASE_URL=
AI_API_KEY=
AI_MODEL=mock
AI_REQUEST_TIMEOUT_SECONDS=60
AI_MAX_TOKENS=4000
AI_DAILY_PREVIEW_LIMIT_PER_USER=20
AI_PROVIDER_TEST_ENABLED=false
AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true
```

For real provider testing, configure the provider only in `deployments/env/backend.env`. Do not put API keys in frontend files, Git, or chat.

Recommended real provider trial order:

1. Gemini free tier.
2. OpenRouter free model.
3. Groq free tier.
4. Paid provider only after quality is confirmed.

Open the frontend as Admin or Instructor:

- `http://10.0.44.2:3000/ai-lab-builder`
- `http://10.0.44.2:3000/ai-lab-builder/previews`

Phase 8 behavior:

- AI output is stored only as a preview first.
- AI output is untrusted.
- Users should describe labs in plain language, not write JSON.
- The backend uses deterministic safe scaffolds for common OSPF, BGP, Linux, and static routing prompts when provider output is incomplete.
- Backend validation is mandatory.
- Approval creates an inactive `LabTemplate`.
- There is no auto-deploy.
- Approval does not create, start, inspect, stop, or destroy a lab.
- Real provider usage requires explicit confirmation when configured.
- Students cannot access AI Lab Builder routes or menus.

## Phase 9A Demo Setup Wizard

Admins can open `http://10.0.44.2:3000/admin/demo-setup` to create repeatable demo data.

The wizard creates demo-prefixed data only:

- `demo_instructor`
- `demo_student`
- `Demo Basic Linux Lab`
- `Demo Linux Verification Ticket`
- `Demo uname verification`

Setup is idempotent. It creates missing demo records only and does not start labs, run AI, create LabInstances, or execute Containerlab.

Environment:

```env
DEMO_SETUP_ENABLED=true
DEMO_INSTRUCTOR_USERNAME=demo_instructor
DEMO_INSTRUCTOR_PASSWORD=
DEMO_STUDENT_USERNAME=demo_student
DEMO_STUDENT_PASSWORD=
```

If demo passwords are empty, setup generates secure passwords and returns them once in the setup response. Do not use demo passwords in production.

API:

```bash
GET  /api/v1/admin/demo/status
POST /api/v1/admin/demo/setup
POST /api/v1/admin/demo/reset
```

Reset requires `RESET_DEMO_DATA` confirmation and targets demo-prefixed data only.

## Phase 9B Browser Demo Flow

Use this flow for live demos without Swagger or curl:

1. Admin logs in and opens `Demo Setup`.
2. Confirm the page shows `DEMO READY`.
3. Copy the student username and go to login.
4. Log in as `demo_student`.
5. Dashboard shows the recommended `Start Demo Ticket` card.
6. Open the demo ticket and start an attempt.
7. Attempt detail shows a five-step guide.
8. Open the linked lab, start it, and wait for `RUNNING`.
9. Return to the attempt and run verification.
10. Confirm the verification result shows `PASSED`.
11. Open the lab and destroy it.

Expected browser behavior:

- Student menu shows only Dashboard, Tickets, My Attempts, and My Labs.
- Student never sees Demo Setup, AI Lab Builder, or hidden solution text.
- Lab lifecycle buttons are disabled during STARTING, STOPPING, and DESTROYING.
- Verification is disabled until the linked lab is RUNNING.

## Phase 9C Management Cleanup

Phase 9C completes safe operational actions in the management UI:

- Users: edit, deactivate, reactivate, and admin-only reset password.
- Lab templates: edit, validate, activate, deactivate, and duplicate as inactive copy.
- Tickets: edit, publish, unpublish to draft, and archive.
- Verification rules: create, edit, deactivate, and reactivate.
- Labs: filter by state, refresh, start, stop, and destroy with confirmation.
- Attempts: admin sees all attempts, instructors see attempts for their own tickets, students see only their own attempts.
- AI previews: view, approve valid previews, reject, and delete when allowed.

Safe-delete behavior:

- Users are deactivated, not hard-deleted.
- Templates are deactivated when they should not be used for new tickets.
- Ticket delete behavior is archive-oriented in the MVP.
- Verification rule delete is a soft deactivate so old verification history remains readable.
- Destroyed lab records remain visible as history.

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

Use the real filename from the `backups/` directory:

```bash
bash scripts/restore_database.sh backups/<filename>.dump
```

Backup artifacts matching `backups/*.dump` and `backups/*.sql` are gitignored.

See [docs/BackupRestore.md](docs/BackupRestore.md).

## Git Tag Suggestion

After verifying the demo:

```bash
cd /opt/isp-academy
git tag -a v0.3.0-demo-ready -m "Demo-ready MVP release"
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
- HTTP-only unless the reverse proxy guide is implemented.
- `celery_worker` has privileged host access for Containerlab.
- AI Lab Builder v1 exists with mock provider and OpenAI-compatible provider abstraction. Real AI provider testing is pending.
- AI-generated FRR startup configs are previewed, not automatically wired into full lab deployment.
- Runtime Ops is Phase 11A-level only; orphan detection is conservative and cleanup is demo-restricted.
- Topology viewer is read-only and uses a simple automatic layout; advanced topology editing is not implemented.
- Router console is command-execution MVP only, not an interactive PTY/WebSocket terminal.
- No AI Mentor yet.
- Production hardening is Phase 10-level only; full HA, SSO, observability, and isolation are not implemented.
- No automated frontend test suite yet.
- No high availability.
- No multi-tenant production isolation.
- No topology editor yet.
- No web terminal yet.

## Future UX Direction

A NetPilot-inspired three-panel layout is a future design direction only:

- Left panel: navigation and labs list.
- Center panel: AI prompt/workspace.
- Right panel: lab context, topology, infra status, and node details.

This is not implemented in Phase 10 and is not intended as an exact copy.

## Documentation

- [Demo Guide](docs/DemoGuide.md)
- [Admin Guide](docs/AdminGuide.md)
- [Instructor Guide](docs/InstructorGuide.md)
- [Student Guide](docs/StudentGuide.md)
- [Troubleshooting](docs/Troubleshooting.md)
- [Backup And Restore](docs/BackupRestore.md)
- [Operations Checklist](docs/OperationsChecklist.md)
- [Reverse Proxy Guide](docs/ReverseProxyGuide.md)
- [Password Rotation Guide](docs/PasswordRotationGuide.md)
- [AI Lab Builder Guide](docs/AiLabBuilderGuide.md)
- [Architecture](docs/Architecture.md)
- [Security Rules](docs/SecurityRules.md)
