import { Link } from "react-router-dom";
import { Card } from "../../components/ui/Card";

export function UnauthorizedPage() {
  return <Card title="Unauthorized"><p className="mb-3 text-sm text-slate-600">Your role cannot access this page.</p><Link className="text-teal-700" to="/dashboard">Back to dashboard</Link></Card>;
}
