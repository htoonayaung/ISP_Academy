export interface Lab {
  id: string;
  template_id: string;
  owner_id: string;
  status: string;
  lab_name: string;
  lab_directory: string;
  started_at: string | null;
  stopped_at: string | null;
  destroyed_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface LabNode {
  id: string;
  lab_instance_id: string;
  name: string;
  kind: string;
  role: string | null;
  container_name: string | null;
  management_ipv4: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LabEvent {
  id: string;
  lab_instance_id: string;
  event_type: string;
  message: string;
  stdout: string | null;
  stderr: string | null;
  created_by: string | null;
  created_at: string;
}
