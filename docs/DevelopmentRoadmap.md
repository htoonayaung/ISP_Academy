# Development Roadmap

## Guiding Principles

- Build one phase at a time.
- Do not write implementation code for a later phase before the current phase is reviewed and accepted.
- Do not generate business logic files early as empty placeholders.
- Do not create future-phase modules until their phase begins.
- Keep the MVP single-server and Containerlab-only.
- Keep security review part of every phase.

## Phase 0: MVP Architecture

Goal:

- Design architecture only.
- Produce documentation.
- Do not generate implementation code.

Deliverables:

- `docs/Architecture.md`
- `docs/MVP_Features.md`
- `docs/FolderStructure.md`
- `docs/DatabaseModel.md`
- `docs/API_List.md`
- `docs/LabLifecycle.md`
- `docs/SecurityRules.md`
- `docs/DevelopmentRoadmap.md`

Approval checklist:

- MVP scope is clear and excludes enterprise features.
- Phase boundaries are clear.
- Phase 1 is foundation-only.
- Phase 1 API list contains only `GET /health`, `GET /ready`, and `GET /api/v1/system/info`.
- Phase 1 folder structure does not include auth, users, labs, tickets, verification, AI, mentor, admin, or instructor business modules.
- Database entities are assigned to implementation phases.
- API endpoints are assigned to implementation phases.
- API container has no direct Containerlab or Docker socket access.
- Only the Celery worker executes Containerlab operations.
- Worker host access is controlled and limited.
- Lab-only security rules are documented.
- Hidden ticket solution protection is documented.
- AI preview and approval safety is documented.

Exit criteria:

- User approves Phase 0 docs.
- Phase 1 can begin with backend foundation only.

## Phase 1: Backend Foundation

Goal:

- Create a clean FastAPI backend foundation with no business logic.

Build:

- FastAPI app setup.
- Settings/config.
- Structured logging.
- Health endpoint: `GET /health`.
- Readiness endpoint: `GET /ready`.
- System info endpoint: `GET /api/v1/system/info`.
- PostgreSQL async connection.
- SQLAlchemy base.
- Alembic setup.
- Redis connection.
- Celery app setup.
- Dockerfile and Docker Compose.
- pytest setup.

Do not build:

- User model.
- Authentication.
- Role-based permissions.
- Lab templates.
- Lab instances.
- Containerlab adapter.
- Tickets.
- Verification.
- AI Lab Builder.
- AI Mentor.
- Admin/instructor dashboards.
- Frontend.

Exit criteria:

- Backend, PostgreSQL, Redis, and Celery run with Docker Compose.
- Tests pass.
- No business logic modules are generated early.

## Phase 2: Simple Authentication

Goal:

- Add users, login, JWT, and role-based access.

Build:

- User model.
- Argon2 password hashing.
- Login endpoint.
- Current user endpoint.
- Admin user management.
- Role dependencies.
- Initial admin seed command.
- Tests for auth and permissions.

Exit criteria:

- Admin, Instructor, Student roles work.
- Inactive users cannot login.
- Password hashes are never returned.

## Phase 3: Lab Template System

Goal:

- Manage safe Containerlab templates without starting labs.

Build:

- LabTemplate model and APIs.
- YAML syntax validation.
- Metadata validation.
- Safety validation for mounts, images, paths, and privileged mode.
- Role-based access.
- Sample templates.

Exit criteria:

- Admin/Instructor can manage templates.
- Students can view active templates.
- No template execution happens yet.

## Phase 4: Containerlab Lab Engine

Goal:

- Create and control lab instances from templates.

Build:

- LabInstance, LabNode, LabEvent.
- LabService.
- ContainerlabAdapter.
- Celery lab tasks.
- Lab directory manager.
- State manager.
- Status parser.

Exit criteria:

- Student can create/start/stop/destroy own labs.
- FastAPI never directly runs Containerlab.
- API container has no Docker socket or Containerlab access.
- Only worker executes Containerlab through adapter.
- All runtime files stay inside `LAB_ROOT`.

## Phase 5: Basic Ticket System

Goal:

- Add ticket-based learning flow.

Build:

- Ticket model.
- TicketAttempt model.
- Publish/archive workflow.
- Student start attempt flow.
- Hidden solution protection.

Exit criteria:

- Student can start a published ticket.
- Starting ticket creates linked lab instance.
- Hidden solution never leaks to student.

## Phase 6: Basic Verification Engine

Goal:

- Verify student labs against instructor-defined rules.

Build:

- VerificationRule.
- VerificationRun.
- VerificationResult.
- Celery verification tasks.
- Assertions: contains, not contains, equals, exit code zero, BGP neighbor established, route exists.

Exit criteria:

- Student can run verification on own attempt.
- Verification targets only lab-owned nodes.
- Results are stored and visible.

## Phase 7: Minimal Frontend

Goal:

- Build usable React UI for existing backend.

Build:

- Login.
- Dashboard.
- Lab templates.
- My labs.
- Lab detail.
- Tickets.
- Ticket detail.
- My attempts.
- Verification result.
- Basic Admin users page.

Exit criteria:

- Core MVP flow works through browser.

## Phase 8: AI Lab Builder V1

Goal:

- Generate safe lab previews from instructor/admin prompts.

Build:

- AI provider abstraction.
- LabPlan schema.
- LabPlan validator.
- Containerlab YAML generator.
- FRR/Linux config generator.
- Verification rule generator.
- Preview and approve APIs.

Exit criteria:

- AI output is validated.
- Approval creates LabTemplate.
- No auto-deploy without approval.

## Phase 9: Prompt-To-Lab Preview UI

Goal:

- Add frontend UI for AI Lab Builder preview and approval.

Build:

- Prompt input.
- LabPlan preview.
- Containerlab YAML preview.
- Config preview.
- Verification preview.
- Validation warnings.
- Approve/reject/regenerate actions.

Exit criteria:

- Instructor/Admin can approve generated template from UI.
- Student cannot access AI Lab Builder.

## Phase 10: Approval-Based Auto Deploy

Goal:

- Allow approved AI lab template to optionally start a lab.

Build:

- Approval with optional lab start.
- Metadata storage.
- Validation re-checks.
- UI status flow.

Exit criteria:

- Only approved and validated AI output can deploy.

## Phase 11: AI Mentor Lite

Goal:

- Provide safe student hints.

Build:

- Mentor endpoint.
- Message storage.
- Rate limiting.
- Audit logging.
- Hidden solution exclusion tests.

Exit criteria:

- Student gets hints without final solution leakage.

## Phase 12: Instructor/Admin Features

Goal:

- Add operational dashboards and progress views.

Build:

- Instructor overview.
- Admin overview.
- Student attempt list.
- Ticket result summary.
- Lab usage summary.
- Audit log viewer.

Exit criteria:

- Instructor/Admin can monitor MVP pilot.

## Phase 13: MVP Hardening

Goal:

- Prepare for internal pilot.

Build:

- Better errors.
- Request IDs.
- Rate limiting.
- CORS.
- Secure headers where practical.
- Backup/restore docs.
- Lab cleanup tasks.
- Production Docker Compose profile.
- User guides.

Exit criteria:

- MVP is ready for controlled internal testing.

## Phase 14: Future Enterprise Upgrade Plan

Goal:

- Plan future expansion after MVP success.

Plan:

- Multi-tenancy.
- Organizations/departments/teams.
- Advanced RBAC.
- TextFSM/Genie verification.
- Versioning.
- Certification.
- Analytics.
- Observability.
- Multi-host scheduling.
- Resource quotas.

Exit criteria:

- Future roadmap is documented without changing MVP implementation.

