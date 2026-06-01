import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { VerificationRun } from "../../types/verification";

export function VerificationRunPage() {
  const { id = "" } = useParams();
  const [run, setRun] = useState<VerificationRun | null>(null);
  useEffect(() => { api<VerificationRun>(`/api/v1/my/verification-runs/${id}`).then(setRun); }, [id]);
  if (!run) return null;
  return <Card title={`Verification ${run.id.slice(0, 8)}`} action={<Badge value={run.status} />}>
    <Table><thead><tr><Th>Rule</Th><Th>Status</Th><Th>Message</Th><Th>Created</Th></tr></thead><tbody>{run.results.map((result) => <tr key={result.id}><Td>{result.verification_rule_id.slice(0, 8)}</Td><Td><Badge value={result.status} /></Td><Td>{result.message}</Td><Td>{formatDate(result.created_at)}</Td></tr>)}</tbody></Table>
  </Card>;
}
