import { Navigate, Outlet } from "react-router-dom";
import { Spinner } from "../ui/Spinner";
import { useAuth } from "../../features/auth/authStore";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center"><Spinner /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
