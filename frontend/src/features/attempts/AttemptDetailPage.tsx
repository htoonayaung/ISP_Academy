import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { Spinner } from "../../components/ui/Spinner";
import { CopyId } from "../../components/ui/CopyId";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { Lab } from "../../types/lab";
import { Ticket, TicketAttempt } from "../../types/ticket";
import { VerificationRun } from "../../types/verification";

function Step({ number, title, active, done }: { number: number; title: string; active?: boolean; done?: boolean }) {
  return (
    <div className={`rounded-md border p-3 text-sm ${done ? "border-emerald-200 bg-emerald-50 text-emerald-900" : active ? "border-teal-200 bg-teal-50 text-teal-900" : "border-slate-200 bg-white text-slate-600"}`}>
      <div className="text-xs font-semibold uppercase">Step {number}</div>
      <div className="mt-1 font-medium">{title}</div>
    </div>
  );
}

export function AttemptDetailPage() {
  const { id = "" } = useParams();
  const [attempt, setAttempt] = useState<TicketAttempt | null>(null);
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [lab, setLab] = useState<Lab | null>(null);
  const [runs, setRuns] = useState<VerificationRun[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function load() {
    try {
      setError("");
      const current = await api<TicketAttempt>(`/api/v1/my/attempts/${id}`);
      setAttempt(current);
      setTicket(await api<Ticket>(`/api/v1/tickets/${current.ticket_id}`));
      setLab(await api<Lab>(`/api/v1/labs/${current.lab_instance_id}`));
      setRuns(await api<VerificationRun[]>(`/api/v1/my/attempts/${id}/verification-runs`));
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load attempt"); }
  }
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!runs.some((run) => ["QUEUED", "RUNNING"].includes(run.status)) && !["STARTING", "STOPPING", "DESTROYING"].includes(lab?.status || "")) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [runs.map((run) => run.status).join(","), lab?.status]);
  async function verify() {
    setMessage("");
    try { await api(`/api/v1/my/attempts/${id}/verify`, { method: "POST" }); setMessage("Verification queued. Results will refresh automatically."); await load(); } catch (err) { setMessage(err instanceof Error ? err.message : "Verification failed"); }
  }
  if (!attempt || !lab) return error ? <Alert message={error} /> : <Spinner />;
  const latestRun = runs[0];
  const hasPassed = runs.some((run) => run.status === "PASSED");
  const hasFailed = runs.some((run) => ["FAILED", "ERROR"].includes(run.status));
  const isVerificationBusy = runs.some((run) => ["QUEUED", "RUNNING"].includes(run.status));
  return <div className="space-y-4">
    <PageHeader title={ticket ? ticket.title : `Attempt ${attempt.id.slice(0, 8)}`} subtitle="Start the linked lab, wait for RUNNING, then run verification." action={<CopyId id={attempt.id} label="Attempt ID" />} />
    {error && <Alert message={error} />}
    <Card title={`Attempt ${attempt.id.slice(0, 8)}`} subtitle={ticket ? `Linked ticket: ${ticket.title}` : "Linked ticket loading"} action={<Badge value={attempt.status} />}>
      <div className="grid gap-3 md:grid-cols-5">
        <Step number={1} title="Start lab" active={["CREATED", "STOPPED", "FAILED"].includes(lab.status)} done={["STARTING", "RUNNING", "STOPPING", "DESTROYING", "DESTROYED"].includes(lab.status)} />
        <Step number={2} title="Wait until RUNNING" active={["STARTING"].includes(lab.status)} done={lab.status === "RUNNING"} />
        <Step number={3} title="Run verification" active={lab.status === "RUNNING" && !latestRun} done={runs.length > 0} />
        <Step number={4} title="Review result" active={isVerificationBusy} done={hasPassed || hasFailed} />
        <Step number={5} title="Destroy lab" active={hasPassed || hasFailed} done={lab.status === "DESTROYED"} />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3"><Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to={`/labs/${lab.id}`}>Open Lab</Link><Badge value={lab.status} /></div>
      {lab.status !== "RUNNING" && <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">Start the linked lab before running verification.</p>}
      {isVerificationBusy && <p className="mt-3 rounded-md bg-sky-50 px-3 py-2 text-sm text-sky-800">Verification is queued or running. This page refreshes automatically.</p>}
      {hasPassed && <p className="mt-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">Great! Your lab passed verification.</p>}
      {hasFailed && <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">Some checks failed. Review the result and try again.</p>}
      {message && <p className="mt-3 text-sm text-slate-700">{message}</p>}
      <Button className="mt-3 bg-teal-700 hover:bg-teal-800" disabled={lab.status !== "RUNNING" || isVerificationBusy} onClick={verify}>{isVerificationBusy ? "Verification running..." : "Run Verification"}</Button>
    </Card>
    <Card title="Verification Runs" subtitle="Queued and running checks refresh automatically."><Table><thead><tr><Th>Run</Th><Th>Status</Th><Th>Results</Th></tr></thead><tbody>{runs.map((run) => <tr key={run.id}><Td><Link className="text-teal-700" to={`/verification-runs/${run.id}`}>{run.id.slice(0, 8)}</Link></Td><Td><Badge value={run.status} /></Td><Td>{run.results?.length || 0}</Td></tr>)}</tbody></Table>{runs.length === 0 && <EmptyState title="No verification runs yet" description="Run verification after the linked lab reaches RUNNING." />}</Card>
  </div>;
}
