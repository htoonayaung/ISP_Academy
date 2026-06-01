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
