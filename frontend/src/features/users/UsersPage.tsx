import { useEffect, useState } from "react";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { User } from "../../types/auth";
import { useAuth } from "../auth/authStore";
import { UserForm } from "./UserForm";

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetting, setResetting] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    try { setUsers(await api<User[]>("/api/v1/users")); } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
  }
  useEffect(() => { load(); }, []);

  async function save(payload: Record<string, unknown>) {
    try {
      if (editing) await api(`/api/v1/users/${editing.id}`, { method: "PATCH", bodyJson: payload });
      else await api("/api/v1/users", { method: "POST", bodyJson: payload });
      setEditing(null); setCreating(false); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
  }

  async function setActive(user: User, isActive: boolean) {
    const verb = isActive ? "Reactivate" : "Deactivate";
    if (!isActive && !confirm(`${verb} ${user.username}? They will no longer be able to login.`)) return;
    try {
      setError(""); setMessage("");
      await api(`/api/v1/users/${user.id}`, { method: "PATCH", bodyJson: { is_active: isActive } });
      setMessage(`${user.username} ${isActive ? "reactivated" : "deactivated"}.`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : `Failed to ${verb.toLowerCase()} user`); }
  }

  async function resetPassword() {
    if (!resetting) return;
    if (newPassword.length < 10) {
      setError("New password must be at least 10 characters.");
      return;
    }
    if (!confirm(`Reset password for ${resetting.username}?`)) return;
    try {
      setError(""); setMessage("");
      await api(`/api/v1/users/${resetting.id}/reset-password`, { method: "POST", bodyJson: { new_password: newPassword } });
      setMessage(`Password reset for ${resetting.username}.`);
      setResetting(null);
      setNewPassword("");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to reset password"); }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Users" subtitle="Create demo accounts and manage basic role-based access." />
      <Card title="Users" action={<Button onClick={() => setCreating(true)}>Create user</Button>}>
        {error && <div className="mb-3"><Alert message={error} /></div>}
        {message && <div className="mb-3 rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800">{message}</div>}
        <Table><thead><tr><Th>User</Th><Th>Role</Th><Th>Status</Th><Th>Actions</Th></tr></thead><tbody>
          {users.map((user) => <tr key={user.id}><Td><div className="font-medium">{user.username}</div><div className="text-xs text-slate-500">{user.email}</div><div className="text-xs text-slate-500">{user.full_name}</div></Td><Td>{user.role}</Td><Td><Badge value={user.is_active ? "ACTIVE" : "INACTIVE"} /></Td><Td><div className="flex flex-wrap gap-2"><Button onClick={() => setEditing(user)}>View/Edit</Button><Button onClick={() => { setResetting(user); setNewPassword(""); }}>Reset Password</Button>{user.is_active ? <Button disabled={user.id === currentUser?.id} className="bg-rose-700 hover:bg-rose-800" onClick={() => setActive(user, false)}>Deactivate</Button> : <Button className="bg-teal-700 hover:bg-teal-800" onClick={() => setActive(user, true)}>Reactivate</Button>}</div></Td></tr>)}
        </tbody></Table>
        {users.length === 0 && !error && <EmptyState title="No users yet" description="Create an instructor or student account for the demo." />}
      </Card>
      {(creating || editing) && <Modal title={editing ? "User" : "Create user"} onClose={() => { setCreating(false); setEditing(null); }}><UserForm user={editing || undefined} onSubmit={save} /></Modal>}
      {resetting && <Modal title={`Reset password for ${resetting.username}`} onClose={() => { setResetting(null); setNewPassword(""); }}>
        <div className="space-y-3">
          <p className="text-sm text-slate-600">Enter a new password. Passwords are never shown after reset.</p>
          <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} autoComplete="new-password" />
          <div className="flex justify-end gap-2"><Button className="bg-slate-200 text-slate-900 hover:bg-slate-300" onClick={() => { setResetting(null); setNewPassword(""); }}>Cancel</Button><Button onClick={resetPassword}>Reset Password</Button></div>
        </div>
      </Modal>}
    </div>
  );
}
