# Folder Structure

## Purpose

This document separates the Phase 1 backend foundation structure from future-phase business modules.

Phase 1 must create only infrastructure and foundation files. It must not create lab, ticket, verification, AI, mentor, admin dashboard, or instructor dashboard business logic.

## Phase 1 Backend Foundation Structure

Phase 1 creates the minimum runnable FastAPI backend foundation:

```text
isp-academy/
  backend/
    app/
      __init__.py
      main.py
      api/
        __init__.py
        deps.py
        router.py
        v1/
          __init__.py
          system.py
      core/
        __init__.py
        config.py
        logging.py
      db/
        __init__.py
        base.py
        session.py
      workers/
        __init__.py
        celery_app.py
      tests/
        __init__.py
        test_health.py
        test_ready.py
        test_system_info.py
    alembic/
      env.py
      script.py.mako
      versions/
    Dockerfile
    pyproject.toml
    requirements.txt

  deployments/
    docker-compose.yml
    env/
      backend.env.example

  docs/
    Architecture.md
    MVP_Features.md
    FolderStructure.md
    DatabaseModel.md
    API_List.md
    LabLifecycle.md
    SecurityRules.md
    DevelopmentRoadmap.md

  README.md
```

## Phase 1 File Rules

Phase 1 may include:

- FastAPI app setup.
- Settings/config loading.
- Structured logging setup.
- Health endpoint.
- Readiness endpoint.
- System info endpoint.
- PostgreSQL async connection setup.
- SQLAlchemy base setup.
- Alembic setup.
- Redis connection setup.
- Celery app setup.
- Dockerfile.
- Docker Compose for backend, PostgreSQL, Redis, Celery worker.
- pytest setup.

Phase 1 must not include:

- Authentication business logic.
- User model or user APIs.
- Lab template model or APIs.
- Lab instance model or APIs.
- Containerlab adapter.
- Lab directory manager.
- Ticket model or APIs.
- Verification model or APIs.
- AI provider abstraction.
- AI Lab Builder modules.
- AI Mentor modules.
- Admin dashboard modules.
- Instructor dashboard modules.
- Frontend implementation.

## Future Backend Structure

The following structure is planned across later phases. These files should be created only when their phase begins.

```text
backend/
  app/
    api/
      v1/
        auth.py                  # Phase 2
        users.py                 # Phase 2
        lab_templates.py         # Phase 3
        labs.py                  # Phase 4
        tickets.py               # Phase 5
        verification.py          # Phase 6
        ai_lab_builder.py        # Phase 8
        mentor.py                # Phase 11
        admin.py                 # Phase 12
        instructor.py            # Phase 12
    core/
      security.py                # Phase 2
      permissions.py             # Phase 2
      rate_limit.py              # Phase 11 or Phase 13
    models/
      user.py                    # Phase 2
      lab_template.py            # Phase 3
      lab_instance.py            # Phase 4
      ticket.py                  # Phase 5
      verification.py            # Phase 6
      command_history.py         # Later
      ai.py                      # Phase 8 and Phase 11
      audit_log.py               # Later, expanded in Phase 12 or 13
    schemas/
      auth.py                    # Phase 2
      user.py                    # Phase 2
      lab_template.py            # Phase 3
      lab_instance.py            # Phase 4
      ticket.py                  # Phase 5
      verification.py            # Phase 6
      ai.py                      # Phase 8 and Phase 11
    repositories/
      users.py                   # Phase 2
      lab_templates.py           # Phase 3
      labs.py                    # Phase 4
      tickets.py                 # Phase 5
      verification.py            # Phase 6
      ai.py                      # Phase 8 and Phase 11
      audit_logs.py              # Later
    services/
      auth_service.py            # Phase 2
      user_service.py            # Phase 2
      lab_template_service.py    # Phase 3
      lab_service.py             # Phase 4
      ticket_service.py          # Phase 5
      verification_service.py    # Phase 6
      ai_lab_builder_service.py  # Phase 8
      mentor_service.py          # Phase 11
      audit_service.py           # Later
    workers/
      lab_tasks.py               # Phase 4
      verification_tasks.py      # Phase 6
      cleanup_tasks.py           # Phase 13
    adapters/
      containerlab_adapter.py    # Phase 4
      ai_provider.py             # Phase 8
    lab_runtime/
      directory_manager.py       # Phase 4
      name_sanitizer.py          # Phase 3 or Phase 4
      yaml_validator.py          # Phase 3
      status_parser.py           # Phase 4
```

## Future Frontend Structure

Frontend implementation starts in Phase 7. Phase 1 should not create frontend files.

```text
frontend/
  src/
    app/
      App.tsx
      providers.tsx
    components/
      layout/
      ui/
    features/
      auth/              # Phase 7
      dashboard/         # Phase 7
      labTemplates/      # Phase 7
      labs/              # Phase 7
      tickets/           # Phase 7
      verification/      # Phase 7
      aiLabBuilder/      # Phase 9
      mentor/            # Phase 11
      users/             # Phase 7
      admin/             # Phase 12
      instructor/        # Phase 12
    lib/
      api.ts
      auth.ts
      routes.ts
    routes/
    types/
  Dockerfile
  package.json
  vite.config.ts
  tailwind.config.js
```

## Backend Boundaries

| Folder | Purpose | First Phase |
| --- | --- | --- |
| `api/` | FastAPI routers and request-level dependencies. | Phase 1 |
| `core/` | Settings, logging, security primitives, permissions, rate limiting. | Phase 1, expanded later |
| `db/` | SQLAlchemy session setup and database base configuration. | Phase 1 |
| `models/` | SQLAlchemy ORM models. | Phase 2 |
| `schemas/` | Pydantic request/response schemas. | Phase 2 |
| `repositories/` | Database access methods for business entities. | Phase 2 |
| `services/` | Business logic and orchestration. | Phase 2 |
| `workers/` | Celery app in Phase 1, domain tasks in later phases. | Phase 1 |
| `adapters/` | External system adapters such as Containerlab and AI providers. | Phase 4 |
| `lab_runtime/` | Lab file management, validation, status parsing, and safe naming utilities. | Phase 3 |
| `tests/` | Unit, integration, and security tests. | Phase 1 |

## Lab Storage Layout

Lab storage is planned for Phase 3 and Phase 4. It should not be used by Phase 1 except as documented configuration.

Runtime lab files must be stored below configured `LAB_ROOT`.

```text
LAB_ROOT/
  templates/
    <template_slug>/
      clab.yml
      configs/
  instances/
    <lab_instance_id>/
      clab.yml
      configs/
      logs/
      metadata.json
```

Rules:

- Do not store lab files outside `LAB_ROOT`.
- Do not accept raw file paths from users.
- Use generated IDs and sanitized slugs for directories.
- Destroyed labs may be cleaned by scheduled task after audit/log retention rules are satisfied.

