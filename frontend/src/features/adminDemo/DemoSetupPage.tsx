import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { Input } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/PageHeader";
import { api } from "../../lib/api";
import { DemoResetResult, DemoSetupResult, DemoStatus } from "../../types/demo";

function BoolBadge({ value }: { value: boolean }) {
  return <Badge value={value ? "READY" : "MISSING"} />;
}

export function DemoSetupPage() {
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [setupResult, setSetupResult] = useState<DemoSetupResult | null>(null);
  const [resetResult, setResetResult] = useState<DemoResetResult | null>(null);
  const [resetConfirm, setResetConfirm] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  async function load() {
    try {
      setError("");
      setStatus(await api<DemoStatus>("/api/v1/admin/demo/status"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo status");
    }
  }

  useEffect(() => { load(); }, []);

  async function runSetup() {
    if (!confirm("Run demo setup? This creates only demo-prefixed data and does not start labs.")) return;
    setIsBusy(true);
    try {
      setError("");
      setResetResult(null);
      setSetupResult(await api<DemoSetupResult>("/api/v1/admin/demo/setup", {
        method: "POST",
        bodyJson: {
          include_linux_demo: true,
          include_frr_demo: false,
          activate_templates: true,
          publish_tickets: true
        }
      }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo setup failed");
    } finally {
      setIsBusy(false);
    }
  }

  async function resetDemo() {
    setIsBusy(true);
    try {
      setError("");
      setSetupResult(null);
      setResetResult(await api<DemoResetResult>("/api/v1/admin/demo/reset", {
        method: "POST",
        bodyJson: { confirm: resetConfirm, destroy_demo_labs: false }
      }));
      setResetConfirm("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo reset failed");
    } finally {
      setIsBusy(false);
    }
  }

  async function copy(value: string) {
    await navigator.clipboard.writeText(value);
  }

  const missing = status ? [
    !status.users.demo_instructor_exists && "demo_instructor",
    !status.users.demo_student_exists && "demo_student",
    !status.lab_templates.basic_linux_exists && "Demo Basic Linux Lab",
    !status.lab_templates.basic_linux_active && "Active demo lab template",
    !status.tickets.demo_ticket_exists && "Demo Linux Verification Ticket",
    !status.tickets.demo_ticket_published && "Published demo ticket",
    !status.verification_rules.demo_rule_exists && "Demo verification rule"
  ].filter(Boolean) : [];

  return (
    <div className="space-y-4">
      <PageHeader title="Demo Setup" subtitle="Create and reset safe demo-prefixed data for MVP walkthroughs." />
      {error && <Alert message={error} />}
      {status?.demo_ready && (
        <Card title="Demo Ready" subtitle="The demo users, lab template, ticket, and verification rule are ready for a browser walkthrough.">
          <div className="space-y-4">
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
              Demo data is ready. Next step: logout from the admin account and login as <strong>demo_student</strong>.
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-md bg-slate-50 p-3 text-sm">
                <div className="text-xs font-medium uppercase text-slate-500">Instructor username</div>
                <div className="mt-1 font-semibold">demo_instructor</div>
              </div>
              <div className="rounded-md bg-slate-50 p-3 text-sm">
                <div className="text-xs font-medium uppercase text-slate-500">Student username</div>
                <div className="mt-1 font-semibold">demo_student</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => copy("demo_student")}>Copy student username</Button>
              <Link className="inline-flex min-h-9 items-center rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to="/login">Go to login</Link>
              <a className="inline-flex min-h-9 items-center rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50" href="https://github.com/htoonayaung/ISP_Academy/blob/phase-7-frontend/docs/DemoGuide.md" target="_blank" rel="noreferrer">Open Demo Guide</a>
            </div>
          </div>
        </Card>
      )}
      <Card title="Demo Status" subtitle="Setup never starts labs, runs AI, or deploys Containerlab.">
        {status ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <Badge value={status.demo_ready ? "DEMO READY" : "NOT READY"} />
              <Badge value={status.safe_to_run_setup ? "SETUP ENABLED" : "SETUP DISABLED"} />
            </div>
            {status.warnings.map((warning) => <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900" key={warning}>{warning}</div>)}
            {missing.length > 0 && <div className="text-sm text-slate-600">Missing: {missing.join(", ")}</div>}
          </div>
        ) : <EmptyState title="Loading demo status" description="Checking demo users, content, and readiness." />}
      </Card>
      {status && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Demo Accounts" subtitle="Generated accounts are for demos only.">
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between"><span>Instructor: demo_instructor</span><BoolBadge value={status.users.demo_instructor_exists} /></div>
              <div className="flex items-center justify-between"><span>Student: demo_student</span><BoolBadge value={status.users.demo_student_exists} /></div>
            </div>
          </Card>
          <Card title="Demo Content" subtitle="Content is created with demo-prefixed slugs.">
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between"><span>Basic Linux template</span><BoolBadge value={status.lab_templates.basic_linux_exists} /></div>
              <div className="flex items-center justify-between"><span>Template active</span><BoolBadge value={status.lab_templates.basic_linux_active} /></div>
              <div className="flex items-center justify-between"><span>Published ticket</span><BoolBadge value={status.tickets.demo_ticket_published} /></div>
              <div className="flex items-center justify-between"><span>Verification rule</span><BoolBadge value={status.verification_rules.demo_rule_exists} /></div>
            </div>
          </Card>
        </div>
      )}
      <Card title="Setup Action" subtitle={status?.demo_ready ? "Demo data already exists. Re-run only if an item is missing." : "Run setup to create demo-prefixed users and content."}>
        <div className="flex flex-wrap items-end gap-3">
          <Button className={status?.demo_ready ? "bg-slate-600 hover:bg-slate-700" : ""} disabled={isBusy || status?.safe_to_run_setup === false || status?.demo_ready === true} onClick={runSetup}>Run Demo Setup</Button>
          {status?.demo_ready && <span className="text-sm text-slate-600">Setup is disabled because the demo is already ready.</span>}
        </div>
      </Card>
      <Card title="Danger Zone" subtitle="Reset requires exact confirmation and affects demo-prefixed data only.">
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3">
          <div className="flex flex-wrap items-end gap-3">
          <div className="w-64">
            <label className="mb-1 block text-xs font-medium text-rose-900">Type RESET_DEMO_DATA</label>
            <Input value={resetConfirm} onChange={(event) => setResetConfirm(event.target.value)} />
          </div>
          <Button className="bg-rose-700 hover:bg-rose-800" disabled={isBusy || resetConfirm !== "RESET_DEMO_DATA"} onClick={resetDemo}>Reset Demo Data</Button>
          </div>
        </div>
      </Card>
      {setupResult && (
        <Card title="Setup Result" subtitle={setupResult.credentials_note}>
          <div className="grid gap-4 lg:grid-cols-2">
            <div><h3 className="mb-2 text-sm font-semibold">Created</h3><ul className="list-disc pl-5 text-sm text-slate-700">{setupResult.created.map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div><h3 className="mb-2 text-sm font-semibold">Existing</h3><ul className="list-disc pl-5 text-sm text-slate-700">{setupResult.existing.map((item) => <li key={item}>{item}</li>)}</ul></div>
          </div>
          <div className="mt-4 space-y-2">
            {setupResult.demo_accounts.map((account) => (
              <div className="flex flex-wrap items-center gap-2 rounded-md bg-slate-50 p-2 text-sm" key={account.username}>
                <span className="font-medium">{account.role}</span>
                <span>{account.username}</span>
                {account.password && <><code className="rounded bg-white px-2 py-1">{account.password}</code><Button onClick={() => copy(account.password || "")}>Copy</Button></>}
              </div>
            ))}
          </div>
        </Card>
      )}
      {resetResult && (
        <Card title="Reset Result" subtitle="Demo-prefixed data cleanup summary.">
          <ul className="list-disc pl-5 text-sm text-slate-700">{resetResult.deleted.map((item) => <li key={item}>{item}</li>)}</ul>
          {resetResult.warnings.map((warning) => <div className="mt-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900" key={warning}>{warning}</div>)}
        </Card>
      )}
      <Card title="Next Steps" subtitle="Browser walkthrough after setup.">
        <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
          <li>Login as demo_student.</li>
          <li>Open the published demo ticket.</li>
          <li>Start attempt.</li>
          <li>Start lab and wait for RUNNING.</li>
          <li>Run verification and confirm PASSED.</li>
          <li>Destroy the lab.</li>
        </ol>
      </Card>
    </div>
  );
}
