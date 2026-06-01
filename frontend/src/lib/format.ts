export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function canStartLab(status: string): boolean {
  return ["CREATED", "STOPPED", "FAILED"].includes(status);
}

export function canStopLab(status: string): boolean {
  return status === "RUNNING";
}

export function canDestroyLab(status: string): boolean {
  return !["DESTROYING", "DESTROYED"].includes(status);
}

export function statusTone(status: string): "green" | "red" | "yellow" | "gray" | "blue" {
  if (["RUNNING", "PASSED", "PUBLISHED"].includes(status)) return "green";
  if (["FAILED", "ERROR", "ARCHIVED"].includes(status)) return "red";
  if (["STARTING", "STOPPING", "DESTROYING", "QUEUED", "RUNNING"].includes(status)) return "yellow";
  if (["CREATED", "STARTED", "DRAFT"].includes(status)) return "blue";
  return "gray";
}
