import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { WandSparkles } from "lucide-react";
import { Alert } from "../../components/ui/Alert";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { PageHeader } from "../../components/ui/PageHeader";
import { Textarea } from "../../components/ui/Textarea";
import { api } from "../../lib/api";
import { AILabBuilderPreview } from "../../types/aiLabBuilder";

const promptExamples = [
  "Create a basic Linux lab with one Alpine host named host1. Add a uname verification rule.",
  "Create a two-router FRR eBGP lab with one point-to-point link and a BGP neighbor verification rule.",
  "Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule."
];

export function AiLabBuilderPage() {
  const [prompt, setPrompt] = useState(promptExamples[0]);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (prompt.trim().length < 10) {
      setError("Prompt must describe the lab goal, nodes, and verification intent.");
      return;
    }
    setIsSubmitting(true);
    try {
      const preview = await api<AILabBuilderPreview>("/api/v1/ai-lab-builder/preview", {
        method: "POST",
        bodyJson: { prompt: prompt.trim() }
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
        subtitle="Generate a safe preview, validate it, then approve it into an inactive lab template."
        action={<Link className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700" to="/ai-lab-builder/previews">Previews</Link>}
      />
      <Card title="Generate Preview" subtitle="Phase 8 never starts Containerlab and never creates a running lab. AI output is treated as untrusted.">
        {error && <Alert message={error} />}
        <form className="space-y-3" onSubmit={submit}>
          <label className="block text-sm font-medium text-slate-700" htmlFor="ai-prompt">Prompt</label>
          <Textarea id="ai-prompt" className="min-h-40" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
          <div className="flex flex-wrap gap-2">
            {promptExamples.map((example) => (
              <button
                className="rounded-md border border-slate-300 px-3 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                key={example}
                type="button"
                onClick={() => setPrompt(example)}
              >
                {example}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Button disabled={isSubmitting} type="submit"><WandSparkles size={16} />{isSubmitting ? "Generating..." : "Generate Preview"}</Button>
            <Badge value="Admin and Instructor only" />
          </div>
        </form>
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
