import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { VerificationRule } from "../../types/verification";

export function VerificationRulesPage() {
  const { id = "" } = useParams();
  const [rules, setRules] = useState<VerificationRule[]>([]);
  const [form, setForm] = useState({ name: "", target_node: "host1", command: "echo ok", parser_type: "SIMPLE_TEXT", assertion_type: "CONTAINS", expected_value: "ok", timeout_seconds: 5, is_active: true });
  async function load() { setRules(await api<VerificationRule[]>(`/api/v1/tickets/${id}/verification-rules`)); }
  useEffect(() => { load(); }, [id]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    await api(`/api/v1/tickets/${id}/verification-rules`, { method: "POST", bodyJson: form });
    setForm({ ...form, name: "" });
    await load();
  }
  async function remove(rule: VerificationRule) {
    if (!confirm("Delete rule?")) return;
    await api(`/api/v1/verification-rules/${rule.id}`, { method: "DELETE" });
    await load();
  }
  return <div className="space-y-4"><Card title="Verification Rules">
    <form onSubmit={submit} className="mb-4 grid gap-3 md:grid-cols-3">
      <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <Input placeholder="Target node" value={form.target_node} onChange={(e) => setForm({ ...form, target_node: e.target.value })} />
      <Input placeholder="Command" value={form.command} onChange={(e) => setForm({ ...form, command: e.target.value })} />
      <Select value={form.assertion_type} onChange={(e) => setForm({ ...form, assertion_type: e.target.value })}>{["CONTAINS","NOT_CONTAINS","EQUALS","EXIT_CODE_ZERO","BGP_NEIGHBOR_ESTABLISHED","ROUTE_EXISTS"].map((x) => <option key={x}>{x}</option>)}</Select>
      <Input placeholder="Expected" value={form.expected_value} onChange={(e) => setForm({ ...form, expected_value: e.target.value })} />
      <Input type="number" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} />
      <Button className="md:col-span-3">Create rule</Button>
    </form>
    <Table><thead><tr><Th>Name</Th><Th>Node</Th><Th>Assertion</Th><Th>Action</Th></tr></thead><tbody>{rules.map((rule) => <tr key={rule.id}><Td>{rule.name}</Td><Td>{rule.target_node}</Td><Td>{rule.assertion_type}</Td><Td><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => remove(rule)}>Delete</Button></Td></tr>)}</tbody></Table>
  </Card></div>;
}
