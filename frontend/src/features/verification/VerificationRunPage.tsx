import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Alert } from "../../components/ui/Alert";
import { Spinner } from "../../components/ui/Spinner";
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
  return <Card title={`Verification ${run.id.slice(0, 8)}`} action={<Badge value={run.status} />}>
    {error && <div className="mb-3"><Alert message={error} /></div>}
    <Table><thead><tr><Th>Rule</Th><Th>Status</Th><Th>Message</Th><Th>Created</Th></tr></thead><tbody>{run.results.map((result) => <tr key={result.id}><Td>{result.verification_rule_id.slice(0, 8)}</Td><Td><Badge value={result.status} /></Td><Td>{result.message}</Td><Td>{formatDate(result.created_at)}</Td></tr>)}</tbody></Table>
  </Card>;
}
