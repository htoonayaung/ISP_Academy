import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { roleLabel } from "../../lib/format";
import { useAuth } from "../auth/authStore";
import { Link } from "react-router-dom";

export function DashboardPage() {
  const { user } = useAuth();
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
  return (
    <div className="space-y-4">
      <PageHeader title="Dashboard" subtitle="Use this page as the starting point for the current MVP demo." />
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
