import { Copy } from "lucide-react";
import { Button } from "./Button";

export function CopyId({ id, label = "ID" }: { id: string; label?: string }) {
  const shortId = id.slice(0, 8);
  function copy() {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(id);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = id;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  return (
    <div className="inline-flex items-center gap-2 rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-700">
      <span>{label}: {shortId}</span>
      <Button
        type="button"
        className="min-h-6 bg-transparent p-1 text-slate-600 hover:bg-slate-200"
        title={`Copy ${label}`}
        onClick={copy}
      >
        <Copy size={13} />
      </Button>
    </div>
  );
}
