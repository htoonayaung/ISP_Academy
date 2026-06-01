export interface LabTemplate {
  id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  difficulty: string;
  containerlab_yaml: string;
  default_startup_config: string | null;
  estimated_cpu: number;
  estimated_memory_mb: number;
  estimated_duration_minutes: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}
