# API List

## API Conventions

- Base path: `/api/v1`
- Authentication: JWT bearer token after Phase 2.
- Response format: JSON.
- Errors use consistent structured error objects.
- Student-facing endpoints must exclude hidden/instructor-only fields.
- Long-running operations enqueue Celery tasks and return current resource state.

## Phase 1 API Boundary

Phase 1 includes only foundation/system endpoints:

- `GET /health`
- `GET /ready`
- `GET /api/v1/system/info`

No authentication, user, lab, ticket, verification, AI, mentor, admin, or instructor APIs should be generated in Phase 1.

## System

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 1 | `GET` | `/health` | Basic process health. | Public |
| Phase 1 | `GET` | `/ready` | Database/Redis readiness. | Public |
| Phase 1 | `GET` | `/api/v1/system/info` | Version and foundation feature info. | Public or authenticated later |

## Authentication

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 2 | `POST` | `/api/v1/auth/login` | Login and receive access token. | Public |
| Phase 2 | `GET` | `/api/v1/auth/me` | Return current user profile. | Authenticated |

## Users

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 2 | `POST` | `/api/v1/users` | Create user. | Admin |
| Phase 2 | `GET` | `/api/v1/users` | List users. | Admin, Instructor limited |
| Phase 2 | `GET` | `/api/v1/users/{user_id}` | View user. | Admin, Instructor limited, self |
| Phase 2 | `PATCH` | `/api/v1/users/{user_id}` | Update user. | Admin, self limited |
| Phase 2 | `DELETE` | `/api/v1/users/{user_id}` | Deactivate/delete user. | Admin |

## Lab Templates

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 3 | `POST` | `/api/v1/lab-templates` | Create lab template. | Admin, Instructor |
| Phase 3 | `GET` | `/api/v1/lab-templates` | List lab templates. | Admin, Instructor, Student active-only |
| Phase 3 | `GET` | `/api/v1/lab-templates/{template_id}` | View lab template. | Admin, Instructor, Student active-only |
| Phase 3 | `PATCH` | `/api/v1/lab-templates/{template_id}` | Update lab template. | Admin, owner Instructor |
| Phase 3 | `DELETE` | `/api/v1/lab-templates/{template_id}` | Delete/deactivate lab template. | Admin, owner Instructor |
| Phase 3 | `POST` | `/api/v1/lab-templates/{template_id}/validate` | Validate template YAML and safety rules. | Admin, owner Instructor |

## Labs

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 4 | `POST` | `/api/v1/labs` | Create lab instance from template. | Admin, Instructor, Student |
| Phase 4 | `GET` | `/api/v1/labs` | List visible labs. | Admin all, Instructor scoped, Student own |
| Phase 4 | `GET` | `/api/v1/labs/{lab_id}` | View lab detail. | Admin, Instructor scoped, owner Student |
| Phase 4 | `POST` | `/api/v1/labs/{lab_id}/start` | Queue lab start task. | Admin, Instructor scoped, owner Student |
| Phase 4 | `POST` | `/api/v1/labs/{lab_id}/stop` | Queue lab stop task. | Admin, Instructor scoped, owner Student |
| Phase 4 | `POST` | `/api/v1/labs/{lab_id}/destroy` | Queue lab destroy task. | Admin, Instructor scoped, owner Student |
| Phase 4 | `GET` | `/api/v1/labs/{lab_id}/status` | Get lifecycle status. | Admin, Instructor scoped, owner Student |
| Phase 4 | `GET` | `/api/v1/labs/{lab_id}/nodes` | List lab-owned nodes. | Admin, Instructor scoped, owner Student |
| Phase 4 | `GET` | `/api/v1/labs/{lab_id}/events` | List lab events/logs. | Admin, Instructor scoped, owner Student |

