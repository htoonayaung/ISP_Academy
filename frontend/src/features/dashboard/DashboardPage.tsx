import { useEffect, useState } from "react";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { roleLabel } from "../../lib/format";
import { useAuth } from "../auth/authStore";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { Ticket } from "../../types/ticket";

export function DashboardPage() {
  const { user } = useAuth();
  const [demoTicket, setDemoTicket] = useState<Ticket | null>(null);
  const [ticketError, setTicketError] = useState("");

  useEffect(() => {
    if (user?.role !== "STUDENT") return;
    api<Ticket[]>("/api/v1/tickets")
      .then((tickets) => setDemoTicket(tickets.find((ticket) => ticket.slug === "demo-linux-verification-ticket") || tickets[0] || null))
      .catch((err) => setTicketError(err instanceof Error ? err.message : "Failed to load tickets"));
  }, [user?.role]);

  const quickActions = user?.role === "ADMIN"
      ? [
        { label: "Manage users", to: "/users" },
        { label: "AI lab builder", to: "/ai-lab-builder" },
        { label: "Create templates", to: "/lab-templates" },
        { label: "Manage tickets", to: "/tickets" }
      ]
    : user?.role === "INSTRUCTOR"
      ? [
          { label: "AI lab builder", to: "/ai-lab-builder" },
          { label: "Create templates", to: "/lab-templates" },
          { label: "Manage tickets", to: "/tickets" },
          { label: "Verification rules", to: "/verification-rules" }
        ]
      : [
          { label: "View tickets", to: "/tickets" },
          { label: "My attempts", to: "/attempts" },
          { label: "My labs", to: "/labs" }
        ];
  const isStudent = user?.role === "STUDENT";
  return (
    <div className="space-y-4">
      <PageHeader title="Dashboard" subtitle={isStudent ? "Follow the guided demo path: open a ticket, start an attempt, run the lab, then verify it." : "Use this page as the starting point for the current MVP demo."} />
      {isStudent && (
        <Card title="Recommended Next Step" subtitle="Start here for the live MVP student demo.">
          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <div className="rounded-md border border-teal-200 bg-teal-50 p-4">
              <h3 className="text-base font-semibold text-teal-950">{demoTicket ? "Start Demo Ticket" : "Open Published Tickets"}</h3>
              <p className="mt-1 text-sm text-teal-900">
                {demoTicket ? demoTicket.description : "No demo ticket was found yet. Open tickets to see what is published for your account."}
              </p>
              {ticketError && <p className="mt-2 text-sm text-rose-700">{ticketError}</p>}
              <Link className="mt-3 inline-flex min-h-9 items-center rounded-md bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800" to={demoTicket ? `/tickets/${demoTicket.id}` : "/tickets"}>
                {demoTicket ? "Start Demo Ticket" : "View Tickets"}
              </Link>
            </div>
            <div className="space-y-2 text-sm text-slate-700">
              <div className="rounded-md bg-slate-50 p-3">1. Open the published demo ticket.</div>
              <div className="rounded-md bg-slate-50 p-3">2. Start an attempt to create your linked lab.</div>
              <div className="rounded-md bg-slate-50 p-3">3. Start the lab, run verification, then destroy it.</div>
            </div>
          </div>
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Current User" subtitle="Signed-in account">
          <dl className="space-y-2 text-sm">
            <div><dt className="text-slate-500">Name</dt><dd className="font-medium">{user?.full_name || "-"}</dd></div>
            <div><dt className="text-slate-500">Username</dt><dd className="font-medium">{user?.username || "-"}</dd></div>
            <div><dt className="text-slate-500">Role</dt><dd className="font-medium"><Badge value={user?.role || "UNKNOWN"} /></dd></div>
          </dl>
        </Card>
        <Card title="Role" subtitle={roleLabel(user?.role)}>
          <p className="text-sm text-slate-600">Your navigation and actions are limited by this role. Student pages only show own tickets, attempts, and labs.</p>
        </Card>
        <Card title="System Status" subtitle="MVP single-server deployment">
          <p className="text-sm text-slate-600">Frontend and backend are running through Docker Compose. API readiness is available at <code className="rounded bg-slate-100 px-1">/ready</code>.</p>
        </Card>
      </div>
      <Card title="Quick Actions" subtitle="Common next steps for your role">
        <div className="flex flex-wrap gap-2">
          {quickActions.map((action) => <Link key={action.to} className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to={action.to}>{action.label}</Link>)}
        </div>
      </Card>
    </div>
  );
}
