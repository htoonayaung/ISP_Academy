import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { Spinner } from "../../components/ui/Spinner";
import { CopyId } from "../../components/ui/CopyId";
import { EmptyState } from "../../components/ui/EmptyState";
import { Input } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { TopologyDiagram } from "../../components/topology/TopologyDiagram";
import { canDestroyLab, canStartLab, canStopLab, formatDate } from "../../lib/format";
import { ApiRequestError } from "../../lib/api";
import { Lab, LabEvent, LabNode } from "../../types/lab";
import { ConsoleNode, ConsoleResult } from "../../types/console";
import { Topology, TopologyNode } from "../../types/topology";
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
  const [topology, setTopology] = useState<Topology | null>(null);
  const [topologyError, setTopologyError] = useState("");
  const [consoleNodes, setConsoleNodes] = useState<ConsoleNode[]>([]);
  const [selectedConsoleNode, setSelectedConsoleNode] = useState<ConsoleNode | null>(null);
  const [consoleCommand, setConsoleCommand] = useState("show ip route");
  const [consoleResult, setConsoleResult] = useState<ConsoleResult | null>(null);
  const [consoleBusy, setConsoleBusy] = useState(false);
  const [consoleError, setConsoleError] = useState("");
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
    try {
      setTopology(await labApi.topology(id));
      setTopologyError("");
    } catch {
      setTopologyError("Could not parse topology.");
      setTopology(null);
    }
    try {
      const response = await labApi.consoleNodes(id);
      setConsoleNodes(response.nodes);
    } catch {
      setConsoleNodes([]);
    }
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
  function openConsole(node: TopologyNode) {
    const consoleNode = consoleNodes.find((item) => item.name === node.id || item.name === node.label);
    if (!consoleNode) {
      setConsoleError("Console not available for this node");
      return;
    }
    setSelectedConsoleNode(consoleNode);
    setConsoleError("");
    setConsoleResult(null);
  }
  async function runConsole(command = consoleCommand) {
    if (!selectedConsoleNode) return;
    try {
      setConsoleBusy(true);
      setConsoleError("");
      setConsoleResult(await labApi.executeConsole(id, selectedConsoleNode.id, command));
      setConsoleCommand(command);
    } catch (err) {
      setConsoleError(err instanceof Error ? err.message : "Console command failed");
    } finally {
      setConsoleBusy(false);
    }
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
    <Card title="Topology" subtitle="Read-only topology with runtime node status. Open Console is available only for console-capable nodes in running labs.">
      {topologyError && <Alert message={topologyError} />}
      {topology?.warnings.map((warning) => <div className="mb-2" key={warning}><Alert className="border-amber-200 bg-amber-50 text-amber-900" message={warning} /></div>)}
      {topology ? <TopologyDiagram topology={topology} labRunning={lab?.status === "RUNNING"} canOpenConsole={(node) => consoleNodes.some((item) => item.name === node.id || item.name === node.label)} onOpenConsole={openConsole} /> : <EmptyState title="No topology data available." description="Topology appears after the lab template can be parsed." />}
    </Card>
    <Card title="FRR Router CLI" subtitle="Commands run inside your lab router only. Host access is not provided.">
      {lab?.status !== "RUNNING" && <Alert className="border-amber-200 bg-amber-50 text-amber-900" message="Start the lab before opening console." />}
      {consoleError && <div className="mb-3"><Alert message={consoleError} /></div>}
      {!selectedConsoleNode ? <EmptyState title="No console node selected" description="Click a console-capable node in the topology and choose Open Console." /> : <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2 text-sm"><span className="font-medium">{selectedConsoleNode.name}</span><Badge value={selectedConsoleNode.console_type} /><Badge value={selectedConsoleNode.status} /></div>
        <div className="flex flex-wrap gap-2">
          {["show ip route", "show ip ospf neighbor", "show bgp summary", "show running-config"].map((command) => <Button key={command} disabled={consoleBusy || lab?.status !== "RUNNING"} onClick={() => runConsole(command)}>{command}</Button>)}
        </div>
        <div className="flex gap-2">
          <Input value={consoleCommand} onChange={(event) => setConsoleCommand(event.target.value)} placeholder="show ip route" />
          <Button disabled={consoleBusy || lab?.status !== "RUNNING"} onClick={() => runConsole()}>Run</Button>
        </div>
        {consoleResult && <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2 text-sm"><Badge value={consoleResult.status.toUpperCase()} /><span>exit {consoleResult.exit_code}</span><span>{consoleResult.duration_ms} ms</span><Button className="bg-slate-200 text-slate-900 hover:bg-slate-300" onClick={() => navigator.clipboard?.writeText(`${consoleResult.stdout}${consoleResult.stderr}`)}>Copy output</Button></div>
          <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-50">{consoleResult.stdout || consoleResult.stderr || "No output"}</pre>
        </div>}
      </div>}
    </Card>
    <Card title="Nodes" subtitle="Lab-owned nodes only; no production network targets."><Table><thead><tr><Th>Name</Th><Th>Kind</Th><Th>Status</Th><Th>Management IPv4</Th></tr></thead><tbody>{nodes.map((node) => <tr key={node.id}><Td>{node.name}</Td><Td>{node.kind}</Td><Td><Badge value={node.status.toUpperCase()} /></Td><Td>{node.management_ipv4 || "-"}</Td></tr>)}</tbody></Table>{nodes.length === 0 && <EmptyState title="No nodes reported yet" description="Start the lab and wait until it is RUNNING to see node status." />}</Card>
    <Card title="Events" subtitle="Student-visible events are sanitized by the backend."><Table><thead><tr><Th>Type</Th><Th>Message</Th><Th>Output</Th><Th>Time</Th></tr></thead><tbody>{events.map((event) => <tr key={event.id}><Td>{event.event_type}</Td><Td>{event.message}</Td><Td><pre className="max-h-24 max-w-md overflow-auto whitespace-pre-wrap text-xs text-slate-600">{event.stdout || event.stderr || "-"}</pre></Td><Td>{formatDate(event.created_at)}</Td></tr>)}</tbody></Table>{events.length === 0 && <EmptyState title="No events yet" description="Lifecycle events will appear here after start, stop, or destroy actions." />}</Card>
  </div>;
}
