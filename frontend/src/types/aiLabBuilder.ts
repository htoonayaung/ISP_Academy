export type AIPreviewStatus = "DRAFT" | "VALID" | "INVALID" | "APPROVED" | "REJECTED";
export type AIValidationStatus = "PASSED" | "FAILED";

export interface LabPlanNode {
  name: string;
  kind: "linux" | "frr";
  role: string;
  image: string;
}

export interface LabPlanLink {
  endpoints: string[];
  subnet?: string | null;
}

export interface LabPlanVerificationRule {
  name: string;
  target_node: string;
  command: string;
  parser_type: string;
  assertion_type: string;
  expected_value?: string | null;
  timeout_seconds: number;
  is_active: boolean;
}

export interface GeneratedConfig {
  node: string;
  config_type: string;
  content: string;
}

export interface LabPlan {
  lab_name: string;
  title: string;
  description: string;
  category: "Linux" | "BGP" | "OSPF";
  difficulty: "Easy" | "Medium" | "Hard";
  estimated_cpu: number;
  estimated_memory_mb: number;
  estimated_duration_minutes: number;
  nodes: LabPlanNode[];
  links: LabPlanLink[];
  verification_rules: LabPlanVerificationRule[];
  student_instructions: string;
  hints: string;
  safety_notes: string[];
}

export interface AILabBuilderPreview {
  id: string;
  requested_by: string;
  prompt: string;
  lab_plan_json: LabPlan;
  generated_containerlab_yaml: string;
  generated_configs: GeneratedConfig[];
  generated_verification_rules: LabPlanVerificationRule[];
  validation_status: AIValidationStatus;
  validation_errors: string[];
  status: AIPreviewStatus;
  approved_at?: string | null;
  approved_by?: string | null;
  created_lab_template_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AILabBuilderApproval {
  preview: AILabBuilderPreview;
  created_lab_template_id: string;
}

export interface AIProviderStatus {
  enabled: boolean;
  provider: string;
  model?: string | null;
  base_url_host_only?: string | null;
  has_api_key: boolean;
  provider_test_enabled: boolean;
  daily_preview_limit_per_user: number;
  real_provider_confirmation_required: boolean;
}
