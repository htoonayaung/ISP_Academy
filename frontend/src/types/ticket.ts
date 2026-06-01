export interface Ticket {
  id: string;
  lab_template_id: string;
  title: string;
  slug: string;
  description: string;
  student_instructions: string;
  hints: string | null;
  hidden_solution?: string | null;
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED";
  created_by: string;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketAttempt {
  id: string;
  ticket_id: string;
  student_id: string;
  lab_instance_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}
