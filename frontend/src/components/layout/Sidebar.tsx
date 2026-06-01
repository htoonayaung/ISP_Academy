import { NavLink } from "react-router-dom";
import { FlaskConical, Home, ListChecks, Network, Ticket, Users } from "lucide-react";
import { useAuth } from "../../features/auth/authStore";

const itemClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-md px-3 py-2 text-sm ${isActive ? "bg-teal-700 text-white" : "text-slate-700 hover:bg-slate-100"}`;

export function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const isInstructor = user?.role === "INSTRUCTOR";
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white p-4 md:block">
      <div className="mb-6 text-lg font-bold text-slate-950">ISP Academy</div>
      <nav className="space-y-1">
        <NavLink className={itemClass} to="/dashboard"><Home size={16} />Dashboard</NavLink>
        {isAdmin && <NavLink className={itemClass} to="/users"><Users size={16} />Users</NavLink>}
        {(isAdmin || isInstructor) && <NavLink className={itemClass} to="/lab-templates"><Network size={16} />Lab Templates</NavLink>}
        <NavLink className={itemClass} to="/labs"><FlaskConical size={16} />Labs</NavLink>
        <NavLink className={itemClass} to="/tickets"><Ticket size={16} />Tickets</NavLink>
        {user?.role === "STUDENT" && <NavLink className={itemClass} to="/attempts"><ListChecks size={16} />My Attempts</NavLink>}
      </nav>
    </aside>
  );
}
