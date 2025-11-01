export type SearchSource = 'database' | 'rag' | 'web';

export type SearchStatus = 'searching' | 'completed' | 'failed';

export interface SolutionSearchRequest {
  problem_description: string;
  department: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  reporter_name: string;
}

export interface SearchResult {
  source: SearchSource;
  title: string;
  description: string;
  relevance_score: number;
  solution?: string;
  url?: string;
  metadata?: {
    incident_id?: number;
    created_at?: string;
    department?: string;
    severity?: string;
  };
}

export interface SolutionSearchResponse {
  search_id: number;
  status: SearchStatus;
  results: SearchResult[];
  summary: string;
  confidence_score: number;
  search_progress?: {
    database_completed: boolean;
    rag_completed: boolean;
    web_completed: boolean;
    total_sources: number;
    completed_sources: number;
  };
}

export interface SearchStatusResponse {
  search_id: number;
  status: SearchStatus;
  progress: {
    database_completed: boolean;
    rag_completed: boolean;
    web_completed: boolean;
    total_sources: number;
    completed_sources: number;
  };
  estimated_completion_time?: number;
}

export interface SolutionSearchFormData {
  problem_description: string;
  department: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  reporter_name: string;
}

export interface SearchRefinementRequest {
  search_id: number;
  additional_keywords?: string[];
  exclude_sources?: SearchSource[];
  min_relevance_score?: number;
  department_filter?: string;
}

export interface SearchRefinementResponse {
  refined_results: SearchResult[];
  updated_summary: string;
  refinement_applied: string;
}
