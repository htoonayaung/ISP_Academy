import { api } from "../../lib/api";
import {
  RuntimeCleanupResult,
  RuntimeEventsResult,
  RuntimeRecoverResult,
  RuntimeRefreshResult,
  RuntimeStatus
} from "../../types/adminRuntime";

export const adminRuntimeApi = {
  status: () => api<RuntimeStatus>("/api/v1/admin/runtime/labs/status"),
  refresh: () => api<RuntimeRefreshResult>("/api/v1/admin/runtime/labs/refresh", { method: "POST" }),
  recover: (labId: string, action: "mark_failed" | "retry_destroy" | "force_destroy_demo_only", confirm: string) =>
    api<RuntimeRecoverResult>(`/api/v1/admin/runtime/labs/${labId}/recover`, {
      method: "POST",
      bodyJson: { action, confirm }
    }),
  cleanupDemo: (confirm: string) =>
    api<RuntimeCleanupResult>("/api/v1/admin/runtime/cleanup/demo", {
      method: "POST",
      bodyJson: { confirm }
    }),
  events: (labId: string) => api<RuntimeEventsResult>(`/api/v1/admin/runtime/labs/${labId}/events`)
};
