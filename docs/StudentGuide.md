# Student Guide

## Login

Open `http://10.0.44.2:3000` and log in with a student account. The sidebar should show Dashboard, Tickets, My Attempts, and My Labs.

## View Published Tickets

Open `Tickets`. Only published tickets are visible. Each ticket shows status and, when available, the linked lab category and difficulty.

## Start Attempt

1. Open a ticket.
2. Read the description, instructions, and hints.
3. Confirm no hidden solution or answer text is visible.
4. Click `Start attempt`.

An attempt creates a linked lab instance in `CREATED` state.

## Open Linked Lab

On the Attempt Detail page, click `Open linked lab`. The Lab Detail page shows status, nodes, lifecycle events, and action buttons.

## View Topology

Students can view read-only topology diagrams for published templates and their own lab instances.

On a lab page, the diagram may show node status and management IP after the lab is running. Clicking a node opens a detail panel.

Console access is not available yet. Students cannot access AI Lab Builder preview topology or other students' lab topology.

## Start Lab

Click `Start`. The status changes to `STARTING` and then `RUNNING`.

Wait until the status is `RUNNING` before running verification.

## Run Verification

Return to the Attempt Detail page. The `Run verification` button is disabled until the linked lab is `RUNNING`.

Click `Run verification` when enabled. The page will show verification runs and status.

## View Result

Open the verification run to see:

- Overall status: `PASSED`, `FAILED`, or `ERROR`.
- Per-rule result.
- Result message.

## Destroy Lab

After the demo, open the linked lab and click `Destroy`. Confirm the dialog. Wait until the lab reaches `DESTROYED`.

Destroying labs after use helps keep the single-server MVP stable.
