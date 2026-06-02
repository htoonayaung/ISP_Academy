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
import { canDestroyLab, canStartLab, canStopLab, formatDate } from "../../lib/format";
import { ApiRequestError } from "../../lib/api";
import { Lab, LabEvent, LabNode } from "../../types/lab";
import { useAuth } from "../auth/authStore";
import { labApi } from "./labApi";

function progressText(status: string): string {
  if (status === "STARTING") return "Lab is starting. This may take a few seconds.";
  if (status === "RUNNING") return "Lab is running. You can now run verification.";
  if (status === "STOPPING") return "Lab is stopping. Buttons are disabled until it finishes.";
  if (status === "DESTROYING") return "Lab is being cleaned up.";
  if (status === "DESTROYED") return "Lab has been destroyed.";
  if (status === "FAILED") return "Lab failed. Review events, then start again or destroy the lab.";
  return "Lab is ready. Start it when you are ready for verification.";
}

export function LabDetailPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const [lab, setLab] = useState<Lab | null>(null);
  const [nodes, setNodes] = useState<LabNode[]>([]);
  const [events, setEvents] = useState<LabEvent[]>([]);
  const [error, setError] = useState("");
  const [actioning, setActioning] = useState(false);
  async function load() {
    try {
      setError("");
      const current = await labApi.get(id);
      setLab(current);
      setNodes(await labApi.nodes(id));
      setEvents(await labApi.events(id));
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load lab"); }
  }
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!lab || !["STARTING", "STOPPING", "DESTROYING"].includes(lab.status)) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [lab?.status, id]);
  async function action(fn: (id: string) => Promise<Lab>) {
    try {
      setActioning(true);
      setError("");
      setLab(await fn(id));
      await load();
    } catch (err) {
      if (err instanceof ApiRequestError && err.status === 409) setError("This lab is already starting or running.");
      else setError(err instanceof Error ? err.message : "Lab action failed");
    }
    finally { setActioning(false); }
  }
  if (!lab && !error) return <Spinner />;
  return <div className="space-y-4">
    {lab && <PageHeader title={lab.lab_name} subtitle="Manage the lab lifecycle and inspect node/event state." action={<CopyId id={lab.id} label="Lab ID" />} />}
    {error && <Alert message={error} />}
    {lab && user?.role === "ADMIN" && ["STARTING", "STOPPING", "DESTROYING"].includes(lab.status) && <Alert className="border-amber-200 bg-amber-50 text-amber-900" message="This lab is in a transient runtime state. Use Lab Runtime if it remains stuck after refresh." />}
    {lab && <Card title={lab.lab_name} subtitle="Use the lifecycle buttons in order. State changes refresh automatically." action={<div className="text-lg"><Badge value={lab.status} /></div>}>
      <div className="flex flex-wrap gap-2">
        <Button disabled={actioning || !canStartLab(lab.status)} onClick={() => action(labApi.start)}>Start</Button>
        <Button disabled={actioning || !canStopLab(lab.status)} onClick={() => action(labApi.stop)}>Stop</Button>
        <Button disabled={actioning || !canDestroyLab(lab.status)} className="bg-rose-700 hover:bg-rose-800" onClick={() => confirm("Destroy lab?") && action(labApi.destroy)}>Destroy</Button>
        {user?.role === "ADMIN" && <Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to="/admin/runtime">Runtime Ops</Link>}
      </div>
      <p className={`mt-3 rounded-md px-3 py-2 text-sm ${lab.status === "RUNNING" ? "bg-emerald-50 text-emerald-800" : ["STARTING", "STOPPING", "DESTROYING"].includes(lab.status) ? "bg-amber-50 text-amber-800" : lab.status === "FAILED" ? "bg-rose-50 text-rose-800" : "bg-slate-50 text-slate-700"}`}>{progressText(lab.status)}</p>
      {lab.last_error && <p className="mt-3 text-sm text-rose-700">{lab.last_error}</p>}
    </Card>}
    <Card title="Nodes" subtitle="Lab-owned nodes only; no production network targets."><Table><thead><tr><Th>Name</Th><Th>Kind</Th><Th>Status</Th><Th>Management IPv4</Th></tr></thead><tbody>{nodes.map((node) => <tr key={node.id}><Td>{node.name}</Td><Td>{node.kind}</Td><Td><Badge value={node.status.toUpperCase()} /></Td><Td>{node.management_ipv4 || "-"}</Td></tr>)}</tbody></Table>{nodes.length === 0 && <EmptyState title="No nodes reported yet" description="Start the lab and wait until it is RUNNING to see node status." />}</Card>
    <Card title="Events" subtitle="Student-visible events are sanitized by the backend."><Table><thead><tr><Th>Type</Th><Th>Message</Th><Th>Output</Th><Th>Time</Th></tr></thead><tbody>{events.map((event) => <tr key={event.id}><Td>{event.event_type}</Td><Td>{event.message}</Td><Td><pre className="max-h-24 max-w-md overflow-auto whitespace-pre-wrap text-xs text-slate-600">{event.stdout || event.stderr || "-"}</pre></Td><Td>{formatDate(event.created_at)}</Td></tr>)}</tbody></Table>{events.length === 0 && <EmptyState title="No events yet" description="Lifecycle events will appear here after start, stop, or destroy actions." />}</Card>
  </div>;
}
