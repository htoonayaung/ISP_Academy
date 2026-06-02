# Security Rules

## Security Position

This platform is a lab-only training system. It must not become a production network automation platform during the MVP.

The most important rule:

```text
Users can operate only on lab-owned nodes inside lab-owned Containerlab instances.
```

## Lab-Only Boundary

Rules:

- No production network integration.
- No arbitrary SSH target IP input.
- No external network attachment in generated labs.
- No direct access to host network devices.
- All lab commands target nodes recorded in the student's `LabInstance`.
- All lab files stay inside configured `LAB_ROOT`.
- Student cannot select Docker image, host mount, privileged mode, or host path.

## Containerlab Safety

Rules:

- Do not use `shell=True`.
- Use subprocess argument lists.
- Sanitize lab names.
- Sanitize file paths.
- Resolve paths and verify they are inside `LAB_ROOT`.
- Do not allow host mounts from user input.
- Do not allow arbitrary Docker images.
- Do not allow privileged containers unless explicitly enabled by Admin configuration.
- Set command timeouts.
- Limit stdout/stderr capture size.
- Store logs safely.
- Do not return raw host stack traces to users.

## Template Safety

Lab templates must be validated before activation and before deployment.

Validation checks:

- YAML parses safely.
- Required Containerlab fields exist.
- Node names are sanitized.
- Interface names are valid.
- No host mount from user input.
- No external network attachment.
- No arbitrary image outside allowlist.
- No privileged container unless admin config permits.
- No paths outside template storage or lab instance storage.

## AI Safety

AI output is untrusted.

Rules:

- Do not auto-deploy AI-generated output.
- AI Lab Builder must return preview first.
- Backend must validate generated LabPlan.
- Approval is required before creating LabTemplate.
- Re-run validation at approval time.
- Do not send hidden solutions to AI provider.
- Do not allow AI to generate arbitrary shell commands.
- Do not allow unsupported node kinds, images, host mounts, external networks, or production IP targets.
- Do not allow privileged containers from AI-generated content.
- AI Lab Builder endpoints are Admin/Instructor only.
- Approval creates an inactive `LabTemplate` only.
- Approval must never create or start a `LabInstance`.
- AI provider credentials must come from environment variables and must not be logged.
- Real provider preview requests must require explicit user confirmation when configured.
- Real provider usage must enforce a simple per-user daily preview limit.
- Provider status APIs must return only redacted metadata such as host-only base URL and `has_api_key`.

MVP AI LabPlan constraints:

- Node count <= 6.
- Link count <= 10.
- Verification rule count <= 10.
- Allowed kinds: `frr`, `linux`.
- Allowed categories: `Linux`, `BGP`, `OSPF`.
- Supported protocols: static routing, OSPF single area, basic eBGP, basic iBGP.

## Authentication

Rules:

- Passwords are hashed with Argon2.
- Never store plaintext passwords.
- JWT secret comes from environment.
- Token expiration is configurable.
- Login failure does not reveal whether email exists.
- Inactive users cannot login.

## Authorization

Admin:

- Can manage users.
- Can reset user passwords without seeing plaintext passwords.
- Cannot deactivate the currently logged-in admin account.
- Can view all labs, tickets, attempts, audit logs.
- Can manage all templates and tickets.

Instructor:

- Can create/manage own lab templates.
- Can create/manage own tickets.
- Can view student attempts related to their content.
- Cannot view unrelated instructor private content unless allowed later.

Student:

- Can view active templates.
- Can view published tickets.
- Can create/control own labs.
- Can view only own attempts.
- Cannot view hidden solutions.
- Cannot view other students' command history.
- Cannot use AI Lab Builder v1.

## Safe Management Actions

Rules:

- Users are deactivated/reactivated, not hard-deleted from the management UI.
- Ticket `Delete` behavior is treated as archive in the MVP.
- Tickets can be unpublished back to `DRAFT` or archived; archived tickets are hidden from students.
- Lab templates are activated/deactivated; duplicate templates are created inactive by default.
- Verification rule delete is a soft deactivate so historical run data remains readable.
- Destroyed lab records remain as history. Lab cleanup must not remove files outside `LAB_ROOT`.
- Destructive or visibility-changing actions require UI confirmation and backend permission checks.

