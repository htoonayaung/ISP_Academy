import { FormEvent, useState } from "react";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Role, User } from "../../types/auth";

export function UserForm({ user, onSubmit }: { user?: User; onSubmit: (data: Record<string, unknown>) => Promise<void> }) {
  const [data, setData] = useState({
    email: user?.email || "",
    username: user?.username || "",
    password: "",
    full_name: user?.full_name || "",
    role: user?.role || "STUDENT",
    is_active: user?.is_active ?? true
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    const payload: Record<string, unknown> = { ...data };
    if (user && !data.password) delete payload.password;
    await onSubmit(payload);
  }

  return (
    <form onSubmit={submit} className="grid gap-3 md:grid-cols-2">
      <Input placeholder="Email" value={data.email} onChange={(e) => setData({ ...data, email: e.target.value })} />
      <Input placeholder="Username" value={data.username} onChange={(e) => setData({ ...data, username: e.target.value })} />
      <Input placeholder={user ? "New password" : "Password"} type="password" value={data.password} onChange={(e) => setData({ ...data, password: e.target.value })} />
      <Input placeholder="Full name" value={data.full_name} onChange={(e) => setData({ ...data, full_name: e.target.value })} />
      <Select value={data.role} onChange={(e) => setData({ ...data, role: e.target.value as Role })}>
        <option>ADMIN</option><option>INSTRUCTOR</option><option>STUDENT</option>
      </Select>
      <Select value={String(data.is_active)} onChange={(e) => setData({ ...data, is_active: e.target.value === "true" })}>
        <option value="true">Active</option><option value="false">Inactive</option>
      </Select>
      <Button className="md:col-span-2">{user ? "Update user" : "Create user"}</Button>
    </form>
  );
}
