import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Spinner } from "../../components/ui/Spinner";
import { LabTemplate } from "../../types/labTemplate";
import { api } from "../../lib/api";

export function LabTemplateDetailPage() {
  const { id } = useParams();
  const [template, setTemplate] = useState<LabTemplate | null>(null);
  useEffect(() => { api<LabTemplate>(`/api/v1/lab-templates/${id}`).then(setTemplate); }, [id]);
  if (!template) return <Spinner />;
  return <Card title={template.name}><p className="mb-3 text-sm text-slate-600">{template.description}</p><pre className="overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-50">{template.containerlab_yaml}</pre></Card>;
}
