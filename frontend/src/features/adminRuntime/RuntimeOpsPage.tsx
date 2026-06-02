import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Input } from "../../components/ui/Input";
import { Modal } from "../../components/ui/Modal";
import { PageHeader } from "../../components/ui/PageHeader";
import { Spinner } from "../../components/ui/Spinner";
import { Table, Td, Th } from "../../components/ui/Table";
import { formatDate } from "../../lib/format";
import { RuntimeLabSummary, RuntimeStatus } from "../../types/adminRuntime";
import { adminRuntimeApi } from "./adminRuntimeApi";

type RecoverAction = "mark_failed" | "retry_destroy" | "force_destroy_demo_only";

interface PendingAction {
  type: "recover" | "cleanup";
  action?: RecoverAction;
  lab?: RuntimeLabSummary;
}

const actionLabels: Record<RecoverAction, string> = {
  mark_failed: "Mark failed",
  retry_destroy: "Retry destroy",
  force_destroy_demo_only: "Force destroy demo"
};

export function RuntimeOpsPage() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [selectedLabId, setSelectedLabId] = useState("");
  const [events, setEvents] = useState<RuntimeStatusEvent[]>([]);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setError("");
      setStatus(await adminRuntimeApi.status());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Runtime status failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const allLabs = useMemo(() => {
    if (!status) return [];
    return Object.values(status.labs_by_status).flat().sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  }, [status]);

  async function refresh() {
    try {
      setBusy(true);
      setError("");
      const result = await adminRuntimeApi.refresh();
      setMessage(`Refresh queued for ${result.queued_refresh_count} labs.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setBusy(false);
    }
  }

  async function showEvents(labId: string) {
    try {
      setSelectedLabId(labId);
      const result = await adminRuntimeApi.events(labId);
      setEvents(result.events);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load runtime events");
    }
  }

  async function runPending() {
    if (!pending) return;
    try {
      setBusy(true);
      setError("");
      setMessage("");
      if (pending.type === "cleanup") {
        const result = await adminRuntimeApi.cleanupDemo(confirmation);
        setMessage(result.message);
      } else if (pending.lab && pending.action) {
        const result = await adminRuntimeApi.recover(pending.lab.id, pending.action, confirmation);
        setMessage(result.message);
      }
      setPending(null);
      setConfirmation("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Runtime action failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Spinner />;

  return <div className="space-y-4">
    <PageHeader title="Lab Runtime" subtitle="Inspect stuck labs, queue safe recovery, and clean demo runtime artifacts." action={<Button disabled={busy} onClick={refresh}>Refresh</Button>} />
    {error && <Alert message={error} />}
    {message && <Alert className="border-emerald-200 bg-emerald-50 text-emerald-800" message={message} />}
    {status && <RuntimeSummary status={status} />}
    {status?.warnings.map((warning) => <Alert key={warning} className="border-amber-200 bg-amber-50 text-amber-900" message={warning} />)}
    {status && <Card title="Lab Status" subtitle="Refresh queues worker-side inspection. Actions are confirmation protected.">
      <Table>
        <thead><tr><Th>Lab name</Th><Th>Owner</Th><Th>Status</Th><Th>Created</Th><Th>Updated</Th><Th>Demo</Th><Th>Containers</Th><Th>Warning</Th><Th>Actions</Th></tr></thead>
        <tbody>{allLabs.map((lab) => <tr key={lab.id}>
          <Td><Link className="font-medium text-teal-700" to={`/labs/${lab.id}`}>{lab.lab_name}</Link></Td>
          <Td><span className="font-mono text-xs">{lab.owner_id.slice(0, 8)}</span></Td>
          <Td><Badge value={lab.status} /></Td>
          <Td>{formatDate(lab.created_at)}</Td>
          <Td>{formatDate(lab.updated_at)}</Td>
          <Td>{lab.is_demo ? "Yes" : "No"}</Td>
          <Td>{lab.has_containers ? "Known" : "-"}</Td>
          <Td>{lab.warning || "-"}</Td>
          <Td><div className="flex flex-wrap gap-2">
            <Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to={`/labs/${lab.id}`}>View lab</Link>
            <Button disabled={busy || !lab.warning} onClick={() => setPending({ type: "recover", action: "mark_failed", lab })}>Mark failed</Button>
            <Button disabled={busy || lab.status === "DESTROYED"} onClick={() => setPending({ type: "recover", action: "retry_destroy", lab })}>Retry destroy</Button>
            <Button disabled={busy || !lab.is_demo || lab.status === "DESTROYED"} className="bg-rose-700 hover:bg-rose-800" onClick={() => setPending({ type: "recover", action: "force_destroy_demo_only", lab })}>Force demo</Button>
            <Button disabled={busy} className="bg-slate-700 hover:bg-slate-800" onClick={() => showEvents(lab.id)}>Events</Button>
          </div></Td>
        </tr>)}</tbody>
      </Table>
      {allLabs.length === 0 && <EmptyState title="No labs found" description="Runtime operations will appear after labs are created." />}
    </Card>}
    <Card title="Stuck Labs" subtitle="STARTING, STOPPING, or DESTROYING longer than the configured threshold.">
      <RuntimeLabList labs={status?.stuck_candidates || []} />
    </Card>
    <Card title="Orphan / Demo Cleanup" subtitle="Cleanup is restricted to demo-prefixed destroyed or failed runtime artifacts. If unsure, use Refresh first.">
      <div className="space-y-3">
        <p className="text-sm text-slate-700">This does not affect non-demo active labs.</p>
        {status?.orphan_candidates.length ? <ul className="space-y-2 text-sm text-amber-800">{status.orphan_candidates.map((orphan) => <li key={orphan.path}>{orphan.warning}</li>)}</ul> : <p className="text-sm text-slate-500">No orphan runtime directories reported.</p>}
        <Button disabled={busy} className="bg-rose-700 hover:bg-rose-800" onClick={() => setPending({ type: "cleanup" })}>Cleanup demo runtime</Button>
      </div>
    </Card>
    <Card title="Events" subtitle="Recent lifecycle, worker, and recovery events for the selected lab.">
      {!selectedLabId && <EmptyState title="No lab selected" description="Choose Events from the lab table." />}
      {selectedLabId && <Table><thead><tr><Th>Type</Th><Th>Message</Th><Th>Output</Th><Th>Time</Th></tr></thead><tbody>{events.map((event) => <tr key={event.id}><Td>{event.event_type}</Td><Td>{event.message}</Td><Td><pre className="max-h-24 max-w-lg overflow-auto whitespace-pre-wrap text-xs">{event.stdout || event.stderr || "-"}</pre></Td><Td>{formatDate(event.created_at)}</Td></tr>)}</tbody></Table>}
    </Card>
    {pending && <Modal title={pending.type === "cleanup" ? "Confirm demo cleanup" : `Confirm ${pending.action ? actionLabels[pending.action] : "recovery"}`} onClose={() => { setPending(null); setConfirmation(""); }}>
      <div className="space-y-4">
        <Alert className="border-amber-200 bg-amber-50 text-amber-900" message={pending.type === "cleanup" ? "Type CLEANUP_DEMO_RUNTIME. This does not affect non-demo active labs." : "Type RECOVER_LAB. If unsure, use Refresh first."} />
        {pending.lab && <p className="text-sm text-slate-700">Target lab: <span className="font-medium">{pending.lab.lab_name}</span></p>}
        <Input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder={pending.type === "cleanup" ? "CLEANUP_DEMO_RUNTIME" : "RECOVER_LAB"} />
        <div className="flex gap-2">
          <Button disabled={busy} onClick={runPending}>Confirm</Button>
          <Button className="bg-slate-200 text-slate-900 hover:bg-slate-300" onClick={() => { setPending(null); setConfirmation(""); }}>Cancel</Button>
        </div>
      </div>
    </Modal>}
  </div>;
}

interface RuntimeStatusEvent {
  id: string;
  event_type: string;
  message: string;
  stdout: string | null;
  stderr: string | null;
  created_at: string;
}

function RuntimeSummary({ status }: { status: RuntimeStatus }) {
  const stuck = status.stuck_candidates.length;
  const destroyed = status.status_counts.DESTROYED || 0;
  const demo = status.demo_labs.length;
  const orphan = status.orphan_candidates.length;
  return <div className="grid gap-3 md:grid-cols-5">
    <Metric label="Running labs" value={status.status_counts.RUNNING || 0} />
    <Metric label="Stuck labs" value={stuck} />
    <Metric label="Destroyed labs" value={destroyed} />
    <Metric label="Demo labs" value={demo} />
    <Metric label="Orphan candidates" value={orphan} />
  </div>;
}

function Metric({ label, value }: { label: string; value: number }) {
  return <Card title={label}><div className="text-2xl font-semibold text-slate-950">{value}</div></Card>;
}

function RuntimeLabList({ labs }: { labs: RuntimeLabSummary[] }) {
  if (labs.length === 0) return <EmptyState title="No stuck labs" description="Transient lab states are currently within the expected window." />;
  return <Table><thead><tr><Th>Lab</Th><Th>Status</Th><Th>Updated</Th><Th>Warning</Th></tr></thead><tbody>{labs.map((lab) => <tr key={lab.id}><Td>{lab.lab_name}</Td><Td><Badge value={lab.status} /></Td><Td>{formatDate(lab.updated_at)}</Td><Td>{lab.warning || "-"}</Td></tr>)}</tbody></Table>;
}
