import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { Lab } from "../../types/lab";
import { TicketAttempt } from "../../types/ticket";
import { VerificationRun } from "../../types/verification";

export function AttemptDetailPage() {
  const { id = "" } = useParams();
  const [attempt, setAttempt] = useState<TicketAttempt | null>(null);
  const [lab, setLab] = useState<Lab | null>(null);
  const [runs, setRuns] = useState<VerificationRun[]>([]);
  const [message, setMessage] = useState("");
  async function load() {
    const current = await api<TicketAttempt>(`/api/v1/my/attempts/${id}`);
    setAttempt(current);
    setLab(await api<Lab>(`/api/v1/labs/${current.lab_instance_id}`));
    setRuns(await api<VerificationRun[]>(`/api/v1/my/attempts/${id}/verification-runs`));
  }
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!runs.some((run) => ["QUEUED", "RUNNING"].includes(run.status))) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [runs.map((run) => run.status).join(",")]);
  async function verify() {
    setMessage("");
    try { await api(`/api/v1/my/attempts/${id}/verify`, { method: "POST" }); await load(); } catch (err) { setMessage(err instanceof Error ? err.message : "Verification failed"); }
  }
  if (!attempt || !lab) return null;
  return <div className="space-y-4">
    <Card title={`Attempt ${attempt.id.slice(0, 8)}`} action={<Badge value={attempt.status} />}>
      <div className="flex flex-wrap items-center gap-3"><Link className="text-teal-700" to={`/labs/${lab.id}`}>Open linked lab</Link><Badge value={lab.status} /></div>
      {lab.status !== "RUNNING" && <p className="mt-3 text-sm text-amber-700">Start the lab before running verification.</p>}
      {message && <p className="mt-3 text-sm text-rose-700">{message}</p>}
      <Button className="mt-3" disabled={lab.status !== "RUNNING"} onClick={verify}>Run verification</Button>
    </Card>
    <Card title="Verification Runs"><Table><thead><tr><Th>Run</Th><Th>Status</Th><Th>Results</Th></tr></thead><tbody>{runs.map((run) => <tr key={run.id}><Td><Link className="text-teal-700" to={`/verification-runs/${run.id}`}>{run.id.slice(0, 8)}</Link></Td><Td><Badge value={run.status} /></Td><Td>{run.results?.length || 0}</Td></tr>)}</tbody></Table></Card>
  </div>;
}
