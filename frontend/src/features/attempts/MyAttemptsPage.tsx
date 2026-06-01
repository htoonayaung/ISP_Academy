import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { TicketAttempt } from "../../types/ticket";

export function MyAttemptsPage() {
  const [attempts, setAttempts] = useState<TicketAttempt[]>([]);
  useEffect(() => { api<TicketAttempt[]>("/api/v1/my/attempts").then(setAttempts); }, []);
  return <Card title="My Attempts"><Table><thead><tr><Th>Attempt</Th><Th>Status</Th><Th>Started</Th><Th>Lab</Th></tr></thead><tbody>{attempts.map((attempt) => <tr key={attempt.id}><Td><Link className="text-teal-700" to={`/attempts/${attempt.id}`}>{attempt.id.slice(0, 8)}</Link></Td><Td><Badge value={attempt.status} /></Td><Td>{formatDate(attempt.started_at)}</Td><Td><Link className="text-teal-700" to={`/labs/${attempt.lab_instance_id}`}>Open lab</Link></Td></tr>)}</tbody></Table></Card>;
}
