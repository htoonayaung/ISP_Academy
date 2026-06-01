import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
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
import { Lab, LabEvent, LabNode } from "../../types/lab";
import { labApi } from "./labApi";

export function LabDetailPage() {
  const { id = "" } = useParams();
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
    } catch (err) { setError(err instanceof Error ? err.message : "Lab action failed"); }
    finally { setActioning(false); }
  }
  if (!lab && !error) return <Spinner />;
  return <div className="space-y-4">
    {lab && <PageHeader title={lab.lab_name} subtitle="Manage the lab lifecycle and inspect node/event state." action={<CopyId id={lab.id} label="Lab ID" />} />}
    {error && <Alert message={error} />}
    {lab && <Card title={lab.lab_name} action={<Badge value={lab.status} />}>
      <div className="flex flex-wrap gap-2">
        <Button disabled={actioning || !canStartLab(lab.status)} onClick={() => action(labApi.start)}>Start</Button>
        <Button disabled={actioning || !canStopLab(lab.status)} onClick={() => action(labApi.stop)}>Stop</Button>
        <Button disabled={actioning || !canDestroyLab(lab.status)} className="bg-rose-700 hover:bg-rose-800" onClick={() => confirm("Destroy lab?") && action(labApi.destroy)}>Destroy</Button>
      </div>
      {["STARTING", "STOPPING", "DESTROYING"].includes(lab.status) && <p className="mt-3 text-sm text-amber-700">This lab is changing state. The page will refresh automatically.</p>}
      {lab.last_error && <p className="mt-3 text-sm text-rose-700">{lab.last_error}</p>}
    </Card>}
    <Card title="Nodes" subtitle="Lab-owned nodes only; no production network targets."><Table><thead><tr><Th>Name</Th><Th>Kind</Th><Th>Status</Th><Th>Management IPv4</Th></tr></thead><tbody>{nodes.map((node) => <tr key={node.id}><Td>{node.name}</Td><Td>{node.kind}</Td><Td><Badge value={node.status.toUpperCase()} /></Td><Td>{node.management_ipv4 || "-"}</Td></tr>)}</tbody></Table>{nodes.length === 0 && <EmptyState title="No nodes reported yet" description="Start the lab and wait until it is RUNNING to see node status." />}</Card>
    <Card title="Events" subtitle="Student-visible events are sanitized by the backend."><Table><thead><tr><Th>Type</Th><Th>Message</Th><Th>Output</Th><Th>Time</Th></tr></thead><tbody>{events.map((event) => <tr key={event.id}><Td>{event.event_type}</Td><Td>{event.message}</Td><Td><pre className="max-h-24 max-w-md overflow-auto whitespace-pre-wrap text-xs text-slate-600">{event.stdout || event.stderr || "-"}</pre></Td><Td>{formatDate(event.created_at)}</Td></tr>)}</tbody></Table>{events.length === 0 && <EmptyState title="No events yet" description="Lifecycle events will appear here after start, stop, or destroy actions." />}</Card>
  </div>;
}
