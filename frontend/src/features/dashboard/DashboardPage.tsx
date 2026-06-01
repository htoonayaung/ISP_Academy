import { Card } from "../../components/ui/Card";
import { useAuth } from "../auth/authStore";

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-950">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Profile">
          <dl className="space-y-2 text-sm">
            <div><dt className="text-slate-500">Name</dt><dd className="font-medium">{user?.full_name}</dd></div>
            <div><dt className="text-slate-500">Username</dt><dd className="font-medium">{user?.username}</dd></div>
            <div><dt className="text-slate-500">Role</dt><dd className="font-medium">{user?.role}</dd></div>
          </dl>
        </Card>
        <Card title="Labs"><p className="text-sm text-slate-600">Create or manage lab instances from tickets and templates.</p></Card>
        <Card title="Verification"><p className="text-sm text-slate-600">Run checks after your lab reaches RUNNING.</p></Card>
      </div>
    </div>
  );
}
