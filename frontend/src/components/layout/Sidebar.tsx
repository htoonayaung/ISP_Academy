import { NavLink } from "react-router-dom";
import { FlaskConical, Home, ListChecks, Network, ShieldCheck, Sparkles, Ticket, Users, WandSparkles } from "lucide-react";
import { useAuth } from "../../features/auth/authStore";

const itemClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-md px-3 py-2 text-sm ${isActive ? "bg-teal-700 text-white" : "text-slate-700 hover:bg-slate-100"}`;

export function Sidebar() {
  const { user } = useAuth();
  const role = user?.role;
  const items = role === "ADMIN"
    ? [
        { to: "/dashboard", label: "Dashboard", icon: Home },
        { to: "/admin/demo-setup", label: "Demo Setup", icon: WandSparkles },
        { to: "/ai-lab-builder", label: "AI Lab Builder", icon: Sparkles },
        { to: "/users", label: "Users", icon: Users },
        { to: "/lab-templates", label: "Lab Templates", icon: Network },
        { to: "/labs", label: "Labs", icon: FlaskConical },
        { to: "/tickets", label: "Tickets", icon: Ticket },
        { to: "/verification-rules", label: "Verification Rules", icon: ShieldCheck },
        { to: "/attempts", label: "Attempts", icon: ListChecks }
      ]
    : role === "INSTRUCTOR"
      ? [
          { to: "/dashboard", label: "Dashboard", icon: Home },
          { to: "/ai-lab-builder", label: "AI Lab Builder", icon: Sparkles },
          { to: "/lab-templates", label: "Lab Templates", icon: Network },
          { to: "/labs", label: "Labs", icon: FlaskConical },
          { to: "/tickets", label: "Tickets", icon: Ticket },
          { to: "/verification-rules", label: "Verification Rules", icon: ShieldCheck }
        ]
      : [
          { to: "/dashboard", label: "Dashboard", icon: Home },
          { to: "/tickets", label: "Tickets", icon: Ticket },
          { to: "/attempts", label: "My Attempts", icon: ListChecks },
          { to: "/labs", label: "My Labs", icon: FlaskConical }
        ];
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white p-4 md:block">
      <div className="mb-6 text-lg font-bold text-slate-950">ISP Academy</div>
      <nav className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          return <NavLink key={item.to} className={itemClass} to={item.to}><Icon size={16} />{item.label}</NavLink>;
        })}
      </nav>
    </aside>
  );
}
