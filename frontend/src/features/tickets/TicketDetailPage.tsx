import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { Spinner } from "../../components/ui/Spinner";
import { CopyId } from "../../components/ui/CopyId";
import { PageHeader } from "../../components/ui/PageHeader";
import { api } from "../../lib/api";
import { Ticket, TicketAttempt } from "../../types/ticket";
import { useAuth } from "../auth/authStore";

export function TicketDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Ticket>(`/api/v1/tickets/${id}`)
      .then(setTicket)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load ticket"));
  }, [id]);
  async function start() {
    try {
      setStarting(true);
      setError("");
      const attempt = await api<TicketAttempt>(`/api/v1/tickets/${id}/start`, { method: "POST" });
      navigate(`/attempts/${attempt.id}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to start attempt"); }
    finally { setStarting(false); }
  }
  if (!ticket) return error ? <Alert message={error} /> : <Spinner />;
  return <div className="space-y-4">
  <PageHeader title={ticket.title} subtitle={ticket.description} action={<CopyId id={ticket.id} label="Ticket ID" />} />
  <Card title="Ticket Detail" subtitle={user?.role === "STUDENT" ? "Read the instructions, then start your attempt. You will be sent directly to the attempt page." : "Instructor-only solution is visible only to authorized staff."} action={<Badge value={ticket.status} />}>
    {error && <div className="mb-3"><Alert message={error} /></div>}
    {ticket.slug === "demo-linux-verification-ticket" && <div className="mb-4 rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-900">Demo ticket: start an attempt, start the linked lab, wait for RUNNING, then run verification.</div>}
    <h3 className="mb-1 font-semibold">Instructions</h3><p className="mb-3 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm">{ticket.student_instructions}</p>
    {ticket.hints && <><h3 className="mb-1 font-semibold">Hints</h3><p className="mb-3 whitespace-pre-wrap rounded-md bg-amber-50 p-3 text-sm text-amber-900">{ticket.hints}</p></>}
    {user?.role !== "STUDENT" && ticket.hidden_solution && <><h3 className="mb-1 font-semibold">Instructor-only solution</h3><p className="mb-3 whitespace-pre-wrap rounded-md bg-amber-50 p-3 text-sm">{ticket.hidden_solution}</p></>}
    {user?.role === "STUDENT" ? <Button className="bg-teal-700 hover:bg-teal-800" disabled={starting} onClick={start}>{starting ? "Starting attempt..." : "Start Attempt"}</Button> : <Link className="font-medium text-teal-700" to={`/tickets/${ticket.id}/verification-rules`}>Manage verification rules</Link>}
  </Card>
  </div>;
}
