import { Link } from "react-router-dom";
import { Card } from "../../components/ui/Card";

export function NotFoundPage() {
  return <Card title="Not Found"><p className="mb-3 text-sm text-slate-600">The page does not exist.</p><Link className="text-teal-700" to="/dashboard">Back to dashboard</Link></Card>;
}
