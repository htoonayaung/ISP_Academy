import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
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
  async function load() {
    setTickets(await api<Ticket[]>("/api/v1/tickets"));
    if (canManage) setTemplates(await api<LabTemplate[]>("/api/v1/lab-templates"));
  }
  useEffect(() => { load(); }, [canManage]);
  async function save(payload: Record<string, unknown>) {
    if (editing) await api(`/api/v1/tickets/${editing.id}`, { method: "PATCH", bodyJson: payload });
    else await api("/api/v1/tickets", { method: "POST", bodyJson: payload });
    setEditing(null); setCreating(false); await load();
  }
  async function post(path: string) { await api(path, { method: "POST" }); await load(); }
  async function archive(id: string) { if (confirm("Archive ticket?")) await post(`/api/v1/tickets/${id}/archive`); }
  return <div className="space-y-4"><Card title={canManage ? "Ticket Management" : "Published Tickets"} action={canManage && <Button onClick={() => setCreating(true)}>Create ticket</Button>}>
    <Table><thead><tr><Th>Title</Th><Th>Status</Th><Th>Actions</Th></tr></thead><tbody>{tickets.map((ticket) => <tr key={ticket.id}><Td><Link className="font-medium text-teal-700" to={`/tickets/${ticket.id}`}>{ticket.title}</Link></Td><Td><Badge value={ticket.status} /></Td><Td><div className="flex flex-wrap gap-2">{canManage && <><Button onClick={() => setEditing(ticket)}>Edit</Button><Button onClick={() => post(`/api/v1/tickets/${ticket.id}/publish`)}>Publish</Button><Button className="bg-rose-700 hover:bg-rose-800" onClick={() => archive(ticket.id)}>Archive</Button></>} {!canManage && <Link className="text-teal-700" to={`/tickets/${ticket.id}`}>Open</Link>}</div></Td></tr>)}</tbody></Table>
  </Card>{(creating || editing) && <Modal title={editing ? "Ticket" : "Create ticket"} onClose={() => { setCreating(false); setEditing(null); }}><TicketForm ticket={editing || undefined} templates={templates} onSubmit={save} /></Modal>}</div>;
}
