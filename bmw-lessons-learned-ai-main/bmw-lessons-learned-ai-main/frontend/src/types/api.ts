// TypeScript types for backend API

export type SeverityLevel = "low" | "medium" | "high" | "critical";

export interface AIAnalysis {
  lesson_summary: string;
  lesson_detailed: string;
  best_practice: string[];
  preventive_actions: string[];
}

export interface LessonLearned {
  id: number;
  commodity: string;
  part_number?: string | null;
  supplier?: string | null;
  error_location: string;
  problem_description: string;
  missed_detection: string;
  provided_solution: string;
  department: string;
  severity: SeverityLevel;
  reporter_name: string;
  attachments: string[];
  ai_analysis: AIAnalysis | null;
  created_at: string;
  updated_at: string;
}

export interface LessonLearnedCreate {
  commodity: string;
  part_number?: string;
  supplier?: string;
  error_location: string;
  problem_description: string;
  missed_detection: string;
  provided_solution: string;
  department: string;
  severity: SeverityLevel;
  reporter_name: string;
  attachments?: string[];
}

export interface FileUploadResponse {
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
  uploaded_at: string;
}

export interface MultipleFileUploadResponse {
  uploaded_files: FileUploadResponse[];
  failed_files: FileValidationError[];
  total_uploaded: number;
  total_failed: number;
}

export interface FileValidationError {
  filename: string;
  error: string;
  error_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface DepartmentSummary {
  department: string;
  total_lessons: number;
  consolidated_summary: string;
  key_patterns: string[];
  top_recommendations: string[];
  severity_breakdown: Record<SeverityLevel, number>;
  generated_at: string;
  ai_generated: boolean;
}

export interface DepartmentInsights {
  department: string;
  total_lessons: number;
  lessons: LessonLearned[];
  severity_distribution: Record<SeverityLevel, number>;
  common_commodities: Array<{ commodity: string; count: number }>;
  recent_trends: string;
  ai_insights: string;
}

export interface StatisticsOverview {
  total_lessons: number;
  lessons_by_severity: Record<SeverityLevel, number>;
  lessons_by_department: Record<string, number>;
  recent_lessons_count: number;
  total_departments: number;
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  database: string;
  openai_api?: string;
  version: string;
}

export interface DepartmentListResponse {
  departments: string[];
  total_departments: number;
}

export interface ErrorResponse {
  detail: string;
  error?: string;
  status_code?: number;
}

// Filter types
export interface LessonFilters {
  page?: number;
  limit?: number;
  department?: string;
  severity?: SeverityLevel;
  search?: string;
  commodity?: string;
  part_number?: string;
  supplier?: string;
  start_date?: string;
  end_date?: string;
  sort_by?: "created_at" | "updated_at" | "severity";
  sort_order?: "asc" | "desc";
}
