import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Select } from "../../components/ui/Select";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { TicketAttempt } from "../../types/ticket";
import { useAuth } from "../auth/authStore";

export function MyAttemptsPage() {
  const { user } = useAuth();
  const [attempts, setAttempts] = useState<TicketAttempt[]>([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!user) return;
    const path = user?.role === "STUDENT" ? "/api/v1/my/attempts" : "/api/v1/attempts";
    api<TicketAttempt[]>(path)
      .then(setAttempts)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load attempts"));
  }, [user?.role]);
  async function hardDelete(attempt: TicketAttempt) {
    if (!confirm(`Permanently delete attempt ${attempt.id.slice(0, 8)}? Verification run history for this attempt will also be deleted.`)) return;
    try {
      setError("");
      await api(`/api/v1/attempts/${attempt.id}/hard-delete`, { method: "DELETE" });
      const path = user?.role === "STUDENT" ? "/api/v1/my/attempts" : "/api/v1/attempts";
      setAttempts(await api<TicketAttempt[]>(path));
    } catch (err) { setError(err instanceof Error ? err.message : "Delete failed"); }
  }
  const visibleAttempts = attempts.filter((attempt) => statusFilter === "ALL" || attempt.status === statusFilter);
  const title = user?.role === "STUDENT" ? "My Attempts" : "Attempts";
  const subtitle = user?.role === "STUDENT" ? "Each attempt links a published ticket to a lab instance." : "Review student attempts scoped by backend permissions.";
  return <div className="space-y-4"><PageHeader title={title} subtitle={subtitle} /><Card title={title} action={<Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="ALL">All statuses</option><option value="STARTED">Started</option><option value="IN_PROGRESS">In Progress</option><option value="SUBMITTED">Submitted</option><option value="PASSED">Passed</option><option value="FAILED">Failed</option></Select>}>{error && <p className="mb-3 text-sm text-rose-700">{error}</p>}<Table><thead><tr><Th>Attempt</Th><Th>Status</Th><Th>Student</Th><Th>Ticket</Th><Th>Started</Th><Th>Lab</Th><Th>Actions</Th></tr></thead><tbody>{visibleAttempts.map((attempt) => <tr key={attempt.id}><Td><Link className="font-medium text-teal-700" to={`/attempts/${attempt.id}`}>{attempt.id.slice(0, 8)}</Link></Td><Td><Badge value={attempt.status} /></Td><Td>{attempt.student_id.slice(0, 8)}</Td><Td>{attempt.ticket_id.slice(0, 8)}</Td><Td>{formatDate(attempt.started_at)}</Td><Td><Link className="text-teal-700" to={`/labs/${attempt.lab_instance_id}`}>Open lab</Link></Td><Td>{user?.role !== "STUDENT" && <button className="inline-flex min-h-9 items-center rounded-md bg-red-800 px-3 py-2 text-sm font-medium text-white hover:bg-red-900" onClick={() => hardDelete(attempt)}>Delete</button>}</Td></tr>)}</tbody></Table>{visibleAttempts.length === 0 && !error && <EmptyState title="No attempts found" description={user?.role === "STUDENT" ? "Open a published ticket and start an attempt to create a linked lab." : "No student attempts match this filter."} />}</Card></div>;
}
