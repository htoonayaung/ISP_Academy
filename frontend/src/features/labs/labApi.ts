import { api } from "../../lib/api";
import { Lab, LabEvent, LabNode } from "../../types/lab";

export const labApi = {
  list: () => api<Lab[]>("/api/v1/labs"),
  get: (id: string) => api<Lab>(`/api/v1/labs/${id}`),
  start: (id: string) => api<Lab>(`/api/v1/labs/${id}/start`, { method: "POST" }),
  stop: (id: string) => api<Lab>(`/api/v1/labs/${id}/stop`, { method: "POST" }),
  destroy: (id: string) => api<Lab>(`/api/v1/labs/${id}/destroy`, { method: "POST" }),
  nodes: (id: string) => api<LabNode[]>(`/api/v1/labs/${id}/nodes`),
  events: (id: string) => api<LabEvent[]>(`/api/v1/labs/${id}/events`)
};
