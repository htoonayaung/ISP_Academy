# MVP Features

## MVP Goal

The MVP must prove that a small ISP training workflow works end to end:

```text
Admin creates users
Instructor creates lab template
Instructor creates ticket
Student starts lab
Containerlab deploys lab
Student troubleshoots lab
Student runs verification
System shows pass/fail
Instructor views progress
```

## Target Scale

- 20 to 50 users.
- 5 to 10 concurrent students.
- 5 to 20 running labs.
- Single organization.
- Single Ubuntu server.
- Containerlab-only lab environment.

## Included In MVP

### Authentication And Roles

- Basic login.
- JWT access token.
- Admin, Instructor, Student roles.
- Role-based API permissions.
- Initial admin seed process.

### Lab Templates

- Admin and Instructor can create lab templates.
- Templates store Containerlab YAML safely.
- Templates include metadata such as category, difficulty, estimated resources, and duration.
- Student can view only active templates.
- Template validation checks YAML and basic safety constraints.

### Lab Instances

- Student can create lab instances from approved templates.
- Student can start, stop, destroy, and view own labs.
- Instructor/Admin can inspect student labs.
- Lab state is tracked clearly.
- Lab operations run through Celery and Containerlab Adapter.

### Ticket-Based Learning

- Instructor can create tickets linked to lab templates.
- Ticket has student-facing instructions.
- Ticket can include hints.
- Ticket can include hidden solution.
- Student must never see hidden solution.
- Student can start an attempt from a published ticket.

### Verification Engine

- Instructor can define basic verification rules.
- Student can run verification against own ticket attempt.
- Verification runs only against nodes inside the student's lab.
- Results are stored and shown as pass/fail with details.

### Minimal Frontend

- Login page.
- Dashboard.
- Lab templates page.
- My labs page.
- Lab detail page.
- Tickets page.
- Ticket detail page.
- My attempts page.
- Verification result page.
- Basic admin users page.

### AI Lab Builder V1

- Instructor/Admin submits a prompt.
- Backend requests strict structured LabPlan JSON from AI.
- Backend validates LabPlan.
- Backend generates preview artifacts.
- Instructor/Admin approves before creating template.
- No auto-deploy without approval.

### AI Mentor Lite

- Student can request safe hints for a ticket attempt.
- AI context excludes hidden solution.
- Hinting does not provide full final configuration.
- Requests are audited and rate limited.

## Excluded From MVP

- 1000-user scaling.
- Kubernetes.
- High availability.
- Full multi-tenancy.
- Departments and teams.
- Certification engine.
- XP, badges, ranks, or leaderboards.
- Advanced analytics.
- Full topology editor.
- Snapshot/restore.
- Multi-host scheduling.
- Arbitrary SSH automation.
- Production network integration.
- Advanced NetBox-style inventory.
- Full AI mentor.
- Multi-provider AI routing.

## MVP Acceptance Criteria

The MVP is successful when:

- Admin can create users.
- Instructor can create or generate a lab template.
- Instructor can create and publish a ticket.
- Student can start the ticket lab.
- Containerlab can deploy the lab.
- Student can troubleshoot inside the lab.
- Student can run verification.
- System can show pass/fail result.
- Instructor can see student progress.
- AI Lab Builder can generate a validated preview.
- AI Mentor can provide safe hints without leaking hidden solution.

