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

## Manage Users Safely

Use the `Users` actions column for routine account operations:

- `View/Edit` updates profile fields, role, and active state.
- `Deactivate` disables login without deleting history.
- `Reactivate` restores login for an inactive account.
- `Reset Password` sets a new password through an admin-only backend endpoint. Passwords are never displayed after reset.

The current admin account cannot deactivate itself. Create a second admin account before rotating or disabling the original admin.

## Create Lab Templates

1. Open `Lab Templates`.
2. Click `Create template`.
3. Enter metadata, category, difficulty, resource estimates, and safe Containerlab YAML.
4. Set active only when the template is ready for tickets.
5. Save.

Use only allowed MVP images and kinds. Do not use host mounts, external networks, privileged containers, or production network targets.

## Manage Lab Templates Safely

Use template actions for operational cleanup:

- `Edit` changes metadata, resource estimates, and YAML after backend validation.
- `Validate` checks Containerlab YAML without starting a lab.
- `Activate` makes a template available for tickets and students.
- `Deactivate` hides a template from new student use while keeping history.
- `Duplicate` creates an inactive copy owned by the current user.

Avoid hard deletion for templates referenced by tickets or lab history. Deactivate instead.

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
- Use `Unpublish` to return a ticket to `DRAFT`.
- Use `Archive` to remove it from the student list.
- Confirm destructive or visibility-changing actions before proceeding.

## Create Verification Rules

1. Open `Verification Rules`.
2. Choose a ticket.
3. Add a rule name.
4. Enter target node, command, assertion type, expected value, and timeout.
5. Save.

Rules run only against lab-owned nodes in a student's running lab attempt.

Use `Edit` to tune a rule. Use `Deactivate` instead of hard delete so older verification history remains understandable.

## Monitor Labs

Open `Labs` to inspect lab status. Use Lab Detail to view:

- Current lab state.
- Nodes and management addresses.
- Sanitized lifecycle events.
- Start, Stop, and Destroy actions when allowed.

Destroy demo labs after use to release server resources.

## Runtime Operations

Open `Lab Runtime` as Admin.

Use this page when labs are stuck, demo runtime files need cleanup, or lab runtime state needs review before a demo.

Runtime states:

- `STARTING` means the worker has queued or is deploying the lab.
- `STOPPING` means the worker is destroying Containerlab resources but preserving the lab record.
- `DESTROYING` means the worker is destroying runtime resources and marking the lab destroyed.
- `FAILED` means the previous lifecycle action failed and needs staff review.

Available actions:

- `Refresh` queues worker-side inspection. It does not delete or destroy anything.
- `Mark failed` is for stuck `STARTING`, `STOPPING`, or `DESTROYING` labs. It changes DB status only and creates a lifecycle event.
- `Retry destroy` queues the normal safe destroy task again.
- `Force destroy demo` is restricted to demo-prefixed labs and requires typed confirmation.
- `Cleanup demo runtime` removes only demo-prefixed destroyed or failed runtime artifacts when safe. It never targets active non-demo labs.

Typed confirmations:

- Runtime recovery requires `RECOVER_LAB`.
- Demo runtime cleanup requires `CLEANUP_DEMO_RUNTIME`.

Destroyed lab records may remain in the database for history. Use cleanup only for runtime files, not for learning history.

## Review Attempts

Open `Attempts` to inspect student attempts:

- Admins see all attempts.
- Instructors see attempts for their own tickets.
- Students see only their own attempts.

Attempt management is read-only in this MVP. Do not reset or remove attempt history manually.
