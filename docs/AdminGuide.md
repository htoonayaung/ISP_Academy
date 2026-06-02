# Admin Guide

## Login

Open `http://10.0.44.2:3000` and log in with an admin account. The Dashboard should show the admin name, username, and `ADMIN` role.

## Demo Setup Wizard

Open `http://10.0.44.2:3000/admin/demo-setup` as Admin.

Use this page to create repeatable demo data:

- Demo instructor account.
- Demo student account.
- Demo Basic Linux Lab template.
- Demo Linux Verification Ticket.
- Demo uname verification rule.

The setup is idempotent and creates missing demo records only. It does not start labs, create LabInstances, call AI, or run Containerlab.

Reset requires typing `RESET_DEMO_DATA` and targets demo-prefixed data only. Do not use demo passwords in production.

## Create Users

1. Open `Users`.
2. Click `Create user`.
3. Enter email, username, password, full name, role, and active state.
4. Save.

Admins can create `ADMIN`, `INSTRUCTOR`, and `STUDENT` users. Only admins should change roles or deactivate users.

## Create Lab Templates

1. Open `Lab Templates`.
2. Click `Create template`.
3. Enter metadata, category, difficulty, resource estimates, and safe Containerlab YAML.
4. Set active only when the template is ready for tickets.
5. Save.

Use only allowed MVP images and kinds. Do not use host mounts, external networks, privileged containers, or production network targets.

## Validate Templates

1. Open `Lab Templates`.
2. Click `Validate` on a template.
3. Confirm the result says the template is valid.

Validation checks structure and safety but does not start a lab.

## Create Tickets

1. Open `Tickets`.
2. Click `Create ticket`.
3. Select an active lab template.
4. Add title, description, student instructions, hints, and instructor-only hidden solution.
5. Save as `DRAFT`.

The hidden solution is visible only to authorized staff and must not appear in the student UI.

## Publish Or Archive Tickets

- Use `Publish` to make a ticket visible to students.
- Use `Archive` to remove it from the student list.
- Confirm destructive or visibility-changing actions before proceeding.

## Create Verification Rules

1. Open `Verification Rules`.
2. Choose a ticket.
3. Add a rule name.
4. Enter target node, command, assertion type, expected value, and timeout.
5. Save.

Rules run only against lab-owned nodes in a student's running lab attempt.

## Monitor Labs

Open `Labs` to inspect lab status. Use Lab Detail to view:

- Current lab state.
- Nodes and management addresses.
- Sanitized lifecycle events.
- Start, Stop, and Destroy actions when allowed.

Destroy demo labs after use to release server resources.
