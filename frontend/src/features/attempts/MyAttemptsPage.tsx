import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { TicketAttempt } from "../../types/ticket";
import { useAuth } from "../auth/authStore";

export function MyAttemptsPage() {
  const { user } = useAuth();
  const [attempts, setAttempts] = useState<TicketAttempt[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (user?.role !== "STUDENT") return;
    api<TicketAttempt[]>("/api/v1/my/attempts")
      .then(setAttempts)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load attempts"));
  }, [user?.role]);
  if (user?.role !== "STUDENT") {
    return <div className="space-y-4"><PageHeader title="Attempts" subtitle="Student attempts are scoped to the owning student in this MVP." /><Card title="Attempts"><p className="text-sm text-slate-600">Use a student account to inspect live attempts.</p></Card></div>;
  }
  return <div className="space-y-4"><PageHeader title="My Attempts" subtitle="Each attempt links a published ticket to a lab instance." /><Card title="My Attempts">{error && <p className="mb-3 text-sm text-rose-700">{error}</p>}<Table><thead><tr><Th>Attempt</Th><Th>Status</Th><Th>Started</Th><Th>Lab</Th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><Td><Link className="font-medium text-teal-700" to={`/attempts/${attempt.id}`}>{attempt.id.slice(0, 8)}</Link></Td><Td><Badge value={attempt.status} /></Td><Td>{formatDate(attempt.started_at)}</Td><Td><Link className="text-teal-700" to={`/labs/${attempt.lab_instance_id}`}>Open lab</Link></Td></tr>)}</tbody></Table>{attempts.length === 0 && !error && <EmptyState title="No attempts yet" description="Open a published ticket and start an attempt to create a linked lab." />}</Card></div>;
}
