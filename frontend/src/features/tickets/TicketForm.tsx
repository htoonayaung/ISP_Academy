import { FormEvent, useState } from "react";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Textarea } from "../../components/ui/Textarea";
import { LabTemplate } from "../../types/labTemplate";
import { Ticket } from "../../types/ticket";

export function TicketForm({ ticket, templates, onSubmit }: { ticket?: Ticket; templates: LabTemplate[]; onSubmit: (data: Record<string, unknown>) => Promise<void> }) {
  const [data, setData] = useState({
    lab_template_id: ticket?.lab_template_id || templates[0]?.id || "",
    title: ticket?.title || "",
    description: ticket?.description || "",
    student_instructions: ticket?.student_instructions || "",
    hints: ticket?.hints || "",
    hidden_solution: ticket?.hidden_solution || "",
    status: ticket?.status || "DRAFT"
  });
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!data.lab_template_id) {
      setError("Choose an active lab template before creating a ticket.");
      return;
    }
    if (data.title.trim().length < 3) {
      setError("Ticket title must be at least 3 characters.");
      return;
    }
    if (!data.description.trim() || !data.student_instructions.trim()) {
      setError("Description and student instructions are required.");
      return;
    }
    await onSubmit({ ...data, hints: data.hints || null, hidden_solution: data.hidden_solution || null });
  }
  return <form onSubmit={submit} className="grid gap-3">
    {error && <Alert message={error} />}
    <Select value={data.lab_template_id} onChange={(e) => setData({ ...data, lab_template_id: e.target.value })}>{templates.map((t) => <option value={t.id} key={t.id}>{t.name}</option>)}</Select>
    <Input placeholder="Title" value={data.title} onChange={(e) => setData({ ...data, title: e.target.value })} />
    <Textarea placeholder="Description" value={data.description} onChange={(e) => setData({ ...data, description: e.target.value })} />
    <Textarea placeholder="Student instructions" value={data.student_instructions} onChange={(e) => setData({ ...data, student_instructions: e.target.value })} />
    <Textarea placeholder="Hints" value={data.hints || ""} onChange={(e) => setData({ ...data, hints: e.target.value })} />
    <p className="text-xs font-medium text-amber-700">Instructor-only solution. This field must never appear in the student UI.</p>
    <Textarea placeholder="Hidden solution" value={data.hidden_solution || ""} onChange={(e) => setData({ ...data, hidden_solution: e.target.value })} />
    <Select value={data.status} onChange={(e) => setData({ ...data, status: e.target.value as Ticket["status"] })}><option>DRAFT</option><option>PUBLISHED</option><option>ARCHIVED</option></Select>
    <Button>{ticket ? "Update ticket" : "Create ticket"}</Button>
  </form>;
}
