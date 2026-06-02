import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { CopyId } from "../../components/ui/CopyId";
import { LoadingState } from "../../components/ui/LoadingState";
import { PageHeader } from "../../components/ui/PageHeader";
import { TopologyDiagram } from "../../components/topology/TopologyDiagram";
import { LabTemplate } from "../../types/labTemplate";
import { Topology } from "../../types/topology";
import { api } from "../../lib/api";
import { Alert } from "../../components/ui/Alert";

export function LabTemplateDetailPage() {
  const { id } = useParams();
  const [template, setTemplate] = useState<LabTemplate | null>(null);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [topologyError, setTopologyError] = useState("");
  useEffect(() => {
    api<LabTemplate>(`/api/v1/lab-templates/${id}`).then(setTemplate);
    api<Topology>(`/api/v1/lab-templates/${id}/topology`).then(setTopology).catch(() => setTopologyError("Could not parse topology."));
  }, [id]);
  if (!template) return <LoadingState message="Loading lab template..." />;
  return <div className="space-y-4">
    <PageHeader title={template.name} subtitle={template.description} action={<CopyId id={template.id} label="Template ID" />} />
    <Card title="Template Metadata">
      <div className="flex flex-wrap gap-2 text-sm">
        <Badge value={template.category} />
        <Badge value={template.difficulty} />
        <Badge value={template.is_active ? "ACTIVE" : "INACTIVE"} />
        <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">{template.estimated_memory_mb} MB</span>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">{template.estimated_duration_minutes} min</span>
      </div>
    </Card>
    <Card title="Topology" subtitle="Read-only topology parsed from Containerlab YAML. Node click shows details only.">
      {topologyError && <Alert message={topologyError} />}
      {topology && topology.warnings.length > 0 && <div className="mb-3 space-y-2">{topology.warnings.map((warning) => <Alert key={warning} className="border-amber-200 bg-amber-50 text-amber-900" message={warning} />)}</div>}
      {topology && <TopologyDiagram topology={topology} />}
    </Card>
    <Card title="Containerlab YAML" subtitle="Stored template content; validation happens server-side.">
      <pre className="overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-50">{template.containerlab_yaml}</pre>
    </Card>
  </div>;
}
