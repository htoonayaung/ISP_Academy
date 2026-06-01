import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
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
    return <Card title="Attempts"><p className="text-sm text-slate-600">Attempt listing is student-scoped in this MVP. Use a student account to inspect live attempts.</p></Card>;
  }
  return <Card title="My Attempts">{error && <p className="mb-3 text-sm text-rose-700">{error}</p>}<Table><thead><tr><Th>Attempt</Th><Th>Status</Th><Th>Started</Th><Th>Lab</Th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><Td><Link className="text-teal-700" to={`/attempts/${attempt.id}`}>{attempt.id.slice(0, 8)}</Link></Td><Td><Badge value={attempt.status} /></Td><Td>{formatDate(attempt.started_at)}</Td><Td><Link className="text-teal-700" to={`/labs/${attempt.lab_instance_id}`}>Open lab</Link></Td></tr>)}</tbody></Table>{attempts.length === 0 && !error && <p className="mt-3 text-sm text-slate-500">No attempts yet.</p>}</Card>;
}
