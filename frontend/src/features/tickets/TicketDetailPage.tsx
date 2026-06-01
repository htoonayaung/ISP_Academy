import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { api } from "../../lib/api";
import { Ticket, TicketAttempt } from "../../types/ticket";
import { useAuth } from "../auth/authStore";

export function TicketDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  useEffect(() => { api<Ticket>(`/api/v1/tickets/${id}`).then(setTicket); }, [id]);
  async function start() {
    const attempt = await api<TicketAttempt>(`/api/v1/tickets/${id}/start`, { method: "POST" });
    navigate(`/attempts/${attempt.id}`);
  }
  if (!ticket) return null;
  return <Card title={ticket.title} action={<Badge value={ticket.status} />}>
    <p className="mb-3 text-sm text-slate-600">{ticket.description}</p>
    <h3 className="mb-1 font-semibold">Instructions</h3><p className="mb-3 whitespace-pre-wrap text-sm">{ticket.student_instructions}</p>
    {ticket.hints && <><h3 className="mb-1 font-semibold">Hints</h3><p className="mb-3 whitespace-pre-wrap text-sm">{ticket.hints}</p></>}
    {user?.role !== "STUDENT" && ticket.hidden_solution && <><h3 className="mb-1 font-semibold">Hidden solution</h3><p className="mb-3 whitespace-pre-wrap rounded-md bg-amber-50 p-3 text-sm">{ticket.hidden_solution}</p></>}
    {user?.role === "STUDENT" ? <Button onClick={start}>Start attempt</Button> : <Link className="text-teal-700" to={`/tickets/${ticket.id}/verification-rules`}>Manage verification rules</Link>}
  </Card>;
}
