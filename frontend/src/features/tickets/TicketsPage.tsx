import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Modal } from "../../components/ui/Modal";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { LabTemplate } from "../../types/labTemplate";
import { Ticket } from "../../types/ticket";
import { useAuth } from "../auth/authStore";
import { TicketForm } from "./TicketForm";

export function TicketsPage() {
  const { user } = useAuth();
  const canManage = user?.role !== "STUDENT";
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [templates, setTemplates] = useState<LabTemplate[]>([]);
  const [editing, setEditing] = useState<Ticket | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  async function load() {
    try {
      setError("");
      setTickets(await api<Ticket[]>("/api/v1/tickets"));
      setTemplates(await api<LabTemplate[]>("/api/v1/lab-templates"));
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load tickets"); }
  }
  useEffect(() => { load(); }, [canManage]);
  async function save(payload: Record<string, unknown>) {
    try {
      if (editing) await api(`/api/v1/tickets/${editing.id}`, { method: "PATCH", bodyJson: payload });
      else await api("/api/v1/tickets", { method: "POST", bodyJson: payload });
      setEditing(null); setCreating(false); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to save ticket"); }
  }
  async function post(path: string, confirmation?: string) {
    if (confirmation && !confirm(confirmation)) return;
    try { await api(path, { method: "POST" }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Request failed"); }
  }
  async function archive(id: string) { await post(`/api/v1/tickets/${id}/archive`, "Archive this ticket? Students will no longer see it."); }
  return <div className="space-y-4">
    <PageHeader title={canManage ? "Ticket Management" : "Published Tickets"} subtitle={canManage ? "Create, publish, archive, and prepare verification rules for troubleshooting tickets." : "Choose a published ticket to start a lab attempt."} />
    <Card title={canManage ? "Tickets" : "Available Tickets"} subtitle={canManage ? "Draft tickets stay private until published." : "Only published tickets are shown to students."} action={canManage && <Button onClick={() => setCreating(true)}>Create ticket</Button>}>
    {error && <div className="mb-3"><Alert message={error} /></div>}
    <Table><thead><tr><Th>Title</Th><Th>Category</Th><Th>Difficulty</Th><Th>Status</Th><Th>Actions</Th></tr></thead><tbody>{tickets.map((ticket) => {
      const template = templates.find((item) => item.id === ticket.lab_template_id);
      const isDemo = ticket.slug === "demo-linux-verification-ticket";
      return <tr key={ticket.id}><Td><Link className="font-medium text-teal-700" to={`/tickets/${ticket.id}`}>{ticket.title}</Link>{isDemo && <span className="ml-2 rounded bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-700">Demo</span>}<div className="text-xs text-slate-500">{ticket.description}</div></Td><Td>{template?.category || "-"}</Td><Td>{template?.difficulty ? <Badge value={template.difficulty} /> : "-"}</Td><Td><Badge value={ticket.status} /></Td><Td><div className="flex flex-wrap gap-2">{canManage && <><Button onClick={() => setEditing(ticket)}>Edit</Button><Button onClick={() => post(`/api/v1/tickets/${ticket.id}/publish`, "Publish this ticket to students?")}>Publish</Button><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => archive(ticket.id)}>Archive</Button></>} {!canManage && <Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to={`/tickets/${ticket.id}`}>View Ticket</Link>}</div></Td></tr>;
    })}</tbody></Table>
    {tickets.length === 0 && !error && <EmptyState title={canManage ? "No tickets yet" : "No published tickets yet"} description={canManage ? "Create a ticket from an active lab template, then publish it for students." : "No published tickets yet. Ask your instructor."} />}
  </Card>{(creating || editing) && <Modal title={editing ? "Ticket" : "Create ticket"} onClose={() => { setCreating(false); setEditing(null); }}><TicketForm ticket={editing || undefined} templates={templates} onSubmit={save} /></Modal>}</div>;
}
