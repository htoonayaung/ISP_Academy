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
  const [error, setError] = useState("");
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
      setError("");
      await api(`/api/v1/tickets/${id}/verification-rules`, { method: "POST", bodyJson: form });
      setForm({ ...form, name: "" });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to save rule"); }
  }
  async function remove(rule: VerificationRule) {
    if (!confirm("Delete rule?")) return;
    try {
      setError("");
      await api(`/api/v1/verification-rules/${rule.id}`, { method: "DELETE" });
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to delete rule"); }
  }
  return <div className="space-y-4">
  <PageHeader title="Verification Rules" subtitle="Create simple command checks for this ticket. Rules run only against lab-owned nodes." />
  <Card title="Create Rule" subtitle="Target node is the node name in the lab template. Command output is compared with the selected assertion.">
    {error && <div className="mb-3"><Alert message={error} /></div>}
    <form onSubmit={submit} className="mb-4 grid gap-3 md:grid-cols-3">
      <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Input placeholder="Target node" value={form.target_node} onChange={(e) => setForm({ ...form, target_node: e.target.value })} />
      <Input placeholder="Command" value={form.command} onChange={(e) => setForm({ ...form, command: e.target.value })} />
      <Select value={form.assertion_type} onChange={(e) => setForm({ ...form, assertion_type: e.target.value })}>{["CONTAINS","NOT_CONTAINS","EQUALS","EXIT_CODE_ZERO","BGP_NEIGHBOR_ESTABLISHED","ROUTE_EXISTS"].map((x) => <option key={x}>{x}</option>)}</Select>
      <Input placeholder="Expected" value={form.expected_value} onChange={(e) => setForm({ ...form, expected_value: e.target.value })} />
      <Input type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} />
      <Button className="md:col-span-3">Create rule</Button>
    </form>
    <Table><thead><tr><Th>Name</Th><Th>Target Node</Th><Th>Command</Th><Th>Assertion</Th><Th>Expected</Th><Th>Action</Th></tr></thead><tbody>{rules.map((rule) => <tr key={rule.id}><Td>{rule.name}</Td><Td>{rule.target_node}</Td><Td><code className="rounded bg-slate-100 px-1">{rule.command}</code></Td><Td>{rule.assertion_type}</Td><Td>{rule.expected_value || "-"}</Td><Td><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => remove(rule)}>Delete</Button></Td></tr>)}</tbody></Table>
    {rules.length === 0 && !error && <EmptyState title="No verification rules yet" description="Add a target node, command, assertion, and expected value for the student demo." />}
  </Card></div>;
}
