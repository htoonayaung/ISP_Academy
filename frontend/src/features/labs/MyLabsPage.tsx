import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { Table, Td, Th } from "../../components/ui/Table";
import { Lab } from "../../types/lab";
import { labApi } from "./labApi";

export function MyLabsPage() {
  const [labs, setLabs] = useState<Lab[]>([]);
  useEffect(() => { labApi.list().then(setLabs); }, []);
  return <div className="space-y-4">
    <PageHeader title="My Labs" subtitle="Open, start, stop, or destroy lab instances owned by your account. Admins can inspect all labs." />
    <Card title="Labs" subtitle="Running labs consume server resources. Destroy demo labs when finished."><Table><thead><tr><Th>Name</Th><Th>Status</Th><Th>Created</Th></tr></thead><tbody>
    {labs.map((lab) => <tr key={lab.id}><Td><Link className="font-medium text-teal-700" to={`/labs/${lab.id}`}>{lab.lab_name}</Link></Td><Td><Badge value={lab.status} /></Td><Td>{new Date(lab.created_at).toLocaleString()}</Td></tr>)}
  </tbody></Table>{labs.length === 0 && <EmptyState title="No labs yet" description="Students create labs by starting a published ticket attempt." />}</Card>
  </div>;
}
