export interface DemoStatus {
  demo_ready: boolean;
  users: {
    demo_instructor_exists: boolean;
    demo_student_exists: boolean;
  };
  lab_templates: {
    basic_linux_exists: boolean;
    basic_linux_active: boolean;
  };
  tickets: {
    demo_ticket_exists: boolean;
    demo_ticket_published: boolean;
  };
  verification_rules: {
    demo_rule_exists: boolean;
  };
  safe_to_run_setup: boolean;
  warnings: string[];
}

export interface DemoAccount {
  role: string;
  username: string;
  password?: string | null;
}

export interface DemoSetupResult {
  status: string;
  created: string[];
  existing: string[];
  credentials_note: string;
  demo_accounts: DemoAccount[];
  next_steps: string[];
}

export interface DemoResetResult {
  status: string;
  deleted: string[];
  skipped: string[];
  warnings: string[];
}
