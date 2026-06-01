import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { CopyId } from "../../components/ui/CopyId";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { AILabBuilderApproval, AILabBuilderPreview } from "../../types/aiLabBuilder";

export function AiLabBuilderPreviewDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<AILabBuilderPreview | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  async function load() {
    if (!id) return;
    try {
      setError("");
      setPreview(await api<AILabBuilderPreview>(`/api/v1/ai-lab-builder/previews/${id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preview");
    }
  }

  useEffect(() => { load(); }, [id]);

  async function approve() {
    if (!preview || !confirm("Approve this preview and create an inactive LabTemplate?")) return;
    setIsBusy(true);
    try {
      const result = await api<AILabBuilderApproval>(`/api/v1/ai-lab-builder/previews/${preview.id}/approve`, { method: "POST" });
      setPreview(result.preview);
      setMessage("Preview approved and inactive lab template created.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setIsBusy(false);
    }
  }

  async function reject() {
    if (!preview) return;
    setIsBusy(true);
    try {
      setPreview(await api<AILabBuilderPreview>(`/api/v1/ai-lab-builder/previews/${preview.id}/reject`, { method: "POST" }));
      setMessage("Preview rejected.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reject failed");
    } finally {
      setIsBusy(false);
    }
  }

  async function remove() {
    if (!preview || !confirm("Delete this preview? Approved previews cannot be deleted.")) return;
    setIsBusy(true);
    try {
      await api(`/api/v1/ai-lab-builder/previews/${preview.id}`, { method: "DELETE" });
      navigate("/ai-lab-builder/previews");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setIsBusy(false);
    }
  }

  if (!preview && error) {
    return <div className="space-y-4"><PageHeader title="AI Preview" subtitle="Preview could not be loaded." /><Alert message={error} /></div>;
  }
  if (!preview) {
    return <div className="space-y-4"><PageHeader title="AI Preview" subtitle="Loading preview..." /><EmptyState title="Loading" description="Fetching generated plan and validation results." /></div>;
  }

  const canApprove = preview.validation_status === "PASSED" && !["APPROVED", "REJECTED"].includes(preview.status);

  return (
    <div className="space-y-4">
      <PageHeader
        title={preview.lab_plan_json.title}
        subtitle={preview.lab_plan_json.description}
        action={<CopyId id={preview.id} label="Preview ID" />}
      />
      {error && <Alert message={error} />}
      {message && <div className="rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800">{message}</div>}
      <Card
        title="Review"
        subtitle="Approval creates an inactive LabTemplate only. It does not start a lab."
        action={<div className="flex flex-wrap gap-2"><Button disabled={!canApprove || isBusy} onClick={approve}>Approve</Button><Button disabled={isBusy || preview.status === "REJECTED"} onClick={reject}>Reject</Button><Button className="bg-rose-700 hover:bg-rose-800" disabled={isBusy || preview.status === "APPROVED"} onClick={remove}>Delete</Button></div>}
      >
        <div className="grid gap-3 text-sm md:grid-cols-4">
          <div><div className="text-slate-500">Status</div><Badge value={preview.status} /></div>
          <div><div className="text-slate-500">Validation</div><Badge value={preview.validation_status} /></div>
          <div><div className="text-slate-500">Category</div><Badge value={preview.lab_plan_json.category} /></div>
          <div><div className="text-slate-500">Difficulty</div><Badge value={preview.lab_plan_json.difficulty} /></div>
        </div>
        {preview.created_lab_template_id && (
          <div className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm">
            Created LabTemplate: <Link className="font-medium text-teal-700" to={`/lab-templates/${preview.created_lab_template_id}`}>{preview.created_lab_template_id}</Link>
          </div>
        )}
      </Card>
      <Card title="Validation Errors" subtitle="AI output is blocked until these are fixed by a new prompt.">
        {preview.validation_errors.length > 0 ? <ul className="list-disc space-y-1 pl-5 text-sm text-rose-700">{preview.validation_errors.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="text-sm text-slate-600">No validation errors.</p>}
      </Card>
      <Card title="Generated Topology" subtitle="Containerlab YAML preview. No deployment occurs in Phase 8.">
        <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-50">{preview.generated_containerlab_yaml}</pre>
      </Card>
      <Card title="Nodes and Links" subtitle="Generated plan summary.">
        <div className="grid gap-4 lg:grid-cols-2">
          <Table><thead><tr><Th>Node</Th><Th>Kind</Th><Th>Image</Th></tr></thead><tbody>{preview.lab_plan_json.nodes.map((node) => <tr key={node.name}><Td>{node.name}</Td><Td>{node.kind}</Td><Td>{node.image}</Td></tr>)}</tbody></Table>
          <Table><thead><tr><Th>Endpoints</Th><Th>Subnet</Th></tr></thead><tbody>{preview.lab_plan_json.links.map((link, index) => <tr key={`${link.endpoints.join("-")}-${index}`}><Td>{link.endpoints.join(" <-> ")}</Td><Td>{link.subnet || "-"}</Td></tr>)}</tbody></Table>
        </div>
      </Card>
      <Card title="Generated Configs" subtitle="Startup config preview generated from the plan.">
        <div className="grid gap-3">
          {preview.generated_configs.map((config) => (
            <div key={`${config.node}-${config.config_type}`}>
              <div className="mb-1 text-sm font-medium text-slate-700">{config.node}</div>
              <pre className="max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-50">{config.content || "# no config"}</pre>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Verification Rules" subtitle="Previewed rules that can be copied into Phase 6 after template approval.">
        <Table>
          <thead><tr><Th>Name</Th><Th>Target</Th><Th>Command</Th><Th>Assertion</Th></tr></thead>
          <tbody>{preview.generated_verification_rules.map((rule) => <tr key={rule.name}><Td>{rule.name}</Td><Td>{rule.target_node}</Td><Td><code>{rule.command}</code></Td><Td>{rule.assertion_type}</Td></tr>)}</tbody>
        </Table>
      </Card>
    </div>
  );
}
