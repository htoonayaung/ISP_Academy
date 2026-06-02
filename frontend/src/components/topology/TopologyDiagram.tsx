import { useMemo, useState } from "react";
import type React from "react";
import { Monitor, Router, SwitchCamera } from "lucide-react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { Topology, TopologyNode } from "../../types/topology";

interface PositionedNode extends TopologyNode {
  x: number;
  y: number;
}

export function TopologyDiagram({
  topology,
  canOpenConsole,
  onOpenConsole,
  labRunning = false
}: {
  topology: Topology;
  canOpenConsole?: (node: TopologyNode) => boolean;
  onOpenConsole?: (node: TopologyNode) => void;
  labRunning?: boolean;
}) {
  const [selectedId, setSelectedId] = useState(topology.nodes[0]?.id || "");
  const positioned = useMemo(() => layoutNodes(topology.nodes), [topology.nodes]);
  const selected = positioned.find((node) => node.id === selectedId) || positioned[0] || null;

  if (topology.nodes.length === 0) {
    return <EmptyState title="No topology data available." description="This lab does not have normalized node data yet." />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
        <svg viewBox="0 0 900 460" role="img" aria-label="Read-only topology diagram" className="h-[420px] w-full">
          <defs>
            <marker id="dot" markerWidth="8" markerHeight="8" refX="4" refY="4">
              <circle cx="4" cy="4" r="3" fill="#64748b" />
            </marker>
          </defs>
          {topology.links.map((link) => {
            const source = positioned.find((node) => node.id === link.source);
            const target = positioned.find((node) => node.id === link.target);
            if (!source || !target) return null;
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            return (
              <g key={link.id}>
                <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#64748b" strokeWidth="3" markerStart="url(#dot)" markerEnd="url(#dot)" />
                <title>{link.label}{link.subnet ? ` ${link.subnet}` : ""}</title>
                <rect x={midX - 80} y={midY - 14} width="160" height="28" rx="6" fill="#ffffff" stroke="#cbd5e1" />
                <text x={midX} y={midY + 4} textAnchor="middle" className="fill-slate-600 text-[12px]">{link.subnet || link.label}</text>
              </g>
            );
          })}
          {positioned.map((node) => {
            const selectedNode = selected?.id === node.id;
            return (
              <g key={node.id} className="cursor-pointer" onClick={() => setSelectedId(node.id)}>
                <rect x={node.x - 76} y={node.y - 44} width="152" height="88" rx="8" fill={selectedNode ? "#ccfbf1" : "#ffffff"} stroke={selectedNode ? "#0f766e" : "#cbd5e1"} strokeWidth={selectedNode ? "3" : "2"} />
                <text x={node.x} y={node.y - 8} textAnchor="middle" className="fill-slate-950 text-[16px] font-semibold">{node.label}</text>
                <text x={node.x} y={node.y + 16} textAnchor="middle" className="fill-slate-500 text-[12px]">{node.kind}{node.role ? ` / ${node.role}` : ""}</text>
                {node.status && <text x={node.x} y={node.y + 36} textAnchor="middle" className="fill-emerald-700 text-[11px]">{node.status}</text>}
              </g>
            );
          })}
        </svg>
      </div>
      <NodeDetail
        node={selected}
        links={topology.links.filter((link) => selected && (link.source === selected.id || link.target === selected.id))}
        canOpenConsole={canOpenConsole}
        onOpenConsole={onOpenConsole}
        labRunning={labRunning}
      />
    </div>
  );
}

function NodeDetail({
  node,
  links,
  canOpenConsole,
  onOpenConsole,
  labRunning
}: {
  node: PositionedNode | null;
  links: Topology["links"];
  canOpenConsole?: (node: TopologyNode) => boolean;
  onOpenConsole?: (node: TopologyNode) => void;
  labRunning: boolean;
}) {
  if (!node) return <EmptyState title="No node selected" description="Click a node to inspect details." />;
  const Icon = iconForKind(node.kind);
  return (
    <aside className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-slate-100"><Icon size={18} /></span>
        <div>
          <h3 className="text-base font-semibold text-slate-950">{node.label}</h3>
          <p className="text-sm text-slate-500">{node.kind}</p>
        </div>
      </div>
      <div className="space-y-3 text-sm">
        {node.status && <Detail label="Status" value={<Badge value={node.status} />} />}
        <Detail label="Role" value={node.role || "-"} />
        <Detail label="Management IP" value={node.management_ipv4 || "-"} />
        <Detail label="Image" value={node.image || "-"} />
        {node.container_name && <Detail label="Container" value={node.container_name} />}
        <Detail label="Interfaces" value={links.length ? links.map((link) => link.source === node.id ? link.source_interface : link.target_interface).filter(Boolean).join(", ") : "-"} />
      </div>
      {onOpenConsole && canOpenConsole?.(node) ? (
        <Button className="mt-4 w-full" disabled={!labRunning} onClick={() => onOpenConsole(node)}>
          {labRunning ? "Open Console" : "Start the lab before opening console."}
        </Button>
      ) : (
        <Button className="mt-4 w-full bg-slate-200 text-slate-600 hover:bg-slate-200" disabled>
          Console unavailable for this node.
        </Button>
      )}
    </aside>
  );
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return <div><div className="text-xs uppercase text-slate-400">{label}</div><div className="mt-1 break-words text-slate-800">{value}</div></div>;
}

function layoutNodes(nodes: TopologyNode[]): PositionedNode[] {
  const count = Math.max(nodes.length, 1);
  const centerX = 450;
  const centerY = 230;
  const radius = count <= 2 ? 170 : 165;
  return nodes.map((node, index) => {
    if (count === 1) return { ...node, x: centerX, y: centerY };
    if (count === 2) return { ...node, x: index === 0 ? 260 : 640, y: centerY };
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
    return { ...node, x: centerX + radius * Math.cos(angle), y: centerY + radius * Math.sin(angle) };
  });
}

function iconForKind(kind: string) {
  const normalized = kind.toLowerCase();
  if (normalized.includes("frr") || normalized.includes("router")) return Router;
  if (normalized.includes("linux") || normalized.includes("host")) return Monitor;
  return SwitchCamera;
}
