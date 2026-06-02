# Demo Guide

## Purpose

This guide walks through the current AI-Powered ISP Academy MVP demo. The demo proves the core training workflow: users log in by role, instructors prepare safe lab content, students start a ticket attempt, Containerlab creates the lab, and verification checks return a result.

## One-Click Demo Setup

Admin can use the Demo Setup Wizard:

```text
http://10.0.44.2:3000/admin/demo-setup
```

Steps:

1. Log in as Admin.
2. Open Demo Setup.
3. Review readiness status.
4. Click Run Demo Setup.
5. Store any generated demo passwords shown in the response.
6. Confirm the page shows demo-ready status.
7. Use the next-step buttons to copy `demo_student`, go to login, or open this guide.

The setup creates demo-prefixed records only and does not start labs, call AI, create LabInstances, or run Containerlab.

## Demo Reset Warning

Reset requires typing:

```text
RESET_DEMO_DATA
```

Reset targets demo-prefixed data only. If demo labs are running, stop or destroy them from the UI before resetting.

## URLs

- Frontend: `http://10.0.44.2:3000`
- Backend API: `http://10.0.44.2:8000`
- Swagger: `http://10.0.44.2:8000/docs`

## Manual Demo Account Setup

Use the seeded admin account to create instructor and student demo accounts.

1. Log in as admin.
2. Open `Users`.
3. Create one `INSTRUCTOR` account.
4. Create one `STUDENT` account.
5. Log out and verify each role can log in.

Do not commit real demo passwords to Git.

## Admin Flow

1. Log in.
2. Confirm Dashboard shows name, username, and `ADMIN`.
3. Confirm sidebar shows Dashboard, Users, Lab Templates, Labs, Tickets, Verification Rules, and Attempts.
4. Create instructor and student accounts.
5. Create an active lab template.
6. Validate the lab template.
7. Create a ticket from that template.
8. Add hints and an instructor-only hidden solution.
9. Publish the ticket.
10. Create a verification rule for the ticket.

Expected behavior: admin can manage users, templates, tickets, verification rules, and inspect labs.

## Instructor Flow

1. Log in as instructor.
2. Confirm Users menu is not visible.
3. Create an own lab template.
4. Create an own ticket.
5. Add hints and hidden solution text.
6. Publish the ticket.
7. Create verification rules for own tickets.

Expected behavior: instructor can manage own teaching content but cannot access admin user management.

## Student Flow

1. Log in as student.
2. Confirm only student navigation is visible: Dashboard, Tickets, My Attempts, My Labs.
3. Confirm Dashboard shows a recommended demo ticket card when demo data exists.
4. Open the demo ticket.
5. Confirm hidden solution is not visible.
6. Start an attempt.
7. Confirm Attempt Detail shows the five-step guide.
8. Open the linked lab.
9. Start the lab.
10. Wait for `RUNNING`.
11. Return to the attempt and run verification.
12. Confirm the verification run shows `PASSED`, `FAILED`, or `ERROR`.
13. Open the lab and destroy it.

Expected behavior: student can only see published tickets, own attempts, and own labs.

## Polished Browser Demo Flow

Use this as the live presentation script:

1. Admin logs in.
2. Admin opens `Demo Setup`.
3. Confirm the success panel says `Demo Ready`.
4. Copy `demo_student`.
5. Go to login and sign in as the student.
6. Student Dashboard shows `Start Demo Ticket`.
7. Student opens the ticket and reads instructions and hints.
8. Student clicks `Start Attempt`.
9. Attempt Detail shows:
   - Step 1: Start lab
   - Step 2: Wait until RUNNING
   - Step 3: Run verification
   - Step 4: Review result
   - Step 5: Destroy lab
10. Student opens the linked lab.
11. Student clicks `Start`.
12. Lab page shows `Lab is starting. This may take a few seconds.`
13. Wait until the status badge shows `RUNNING`.
14. Return to the attempt and click `Run Verification`.
15. Wait for the verification run to finish.
16. Confirm `Great! Your lab passed verification.` when the demo rule passes.
17. Open the lab and click `Destroy`.
18. Confirm destruction and wait for `DESTROYED`.

## What To Expect On Each Screen

- Demo Setup: `Demo Ready` success panel, demo usernames, next-step buttons, and a separated reset danger zone.
- Student Dashboard: Published Tickets, My Attempts, My Labs shortcuts, and a recommended demo ticket card.
- Ticket List: category, difficulty, status, demo badge, and `View Ticket` action.
- Ticket Detail: instructions, hints, prominent `Start Attempt`, and no hidden solution for students.
- Attempt Detail: linked ticket title, linked lab status, five-step guide, `Open Lab`, and `Run Verification`.
- Lab Detail: prominent status badge, state-aware lifecycle buttons, friendly progress text, nodes, and sanitized events.
- Verification Run: queued/running message, overall result, and per-rule result rows.

## Full Browser Demo Checklist

- Admin login works.
- Dashboard profile values are visible.
- Admin menu is complete.
- Create student works.
- Create lab template works.
- Validate template shows a clear result.
- Create ticket works.
- Publish ticket requires confirmation.
- Create verification rule works.
- Student login works.
- Student sees published ticket.
- Student does not see `hidden_solution`, instructor-only solution, answer, or solution text.
- Student starts attempt.
- Linked lab opens.
- Lab reaches `RUNNING`.
- Verification can run only when lab is `RUNNING`.
- Verification result shows `PASSED`, `FAILED`, or `ERROR`.
- Lab destroy requires confirmation and reaches `DESTROYED`.
- Browser console has no critical uncaught errors.

## Expected Page Behavior

- Dashboard shows user identity, role, system status, and role-based quick actions.
- Users page shows account role and active status.
- Lab Templates page shows category, difficulty, active state, validation action, and empty states.
- Tickets page shows category, difficulty, and Draft/Published/Archived status.
- Lab Detail page shows status, action buttons, nodes, and sanitized events.
- Attempt Detail page shows linked lab status and disables verification until the lab is `RUNNING`.
- Verification Run page shows overall status and per-rule result messages.

## Common Problems

- Blank profile/sidebar: clear `localStorage.isp_academy_token`, log in again, and check `/api/v1/auth/me`.
- CORS error: confirm backend `CORS_ORIGINS` includes `http://10.0.44.2:3000`.
- Lab stuck STARTING: wait 10 to 20 seconds, refresh the lab page, then check `docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker`.
- Duplicate start warning: the backend rejected a second start request because the lab is already starting or running.
- Verification button disabled: confirm the linked lab status is `RUNNING`.
- Verification stuck: confirm lab is `RUNNING`, the rule target node exists, and the worker is running.
- Verification failed: open the Verification Run page, review per-rule messages, then adjust the lab or rerun after the lab is still `RUNNING`.
