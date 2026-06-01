import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Table, Td, Th } from "../../components/ui/Table";
import { Lab } from "../../types/lab";
import { labApi } from "./labApi";

export function MyLabsPage() {
  const [labs, setLabs] = useState<Lab[]>([]);
  useEffect(() => { labApi.list().then(setLabs); }, []);
  return <Card title="Labs"><Table><thead><tr><Th>Name</Th><Th>Status</Th><Th>Created</Th></tr></thead><tbody>
    {labs.map((lab) => <tr key={lab.id}><Td><Link className="font-medium text-teal-700" to={`/labs/${lab.id}`}>{lab.lab_name}</Link></Td><Td><Badge value={lab.status} /></Td><Td>{new Date(lab.created_at).toLocaleString()}</Td></tr>)}
  </tbody></Table>{labs.length === 0 && <p className="mt-3 text-sm text-slate-500">No labs yet.</p>}</Card>;
}
