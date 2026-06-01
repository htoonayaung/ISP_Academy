import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Table, Td, Th } from "../../components/ui/Table";
import { api } from "../../lib/api";
import { Ticket } from "../../types/ticket";

export function VerificationRulesIndexPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Ticket[]>("/api/v1/tickets")
      .then(setTickets)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load tickets"));
  }, []);

  return (
    <Card title="Verification Rules">
      {error && <div className="mb-3"><Alert message={error} /></div>}
      <Table>
        <thead><tr><Th>Ticket</Th><Th>Status</Th><Th>Rules</Th></tr></thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr key={ticket.id}>
              <Td>{ticket.title}</Td>
              <Td><Badge value={ticket.status} /></Td>
              <Td><Link className="font-medium text-teal-700" to={`/tickets/${ticket.id}/verification-rules`}>Manage rules</Link></Td>
            </tr>
          ))}
        </tbody>
      </Table>
      {tickets.length === 0 && !error && <p className="mt-3 text-sm text-slate-500">No tickets found.</p>}
    </Card>
  );
}
