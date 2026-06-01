export interface VerificationRule {
  id: string;
  ticket_id: string;
  name: string;
  target_node: string;
  command: string;
  parser_type: string;
  assertion_type: string;
  expected_value: string | null;
  timeout_seconds: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VerificationResult {
  id: string;
  verification_run_id: string;
  verification_rule_id: string;
  status: string;
  actual_output: string | null;
  message: string;
  created_at: string;
}

export interface VerificationRun {
  id: string;
  ticket_attempt_id: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  results: VerificationResult[];
}
