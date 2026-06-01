import { Navigate, Outlet } from "react-router-dom";
import { Role } from "../../types/auth";
import { useAuth } from "../../features/auth/authStore";

export function RoleRoute({ roles }: { roles: Role[] }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return <Navigate to="/unauthorized" replace />;
  return <Outlet />;
}
