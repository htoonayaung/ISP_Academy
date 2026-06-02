import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { VerificationRule } from "../../types/verification";

export function VerificationRulesPage() {
  const { id = "" } = useParams();
  const [rules, setRules] = useState<VerificationRule[]>([]);
  const [form, setForm] = useState({ name: "", target_node: "host1", command: "echo ok", parser_type: "SIMPLE_TEXT", assertion_type: "CONTAINS", expected_value: "ok", timeout_seconds: 5, is_active: true });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function load() {
    try { setError(""); setRules(await api<VerificationRule[]>(`/api/v1/tickets/${id}/verification-rules`)); }
    catch (err) { setError(err instanceof Error ? err.message : "Failed to load rules"); }
  }
  useEffect(() => { load(); }, [id]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (form.name.trim().length < 3) {
      setError("Rule name must be at least 3 characters.");
      return;
    }
    if (!form.target_node.trim() || !form.command.trim()) {
      setError("Target node and command are required.");
      return;
    }
    try {
      setError(""); setMessage("");
      if (editingId) await api(`/api/v1/verification-rules/${editingId}`, { method: "PATCH", bodyJson: form });
      else await api(`/api/v1/tickets/${id}/verification-rules`, { method: "POST", bodyJson: form });
      setForm({ ...form, name: "" });
      setEditingId(null);
      setMessage(editingId ? "Rule updated." : "Rule created.");
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to save rule"); }
  }
  function edit(rule: VerificationRule) {
    setEditingId(rule.id);
    setForm({
      name: rule.name,
      target_node: rule.target_node,
      command: rule.command,
      parser_type: rule.parser_type,
      assertion_type: rule.assertion_type,
      expected_value: rule.expected_value || "",
      timeout_seconds: rule.timeout_seconds,
      is_active: rule.is_active
    });
  }
  async function setActive(rule: VerificationRule, isActive: boolean) {
    if (!confirm(`${isActive ? "Reactivate" : "Deactivate"} rule "${rule.name}"? Historical results will remain.`)) return;
    try {
      setError(""); setMessage("");
      if (isActive) await api(`/api/v1/verification-rules/${rule.id}`, { method: "PATCH", bodyJson: { is_active: true } });
      else await api(`/api/v1/verification-rules/${rule.id}`, { method: "DELETE" });
      setMessage(`${rule.name} ${isActive ? "reactivated" : "deactivated"}.`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to update rule"); }
  }
  return <div className="space-y-4">
  <PageHeader title="Verification Rules" subtitle="Create simple command checks for this ticket. Rules run only against lab-owned nodes." />
  <Card title="Create Rule" subtitle="Target node is the node name in the lab template. Command output is compared with the selected assertion.">
    {error && <div className="mb-3"><Alert message={error} /></div>}
    {message && <div className="mb-3 rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800">{message}</div>}
    <form onSubmit={submit} className="mb-4 grid gap-3 md:grid-cols-3">
      <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Input placeholder="Target node" value={form.target_node} onChange={(e) => setForm({ ...form, target_node: e.target.value })} />
      <Input placeholder="Command" value={form.command} onChange={(e) => setForm({ ...form, command: e.target.value })} />
      <Select value={form.assertion_type} onChange={(e) => setForm({ ...form, assertion_type: e.target.value })}>{["CONTAINS","NOT_CONTAINS","EQUALS","EXIT_CODE_ZERO","BGP_NEIGHBOR_ESTABLISHED","ROUTE_EXISTS"].map((x) => <option key={x}>{x}</option>)}</Select>
      <Input placeholder="Expected" value={form.expected_value} onChange={(e) => setForm({ ...form, expected_value: e.target.value })} />
      <Input type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} />
      <div className="flex gap-2 md:col-span-3"><Button>{editingId ? "Update rule" : "Create rule"}</Button>{editingId && <Button type="button" className="bg-slate-200 text-slate-900 hover:bg-slate-300" onClick={() => { setEditingId(null); setForm({ name: "", target_node: "host1", command: "echo ok", parser_type: "SIMPLE_TEXT", assertion_type: "CONTAINS", expected_value: "ok", timeout_seconds: 5, is_active: true }); }}>Cancel edit</Button>}</div>
    </form>
    <Table><thead><tr><Th>Name</Th><Th>Target Node</Th><Th>Command</Th><Th>Assertion</Th><Th>Expected</Th><Th>Status</Th><Th>Action</Th></tr></thead><tbody>{rules.map((rule) => <tr key={rule.id}><Td>{rule.name}</Td><Td>{rule.target_node}</Td><Td><code className="rounded bg-slate-100 px-1">{rule.command}</code></Td><Td>{rule.assertion_type}</Td><Td>{rule.expected_value || "-"}</Td><Td>{rule.is_active ? "ACTIVE" : "INACTIVE"}</Td><Td><div className="flex flex-wrap gap-2"><Button onClick={() => edit(rule)}>Edit</Button>{rule.is_active ? <Button className="bg-rose-700 hover:bg-rose-800" onClick={() => setActive(rule, false)}>Deactivate</Button> : <Button className="bg-teal-700 hover:bg-teal-800" onClick={() => setActive(rule, true)}>Reactivate</Button>}</div></Td></tr>)}</tbody></Table>
    {rules.length === 0 && !error && <EmptyState title="No verification rules yet" description="Add a target node, command, assertion, and expected value for the student demo." />}
  </Card></div>;
}
