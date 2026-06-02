import { LabEvent } from "./lab";

export interface RuntimeContainerSummary {
  source: string;
  known_container_count: number;
  running_lab_count: number;
  message: string;
}

export interface RuntimeLabSummary {
  id: string;
  lab_name: string;
  owner_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
  has_containers: boolean;
  warning: string | null;
}

export interface RuntimeOrphanCandidate {
  path: string;
  warning: string;
}

export interface RuntimeStatus {
  containers: RuntimeContainerSummary;
  status_counts: Record<string, number>;
  labs_by_status: Record<string, RuntimeLabSummary[]>;
  stuck_candidates: RuntimeLabSummary[];
  orphan_candidates: RuntimeOrphanCandidate[];
  demo_labs: RuntimeLabSummary[];
  warnings: string[];
}

export interface RuntimeRefreshResult {
  queued_refresh_count: number;
  inspected_statuses: string[];
  warnings: string[];
}

export interface RuntimeRecoverResult {
  lab_id: string;
  action: string;
  status: string;
  queued_task: boolean;
  message: string;
}

export interface RuntimeCleanupResult {
  queued_task: boolean;
  eligible_demo_labs: RuntimeLabSummary[];
  skipped: string[];
  message: string;
}

export interface RuntimeEventsResult {
  lab_id: string;
  events: LabEvent[];
}
