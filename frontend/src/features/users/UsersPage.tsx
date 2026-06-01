import { useEffect, useState } from "react";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { User } from "../../types/auth";
import { UserForm } from "./UserForm";

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [editing, setEditing] = useState<User | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

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

  async function deactivate(user: User) {
    if (!confirm(`Deactivate ${user.username}?`)) return;
    try {
      setError("");
      await api(`/api/v1/users/${user.id}`, { method: "DELETE" });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to deactivate user"); }
  }

  return (
    <div className="space-y-4">
      <Card title="Users" action={<Button onClick={() => setCreating(true)}>Create user</Button>}>
        {error && <div className="mb-3"><Alert message={error} /></div>}
        <Table><thead><tr><Th>User</Th><Th>Role</Th><Th>Status</Th><Th>Actions</Th></tr></thead><tbody>
          {users.map((user) => <tr key={user.id}><Td><div className="font-medium">{user.username}</div><div className="text-xs text-slate-500">{user.email}</div></Td><Td>{user.role}</Td><Td><Badge value={user.is_active ? "ACTIVE" : "INACTIVE"} /></Td><Td><div className="flex gap-2"><Button onClick={() => setEditing(user)}>View/Edit</Button><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => deactivate(user)}>Deactivate</Button></div></Td></tr>)}
        </tbody></Table>
      </Card>
      {(creating || editing) && <Modal title={editing ? "User" : "Create user"} onClose={() => { setCreating(false); setEditing(null); }}><UserForm user={editing || undefined} onSubmit={save} /></Modal>}
    </div>
  );
}
