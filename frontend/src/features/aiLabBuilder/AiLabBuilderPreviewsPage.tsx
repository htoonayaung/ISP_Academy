import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { AILabBuilderPreview } from "../../types/aiLabBuilder";

export function AiLabBuilderPreviewsPage() {
  const [previews, setPreviews] = useState<AILabBuilderPreview[]>([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setError("");
      setPreviews(await api<AILabBuilderPreview[]>("/api/v1/ai-lab-builder/previews"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load previews");
    }
  }

  useEffect(() => { load(); }, []);

  async function act(preview: AILabBuilderPreview, action: "approve" | "reject" | "delete") {
    const label = action === "approve" ? "Approve this preview and create an inactive LabTemplate?" : action === "reject" ? "Reject this preview?" : "Delete this preview?";
    if (!confirm(label)) return;
    try {
      setError("");
      if (action === "approve") await api(`/api/v1/ai-lab-builder/previews/${preview.id}/approve`, { method: "POST" });
      if (action === "reject") await api(`/api/v1/ai-lab-builder/previews/${preview.id}/reject`, { method: "POST" });
      if (action === "delete") await api(`/api/v1/ai-lab-builder/previews/${preview.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview action failed");
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Lab Previews"
        subtitle="Review generated plans before they become inactive lab templates."
        action={<Link className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to="/ai-lab-builder">New Preview</Link>}
      />
      <Card title="Previews" subtitle="Admin sees all previews. Instructors see only their own previews.">
        {error && <Alert message={error} />}
        <Table>
          <thead><tr><Th>Preview</Th><Th>Category</Th><Th>Validation</Th><Th>Status</Th><Th>Created</Th><Th>Action</Th></tr></thead>
          <tbody>
            {previews.map((preview) => (
              <tr key={preview.id}>
                <Td><Link className="font-medium text-teal-700" to={`/ai-lab-builder/previews/${preview.id}`}>{preview.lab_plan_json.title}</Link><div className="text-xs text-slate-500">{preview.prompt}</div></Td>
                <Td>{preview.lab_plan_json.category}</Td>
                <Td><Badge value={preview.validation_status} /></Td>
                <Td><Badge value={preview.status} /></Td>
                <Td>{new Date(preview.created_at).toLocaleString()}</Td>
                <Td><div className="flex flex-wrap gap-2"><Link to={`/ai-lab-builder/previews/${preview.id}`}><Button>Open</Button></Link><Button disabled={preview.validation_status !== "PASSED" || ["APPROVED", "REJECTED"].includes(preview.status)} onClick={() => act(preview, "approve")}>Approve</Button><Button disabled={preview.status === "REJECTED"} onClick={() => act(preview, "reject")}>Reject</Button><Button disabled={preview.status === "APPROVED"} className="bg-rose-700 hover:bg-rose-800" onClick={() => act(preview, "delete")}>Delete</Button></div></Td>
              </tr>
            ))}
          </tbody>
        </Table>
        {previews.length === 0 && !error && <EmptyState title="No AI previews yet" description="Generate a preview, inspect validation, then approve it into a lab template." />}
      </Card>
    </div>
  );
}
