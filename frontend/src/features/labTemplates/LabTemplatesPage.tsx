import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { LabTemplate, ValidationResult } from "../../types/labTemplate";
import { LabTemplateForm } from "./LabTemplateForm";

export function LabTemplatesPage() {
  const [templates, setTemplates] = useState<LabTemplate[]>([]);
  const [editing, setEditing] = useState<LabTemplate | null>(null);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function load() { try { setTemplates(await api<LabTemplate[]>("/api/v1/lab-templates")); } catch (err) { setError(err instanceof Error ? err.message : "Failed"); } }
  useEffect(() => { load(); }, []);
  async function save(payload: Record<string, unknown>) {
    try {
      if (editing) await api(`/api/v1/lab-templates/${editing.id}`, { method: "PATCH", bodyJson: payload });
      else await api("/api/v1/lab-templates", { method: "POST", bodyJson: payload });
      setEditing(null); setCreating(false); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
  }
  async function validate(id: string) {
    try {
      setError("");
      const result = await api<ValidationResult>(`/api/v1/lab-templates/${id}/validate`, { method: "POST" });
      setMessage(result.is_valid ? "Template is valid" : result.errors.join(", "));
    } catch (err) { setError(err instanceof Error ? err.message : "Validation failed"); }
  }
  async function deactivate(id: string) {
    if (!confirm("Deactivate template?")) return;
    try {
      setError("");
      await api(`/api/v1/lab-templates/${id}`, { method: "DELETE" }); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to deactivate template"); }
  }
  return (
    <div className="space-y-4"><Card title="Lab Templates" action={<Button onClick={() => setCreating(true)}>Create template</Button>}>
      {error && <Alert message={error} />}{message && <div className="mb-3 rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800">{message}</div>}
      <Table><thead><tr><Th>Name</Th><Th>Category</Th><Th>Status</Th><Th>Actions</Th></tr></thead><tbody>
        {templates.map((template) => <tr key={template.id}><Td><Link className="font-medium text-teal-700" to={`/lab-templates/${template.id}`}>{template.name}</Link></Td><Td>{template.category}</Td><Td><Badge value={template.is_active ? "ACTIVE" : "INACTIVE"} /></Td><Td><div className="flex flex-wrap gap-2"><Button onClick={() => setEditing(template)}>Edit</Button><Button onClick={() => validate(template.id)}>Validate</Button><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => deactivate(template.id)}>Deactivate</Button></div></Td></tr>)}
      </tbody></Table>
    </Card>{(creating || editing) && <Modal title={editing ? "Lab template" : "Create template"} onClose={() => { setCreating(false); setEditing(null); }}><LabTemplateForm template={editing || undefined} onSubmit={save} /></Modal>}</div>
  );
}
