import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { Spinner } from "../../components/ui/Spinner";
import { CopyId } from "../../components/ui/CopyId";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { VerificationRun } from "../../types/verification";

export function VerificationRunPage() {
  const { id = "" } = useParams();
  const [run, setRun] = useState<VerificationRun | null>(null);
  const [error, setError] = useState("");
  async function load() {
    try {
      setError("");
      setRun(await api<VerificationRun>(`/api/v1/my/verification-runs/${id}`));
    } catch (err) { setError(err instanceof Error ? err.message : "Failed to load verification run"); }
  }
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!run || !["QUEUED", "RUNNING"].includes(run.status)) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [run?.status, id]);
  if (!run && !error) return <Spinner />;
  if (!run) return <Alert message={error} />;
  return <div className="space-y-4">
  <PageHeader title={`Verification ${run.id.slice(0, 8)}`} subtitle="Review per-rule verification results for this attempt." action={<CopyId id={run.id} label="Run ID" />} />
  <Card title="Verification Results" subtitle="PASSED, FAILED, or ERROR is shown for each rule." action={<Badge value={run.status} />}>
    {error && <div className="mb-3"><Alert message={error} /></div>}
    {["QUEUED", "RUNNING"].includes(run.status) && <div className="mb-3 rounded-md bg-sky-50 px-3 py-2 text-sm text-sky-800">Verification is queued or running. Results will refresh automatically.</div>}
    {run.status === "PASSED" && <div className="mb-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">Great! Your lab passed verification.</div>}
    {run.status === "FAILED" && <div className="mb-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">Some checks failed. Review the result and try again.</div>}
    {run.status === "ERROR" && <div className="mb-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">Verification hit an error. Review the message below or ask an instructor.</div>}
    <Table><thead><tr><Th>Rule</Th><Th>Status</Th><Th>Message</Th><Th>Created</Th></tr></thead><tbody>{run.results.map((result) => <tr key={result.id}><Td>{result.verification_rule_id.slice(0, 8)}</Td><Td><Badge value={result.status} /></Td><Td>{result.message}</Td><Td>{formatDate(result.created_at)}</Td></tr>)}</tbody></Table>
    {run.results.length === 0 && <EmptyState title="No rule results yet" description="Queued or running verification tasks will populate this table shortly." />}
  </Card>
  </div>;
}
