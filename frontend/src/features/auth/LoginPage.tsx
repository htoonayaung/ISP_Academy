import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { useAuth } from "./authStore";

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-lg bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold">ISP Academy</h1>
        <p className="mb-5 text-sm text-slate-500">Sign in to continue</p>
        {error && <div className="mb-4"><Alert message={error} /></div>}
        <label className="mb-3 block text-sm font-medium">Username or email<Input value={username} onChange={(e) => setUsername(e.target.value)} /></label>
        <label className="mb-5 block text-sm font-medium">Password<Input value={password} onChange={(e) => setPassword(e.target.value)} type="password" /></label>
        <Button className="w-full" disabled={loading}>{loading ? "Signing in..." : "Login"}</Button>
      </form>
    </div>
  );
}
