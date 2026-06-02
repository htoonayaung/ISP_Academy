# Instructor Guide

## Login

Open `http://10.0.44.2:3000` and log in with an instructor account. The sidebar should show Dashboard, Lab Templates, Labs, Tickets, and Verification Rules. The Users admin page should not be visible.

## Create Lab Templates

1. Open `Lab Templates`.
2. Click `Create template`.
3. Enter a clear name, description, category, difficulty, and resource estimates.
4. Paste safe Containerlab YAML.
5. Save.
6. Click `Validate`.

Templates must stay inside the allowed MVP safety scope. Do not use host mounts, external networks, arbitrary images, or privileged containers.

Use `Activate` only after validation passes and the template is ready for tickets. Use `Deactivate` to remove a template from new student use without deleting history. Use `Duplicate` to create an inactive copy for revisions.

## Create Tickets

1. Open `Tickets`.
2. Click `Create ticket`.
3. Select one of your templates.
4. Enter the problem statement and student instructions.
5. Add hints when useful.
6. Add hidden solution text for staff review.
7. Save as `DRAFT`.

## Add Hints And Hidden Solution

Hints may be shown to students. Hidden solution is instructor-only and should contain the answer, expected commands, or instructor notes.

Always verify as a student that hidden solution text is not visible.

## Publish Tickets

Use `Publish` when the template, instructions, and verification rules are ready. Published tickets appear in the student ticket list.

Use `Unpublish` to return a ticket to draft when it needs revision.

Use `Archive` when a ticket should no longer be available to students.

## Create Verification Rules

1. Open `Verification Rules`.
2. Select the ticket.
3. Add target node, command, assertion type, and expected value.
4. Keep commands simple and safe.

Example:

- Target node: `host1`
- Command: `echo ok`
- Assertion type: `CONTAINS`
- Expected value: `ok`

Use `Edit` for corrections. Use `Deactivate` instead of hard delete when a rule should no longer run; old verification runs remain stored.

## Review Attempts

Open `Attempts` to review attempts for tickets you created. The view is read-only in this MVP. Students still control their own lab lifecycle and run verification from their own attempt page.

## Topology Diagrams

Instructors can view read-only topology diagrams for templates and labs they are allowed to access. AI Lab Builder preview pages also show topology previews before approval.

Clicking a node shows details only. There is no console, terminal, config apply, or topology editor in this phase.

## View Student Flow

For demo validation, use a student account to:

1. Open the published ticket.
2. Start an attempt.
3. Start the linked lab.
4. Wait for `RUNNING`.
5. Run verification.
6. Confirm the result is shown.
