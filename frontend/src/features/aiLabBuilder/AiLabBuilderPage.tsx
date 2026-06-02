import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { WandSparkles } from "lucide-react";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { PageHeader } from "../../components/ui/PageHeader";
import { Textarea } from "../../components/ui/Textarea";
import { api } from "../../lib/api";
import { AILabBuilderPreview, AIProviderStatus } from "../../types/aiLabBuilder";

const promptExamples = [
  "Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule.",
  "Create a two-router FRR eBGP lab with one point-to-point link and a BGP neighbor verification rule.",
  "Create a basic Linux lab with one Alpine host named host1 and a uname verification rule.",
  "Create a two-router FRR static routing lab with one point-to-point link and a route verification rule."
];

const exampleLabels = ["Two-router FRR OSPF", "Two-router FRR eBGP", "Basic Linux uname verification", "Static routing lab"];

export function AiLabBuilderPage() {
  const [prompt, setPrompt] = useState(promptExamples[0]);
  const [error, setError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [providerStatus, setProviderStatus] = useState<AIProviderStatus | null>(null);
  const [confirmRealProviderUsage, setConfirmRealProviderUsage] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadProviderStatus() {
      try {
        setStatusError("");
        setProviderStatus(await api<AIProviderStatus>("/api/v1/ai-lab-builder/provider/status"));
      } catch (err) {
        setStatusError(err instanceof Error ? err.message : "Provider status is unavailable");
      }
    }
    loadProviderStatus();
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (prompt.trim().length < 10) {
      setError("Prompt must describe the lab goal, nodes, and verification intent.");
      return;
    }
    if (providerStatus?.real_provider_confirmation_required && !confirmRealProviderUsage) {
      setError("Real AI provider usage requires explicit confirmation.");
      return;
    }
    setIsSubmitting(true);
    try {
      const preview = await api<AILabBuilderPreview>("/api/v1/ai-lab-builder/preview", {
        method: "POST",
        bodyJson: {
          prompt: prompt.trim(),
          confirm_real_provider_usage: confirmRealProviderUsage
        }
      });
      navigate(`/ai-lab-builder/previews/${preview.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate preview");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Lab Builder"
        subtitle="Describe the lab in plain English. The backend turns it into a safe LabPlan preview."
        action={<Link className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to="/ai-lab-builder/previews">Previews</Link>}
      />
      <Card title="Provider Status" subtitle="API keys stay on the backend and are never shown in the browser.">
        {providerStatus ? (
          <div className="grid gap-3 text-sm md:grid-cols-3">
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">Provider</div><div className="font-medium">{providerStatus.provider}</div></div>
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">Model</div><div className="font-medium">{providerStatus.model || "-"}</div></div>
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">Enabled</div><Badge value={providerStatus.enabled ? "ENABLED" : "DISABLED"} /></div>
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">API Key</div><Badge value={providerStatus.has_api_key ? "SET" : "NOT SET"} /></div>
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">Daily Limit</div><div className="font-medium">{providerStatus.daily_preview_limit_per_user}</div></div>
            <div className="rounded-md bg-slate-50 p-3"><div className="text-slate-500">Base URL</div><div className="font-medium">{providerStatus.base_url_host_only || "-"}</div></div>
          </div>
        ) : (
          <p className="text-sm text-slate-600">{statusError || "Loading provider status..."}</p>
        )}
        {providerStatus?.real_provider_confirmation_required && (
          <div className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">This uses a real AI provider and may consume quota or cost.</div>
        )}
        {providerStatus && !providerStatus.enabled && (
          <div className="mt-3 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">AI Lab Builder is disabled on this server.</div>
        )}
      </Card>
      <Card title="Generate Preview" subtitle="You can describe the lab in plain English. The system will generate the structured LabPlan internally.">
        {error && <Alert message={error} />}
        {providerStatus && !providerStatus.enabled ? (
          <p className="text-sm text-slate-600">AI Lab Builder is disabled on this server.</p>
        ) : <form className="space-y-3" onSubmit={submit}>
          <label className="block text-sm font-medium text-slate-700" htmlFor="ai-prompt">Lab description</label>
          <Textarea
            id="ai-prompt"
            className="min-h-40"
            placeholder="Describe the lab you want, e.g. Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule."
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
          />
          <p className="text-sm text-slate-600">Do not write JSON. Keep the request simple: lab type, node count, protocol, and verification goal.</p>
          <div className="flex flex-wrap gap-2">
            {promptExamples.map((example, index) => (
              <button
                className="rounded-md border border-slate-300 px-3 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                key={example}
                type="button"
                onClick={() => setPrompt(example)}
              >
                {exampleLabels[index]}
              </button>
            ))}
          </div>
          {providerStatus?.real_provider_confirmation_required && (
            <label className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              <input className="mt-1" type="checkbox" checked={confirmRealProviderUsage} onChange={(event) => setConfirmRealProviderUsage(event.target.checked)} />
              <span>I understand this request may use real AI provider quota.</span>
            </label>
          )}
          <div className="flex items-center gap-3">
            <Button disabled={isSubmitting} type="submit"><WandSparkles size={16} />{isSubmitting ? "Generating..." : "Generate Preview"}</Button>
            <Badge value="Admin and Instructor only" />
          </div>
        </form>}
      </Card>
      <Card title="MVP Constraints" subtitle="The validator enforces these limits before approval.">
        <div className="grid gap-3 text-sm text-slate-700 md:grid-cols-3">
          <div className="rounded-md bg-slate-50 p-3">Kinds: linux, frr</div>
          <div className="rounded-md bg-slate-50 p-3">Categories: Linux, BGP, OSPF</div>
          <div className="rounded-md bg-slate-50 p-3">Limits: 6 nodes, 10 links, 10 rules</div>
        </div>
      </Card>
    </div>
  );
}
