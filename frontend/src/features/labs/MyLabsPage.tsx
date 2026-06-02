import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Select } from "../../components/ui/Select";
import { Table, Td, Th } from "../../components/ui/Table";
import { Alert } from "../../components/ui/Alert";
import { canDestroyLab, canStartLab, canStopLab, formatDate } from "../../lib/format";
import { Lab } from "../../types/lab";
import { labApi } from "./labApi";

export function MyLabsPage() {
  const [labs, setLabs] = useState<Lab[]>([]);
  const [filter, setFilter] = useState("ALL");
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");
  async function load() {
    try { setError(""); setLabs(await labApi.list()); }
    catch (err) { setError(err instanceof Error ? err.message : "Failed to load labs"); }
  }
  useEffect(() => { load(); }, []);
  async function run(lab: Lab, action: "start" | "stop" | "destroy") {
    if (action === "destroy" && !confirm(`Destroy lab ${lab.lab_name}?`)) return;
    try {
      setBusyId(lab.id); setError("");
      if (action === "start") await labApi.start(lab.id);
      if (action === "stop") await labApi.stop(lab.id);
      if (action === "destroy") await labApi.destroy(lab.id);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Lab action failed"); }
    finally { setBusyId(""); }
  }
  const visibleLabs = labs.filter((lab) => {
    if (filter === "ALL") return true;
    if (filter === "RUNNING") return lab.status === "RUNNING";
    if (filter === "READY") return ["CREATED", "STOPPED"].includes(lab.status);
    if (filter === "FAILED") return lab.status === "FAILED";
    if (filter === "DESTROYED") return lab.status === "DESTROYED";
    return true;
  });
  return <div className="space-y-4">
    <PageHeader title="My Labs" subtitle="Open, start, stop, or destroy lab instances owned by your account. Admins can inspect all labs." />
    <Card title="Labs" subtitle="Running labs consume server resources. Destroy demo labs when finished." action={<div className="flex items-center gap-2"><Select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="ALL">All</option><option value="RUNNING">Running</option><option value="READY">Created/Stopped</option><option value="FAILED">Failed</option><option value="DESTROYED">Destroyed</option></Select><Button onClick={load}>Refresh</Button></div>}>
      {error && <div className="mb-3"><Alert message={error} /></div>}
      <Table><thead><tr><Th>Name</Th><Th>Status</Th><Th>Created</Th><Th>Actions</Th></tr></thead><tbody>
    {visibleLabs.map((lab) => <tr key={lab.id}><Td><Link className="font-medium text-teal-700" to={`/labs/${lab.id}`}>{lab.lab_name}</Link></Td><Td><Badge value={lab.status} /></Td><Td>{formatDate(lab.created_at)}</Td><Td><div className="flex flex-wrap gap-2"><Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to={`/labs/${lab.id}`}>View</Link><Button disabled={busyId === lab.id || !canStartLab(lab.status)} onClick={() => run(lab, "start")}>Start</Button><Button disabled={busyId === lab.id || !canStopLab(lab.status)} onClick={() => run(lab, "stop")}>Stop</Button><Button disabled={busyId === lab.id || !canDestroyLab(lab.status)} className="bg-rose-700 hover:bg-rose-800" onClick={() => run(lab, "destroy")}>Destroy</Button></div></Td></tr>)}
  </tbody></Table>{visibleLabs.length === 0 && <EmptyState title="No labs found" description="Adjust the filter or start a published ticket attempt to create a linked lab." />}</Card>
  </div>;
}
