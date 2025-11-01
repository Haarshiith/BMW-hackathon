// Department-related API calls

import { apiClient } from "./api";
import {
  DepartmentSummary,
  DepartmentInsights,
  LessonLearned,
  PaginatedResponse,
  DepartmentListResponse,
} from "@/types/api";

export const departmentService = {
  /**
   * Get list of all departments
   */
  async getDepartments(): Promise<string[]> {
    const response = await apiClient.get<DepartmentListResponse>(
      "/departments"
    );
    return response.departments;
  },

  /**
   * Get all lessons for a specific department
   */
  async getDepartmentLessons(
    department: string,
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<LessonLearned>> {
    return apiClient.get<PaginatedResponse<LessonLearned>>(
      `/departments/${department}/lessons?page=${page}&limit=${limit}`
    );
  },

  /**
   * Get AI-powered consolidated summary for a department
   */
  async getDepartmentSummary(department: string): Promise<DepartmentSummary> {
    return apiClient.get<DepartmentSummary>(
      `/departments/${department}/summary`
    );
  },

  /**
   * Get comprehensive insights and analytics for a department
   */
  async getDepartmentInsights(department: string): Promise<DepartmentInsights> {
    return apiClient.get<DepartmentInsights>(
      `/departments/${department}/insights`
    );
  },

  /**
   * Get basic statistics for a department (no AI calls)
   */
  async getDepartmentStatistics(department: string): Promise<{
    department: string;
    total_lessons: number;
    severity_breakdown: {
      low: number;
      medium: number;
      high: number;
      critical: number;
    };
    unique_commodities: number;
    unique_suppliers: number;
    commodities: string[];
    suppliers: string[];
  }> {
    return apiClient.get(`/departments/${department}/statistics`);
  },

  /**
   * Regenerate department AI summary (force refresh)
   */
  async regenerateDepartmentSummary(department: string): Promise<any> {
    return apiClient.post(`/departments/${department}/regenerate-summary`);
  },
};