## Runtime Recovery Safety

Rules:

- Runtime admin APIs are Admin-only.
- Students and instructors cannot access global runtime cleanup.
- Runtime status must not require Docker socket access in the API container.
- Worker-only Containerlab/Docker execution boundary remains unchanged.
- Recovery uses typed confirmations.
- `mark_failed` changes DB state only and creates a lab event.
- `retry_destroy` queues the existing safe worker destroy task.
- `force_destroy_demo_only` is restricted to demo-prefixed labs.
- Demo cleanup removes only demo-prefixed destroyed or failed runtime artifacts when paths remain inside `LAB_ROOT`.
- No global wipe or unsafe hard delete is allowed.
- If cleanup is uncertain, skip and warn.
- Container names and lab paths must come from DB or worker inspection, not raw user input.

## Topology Viewer Safety

Rules:

- Topology parsing uses `yaml.safe_load` only.
- Topology parsing never executes YAML or shell commands.
- Topology APIs do not require Docker socket or Containerlab access.
- Students can view only active template topology and their own lab topology.
- Students cannot access AI Lab Builder preview topology.
- Do not expose secrets or host file paths in topology responses.
- Container names are hidden from students.
- Topology diagrams are read-only; no drag/drop editor, console, web terminal, SSH runner, or config apply exists in this phase.

## Router Console Safety

Rules:

- Console APIs are lab-node scoped.
- The target node must belong to the requested `LabInstance`.
- The lab must be `RUNNING`.
- Students can access only their own lab nodes.
- Users never pass container names directly.
- Container names come from DB `LabNode` records only.
- API and frontend must not mount Docker socket.
- Only `celery_worker` executes `docker exec`.
- `subprocess.run` must use argument lists and no `shell=True`.
- Command policy blocks shell escapes, pipes, redirects, host paths, package managers, Docker, Containerlab, and host shell commands.
- No SSH login, PTY, full web terminal, host shell, or backend shell exposure exists in this phase.

## Hidden Solution Protection

Rules:

- `hidden_solution` must never be included in student API responses.
- `hidden_solution` must never be sent to AI Mentor.
- Tests must prove hidden solution is not leaked.
- Logs must not accidentally serialize full ticket objects into student-visible output.

## Verification Safety

Rules:

- Verification runs only against nodes inside the student's lab.
- Commands come from instructor-created verification rules.
- Student cannot submit arbitrary verification commands.
- Command timeout is required.
- Output length limit is required.
- Results are stored with safe redaction where needed.

## Audit Events

Audit these actions:

- Login success/failure.
- User creation/update/deactivation.
- Lab template creation/update/delete/validation.
- Lab start/stop/destroy.
- Ticket publish/archive.
- Verification run.
- AI Lab Builder preview/approval.
- AI Mentor request.
- Permission denied events for sensitive resources.

## Secret Management

Rules:

- Never hardcode secrets.
- Use environment variables and `.env.example` without real secret values.
- Do not commit real provider API keys.
- Do not log tokens, password hashes, or AI provider credentials.
- Do not paste secrets into chat, documentation, screenshots, shell history, or issue trackers.
- `deployments/env/backend.env` must stay ignored by Git.
- Backup dumps and SQL files must stay ignored by Git.
- Rotate admin passwords, demo passwords, JWT secrets, AI API keys, and GitHub tokens using the password rotation guide.
- AI API keys must remain backend-only and must never be returned by frontend or provider status APIs.

## Docker Compose Boundary

Rules:

- Backend must not mount `/var/run/docker.sock`.
- Backend must not run privileged.
- Backend must not use host network or host PID.
- Frontend must not mount `/var/run/docker.sock`.
- Frontend must not run privileged.
- Frontend must not use host network or host PID.
- Only `celery_worker` may have Docker/Containerlab host access in the MVP.
- `celery_worker` privileged access is MVP-only technical debt.
- PostgreSQL and Redis should bind to loopback unless an explicit internal network change is approved.
