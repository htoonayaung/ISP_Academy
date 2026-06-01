import { LogOut } from "lucide-react";
import { useAuth } from "../../features/auth/authStore";
import { Button } from "../ui/Button";

export function Topbar() {
  const { user, logout } = useAuth();
  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
      <div className="text-sm font-medium text-slate-600">AI-Powered ISP Academy MVP</div>
      <div className="flex items-center gap-3">
        <div className="text-right text-sm">
          <div className="font-medium text-slate-900">{user?.username}</div>
          <div className="text-xs text-slate-500">{user?.role}</div>
        </div>
        <Button onClick={logout} className="bg-slate-100 text-slate-900 hover:bg-slate-200"><LogOut size={16} />Logout</Button>
      </div>
    </header>
  );
}
