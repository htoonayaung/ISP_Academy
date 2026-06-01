export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export function shortId(value: string): string {
  return value.slice(0, 8);
}

export function roleLabel(role: string | undefined): string {
  if (role === "ADMIN") return "Administrator";
  if (role === "INSTRUCTOR") return "Instructor";
  if (role === "STUDENT") return "Student";
  return "Unknown role";
}

export function canStartLab(status: string): boolean {
  return ["CREATED", "STOPPED", "FAILED"].includes(status);
}

export function canStopLab(status: string): boolean {
  return status === "RUNNING";
}

export function canDestroyLab(status: string): boolean {
  return !["STARTING", "STOPPING", "DESTROYING", "DESTROYED"].includes(status);
}

export function statusTone(status: string): "green" | "red" | "yellow" | "gray" | "blue" {
  if (["RUNNING", "PASSED", "PUBLISHED", "ACTIVE"].includes(status)) return "green";
  if (["FAILED", "ERROR", "ARCHIVED"].includes(status)) return "red";
  if (["STARTING", "STOPPING", "DESTROYING", "QUEUED", "RUNNING"].includes(status)) return "yellow";
  if (["CREATED", "STARTED", "DRAFT", "IN_PROGRESS"].includes(status)) return "blue";
  return "gray";
}
