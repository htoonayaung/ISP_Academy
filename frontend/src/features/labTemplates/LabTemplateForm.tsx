import { FormEvent, useState } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Textarea } from "../../components/ui/Textarea";
import { LabTemplate } from "../../types/labTemplate";

const defaultYaml = `name: basic-linux
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:3.20
      cmd: sleep infinity
`;

export function LabTemplateForm({ template, onSubmit }: { template?: LabTemplate; onSubmit: (data: Record<string, unknown>) => Promise<void> }) {
  const [data, setData] = useState({
    name: template?.name || "",
    description: template?.description || "",
    category: template?.category || "Linux",
    difficulty: template?.difficulty || "Easy",
    containerlab_yaml: template?.containerlab_yaml || defaultYaml,
    default_startup_config: template?.default_startup_config || "",
    estimated_cpu: template?.estimated_cpu || 1,
    estimated_memory_mb: template?.estimated_memory_mb || 128,
    estimated_duration_minutes: template?.estimated_duration_minutes || 30,
    is_active: template?.is_active || false
  });
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (data.name.trim().length < 3) {
      setError("Template name must be at least 3 characters.");
      return;
    }
    if (!data.description.trim() || !data.containerlab_yaml.trim()) {
      setError("Description and Containerlab YAML are required.");
      return;
    }
    await onSubmit({ ...data, default_startup_config: data.default_startup_config || null });
  }
  return (
    <form onSubmit={submit} className="grid gap-3">
      {error && <Alert message={error} />}
      <Input placeholder="Name" value={data.name} onChange={(e) => setData({ ...data, name: e.target.value })} />
      <Textarea placeholder="Description" value={data.description} onChange={(e) => setData({ ...data, description: e.target.value })} />
      <div className="grid gap-3 md:grid-cols-3">
        <Select value={data.category} onChange={(e) => setData({ ...data, category: e.target.value })}>{["Linux","BGP","OSPF","ISIS","MPLS","EVPN","VXLAN","Security"].map((x) => <option key={x}>{x}</option>)}</Select>
        <Select value={data.difficulty} onChange={(e) => setData({ ...data, difficulty: e.target.value })}>{["Easy","Medium","Hard"].map((x) => <option key={x}>{x}</option>)}</Select>
        <Select value={String(data.is_active)} onChange={(e) => setData({ ...data, is_active: e.target.value === "true" })}><option value="false">Inactive</option><option value="true">Active</option></Select>
      </div>
      <Textarea className="font-mono" value={data.containerlab_yaml} onChange={(e) => setData({ ...data, containerlab_yaml: e.target.value })} />
      <div className="grid gap-3 md:grid-cols-3">
        <Input type="number" value={data.estimated_cpu} onChange={(e) => setData({ ...data, estimated_cpu: Number(e.target.value) })} />
        <Input type="number" value={data.estimated_memory_mb} onChange={(e) => setData({ ...data, estimated_memory_mb: Number(e.target.value) })} />
        <Input type="number" value={data.estimated_duration_minutes} onChange={(e) => setData({ ...data, estimated_duration_minutes: Number(e.target.value) })} />
      </div>
      <Button>{template ? "Update template" : "Create template"}</Button>
    </form>
  );
}
