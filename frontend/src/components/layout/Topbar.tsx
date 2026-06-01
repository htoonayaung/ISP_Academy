import { LogOut, Menu } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../features/auth/authStore";
import { Button } from "../ui/Button";

export function Topbar() {
  const { user, logout } = useAuth();
  return (
    <header className="border-b border-slate-200 bg-white px-4 py-3">
      <div className="flex items-center justify-between">
      <div className="text-sm font-medium text-slate-600">AI-Powered ISP Academy MVP</div>
      <div className="flex items-center gap-3">
        <div className="text-right text-sm">
          <div className="font-medium text-slate-900">{user?.username || "Loading"}</div>
          <div className="text-xs text-slate-500">{user?.role || "-"}</div>
        </div>
        <Button onClick={logout} className="bg-slate-100 text-slate-900 hover:bg-slate-200"><LogOut size={16} />Logout</Button>
      </div>
      </div>
      <nav className="mt-3 flex gap-2 overflow-x-auto md:hidden">
        <NavLink className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-slate-700" to="/dashboard"><Menu size={14} />Menu</NavLink>
      </nav>
    </header>
  );
}