## Tickets

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 5 | `POST` | `/api/v1/tickets` | Create ticket. | Admin, Instructor |
| Phase 5 | `GET` | `/api/v1/tickets` | List tickets. | Admin, Instructor, Student published-only |
| Phase 5 | `GET` | `/api/v1/tickets/{ticket_id}` | View ticket. | Admin, Instructor, Student published-only |
| Phase 5 | `PATCH` | `/api/v1/tickets/{ticket_id}` | Update ticket. | Admin, owner Instructor |
| Phase 5 | `DELETE` | `/api/v1/tickets/{ticket_id}` | Delete/archive ticket. | Admin, owner Instructor |
| Phase 5 | `POST` | `/api/v1/tickets/{ticket_id}/publish` | Publish ticket. | Admin, owner Instructor |
| Phase 5 | `POST` | `/api/v1/tickets/{ticket_id}/archive` | Archive ticket. | Admin, owner Instructor |
| Phase 5 | `POST` | `/api/v1/tickets/{ticket_id}/start` | Start student attempt and lab. | Student |
| Phase 5 | `GET` | `/api/v1/my/attempts` | List own attempts. | Student |
| Phase 5 | `GET` | `/api/v1/my/attempts/{attempt_id}` | View own attempt. | Student |

## Verification

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 6 | `POST` | `/api/v1/tickets/{ticket_id}/verification-rules` | Create verification rule. | Admin, owner Instructor |
| Phase 6 | `GET` | `/api/v1/tickets/{ticket_id}/verification-rules` | List verification rules. | Admin, Instructor, Student limited result context |
| Phase 6 | `PATCH` | `/api/v1/verification-rules/{rule_id}` | Update rule. | Admin, owner Instructor |
| Phase 6 | `DELETE` | `/api/v1/verification-rules/{rule_id}` | Delete rule. | Admin, owner Instructor |
| Phase 6 | `POST` | `/api/v1/my/attempts/{attempt_id}/verify` | Queue verification run. | Student owner |
| Phase 6 | `GET` | `/api/v1/my/attempts/{attempt_id}/verification-runs` | List own verification runs. | Student owner |
| Phase 6 | `GET` | `/api/v1/my/verification-runs/{run_id}` | View own verification run. | Student owner |

## AI Lab Builder

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 8 | `POST` | `/api/v1/ai-lab-builder/preview` | Generate validated lab preview. | Admin, Instructor |
| Phase 8.5 | `GET` | `/api/v1/ai-lab-builder/provider/status` | Return safe provider status without API key. | Admin |
| Phase 8 | `GET` | `/api/v1/ai-lab-builder/previews` | List AI lab previews. | Admin all, owner Instructor |
| Phase 8 | `GET` | `/api/v1/ai-lab-builder/previews/{preview_id}` | View preview. | Admin, owner Instructor |
| Phase 8 | `POST` | `/api/v1/ai-lab-builder/previews/{preview_id}/approve` | Approve preview and create inactive lab template. | Admin, owner Instructor |
| Phase 8 | `POST` | `/api/v1/ai-lab-builder/previews/{preview_id}/reject` | Reject preview. | Admin, owner Instructor |
| Phase 8 | `DELETE` | `/api/v1/ai-lab-builder/previews/{preview_id}` | Delete unapproved preview. | Admin, owner Instructor |

## AI Mentor Lite

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 11 | `POST` | `/api/v1/my/attempts/{attempt_id}/mentor` | Request safe mentor hint. | Student owner |
| Phase 11 | `GET` | `/api/v1/my/attempts/{attempt_id}/mentor/messages` | View own mentor messages. | Student owner |

## Instructor And Admin

| Phase | Method | Path | Purpose | Roles |
| --- | --- | --- | --- | --- |
| Phase 12 | `GET` | `/api/v1/admin/overview` | Admin dashboard summary. | Admin |
| Phase 12 | `GET` | `/api/v1/instructor/overview` | Instructor dashboard summary. | Instructor |
| Phase 12 | `GET` | `/api/v1/instructor/students` | Student list visible to instructor. | Instructor |
| Phase 12 | `GET` | `/api/v1/instructor/attempts` | Student attempts for instructor content. | Instructor |
| Phase 12 | `GET` | `/api/v1/instructor/tickets/{ticket_id}/attempts` | Attempts for one ticket. | Instructor owner, Admin |
| Later | `GET` | `/api/v1/admin/audit-logs` | Audit log viewer. | Admin |
| Phase 12 | `GET` | `/api/v1/admin/lab-usage` | Lab usage summary. | Admin |

## API Security Notes

- Every protected endpoint must perform authorization at service layer, not only in router dependencies.
- Student ticket responses must omit `hidden_solution`.
- Lab command endpoints must accept only lab ID, target node name, and allowed command patterns.
- Verification commands come from instructor-defined rules, not arbitrary student input.
- AI endpoints are disabled when provider config is disabled.
- Endpoints must be implemented only in their assigned phase.
