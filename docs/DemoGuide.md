# Demo Guide

## Purpose

This guide walks through the current AI-Powered ISP Academy MVP demo. The demo proves the core training workflow: users log in by role, instructors prepare safe lab content, students start a ticket attempt, Containerlab creates the lab, and verification checks return a result.

## URLs

- Frontend: `http://10.0.44.2:3000`
- Backend API: `http://10.0.44.2:8000`
- Swagger: `http://10.0.44.2:8000/docs`

## Demo Account Setup

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
3. Open a published ticket.
4. Confirm hidden solution is not visible.
5. Start an attempt.
6. Open the linked lab.
7. Start the lab.
8. Wait for `RUNNING`.
9. Return to the attempt and run verification.
10. Open the verification run and confirm per-rule result.
11. Destroy the lab.

Expected behavior: student can only see published tickets, own attempts, and own labs.

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
- Lab stuck: check `docker compose -f deployments/docker-compose.yml logs --tail=100 celery_worker`.
- Verification stuck: confirm lab is `RUNNING`, rule target node exists, and worker is running.
