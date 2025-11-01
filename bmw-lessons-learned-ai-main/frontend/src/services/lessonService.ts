// Lesson-related API calls

import { apiClient } from "./api";
import {
  LessonLearned,
  LessonLearnedCreate,
  PaginatedResponse,
  LessonFilters,
} from "@/types/api";

export const lessonService = {
  /**
   * Get all lessons with optional filters and pagination
   */
  async getLessons(
    filters?: LessonFilters
  ): Promise<PaginatedResponse<LessonLearned>> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          params.append(key, String(value));
        }
      });
    }

    const queryString = params.toString();
    const url = queryString ? `/lessons?${queryString}` : "/lessons";

    return apiClient.get<PaginatedResponse<LessonLearned>>(url);
  },

  /**
   * Get a single lesson by ID
   */
  async getLessonById(id: number | string): Promise<LessonLearned> {
    return apiClient.get<LessonLearned>(`/lessons/${id}`);
  },

  /**
   * Create a new lesson (JSON format)
   */
  async createLesson(data: LessonLearnedCreate): Promise<LessonLearned> {
    return apiClient.post<LessonLearned>("/lessons", data);
  },

  /**
   * Create a new lesson with file uploads (multipart/form-data)
   * This is the recommended approach for creating lessons with attachments
   */
  async createLessonWithFiles(
    data: LessonLearnedCreate,
    files?: File[]
  ): Promise<LessonLearned> {
    const formData = new FormData();

    // Append all form fields
    formData.append("commodity", data.commodity);
    formData.append("error_location", data.error_location);
    formData.append("problem_description", data.problem_description);
    formData.append("missed_detection", data.missed_detection);
    formData.append("provided_solution", data.provided_solution);
    formData.append("department", data.department);
    formData.append("severity", data.severity);
    formData.append("reporter_name", data.reporter_name);

    // Optional fields
    if (data.part_number) formData.append("part_number", data.part_number);
    if (data.supplier) formData.append("supplier", data.supplier);

    // Append files
    if (files && files.length > 0) {
      files.forEach((file) => {
        formData.append("attachments", file);
      });
    }

    return apiClient.postFormData<LessonLearned>(
      "/lessons/create-with-files",
      formData
    );
  },

  /**
   * Update an existing lesson
   */
  async updateLesson(
    id: number | string,
    data: Partial<LessonLearnedCreate>
  ): Promise<LessonLearned> {
    return apiClient.put<LessonLearned>(`/lessons/${id}`, data);
  },

  /**
   * Delete a lesson
   */
  async deleteLesson(id: number | string): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/lessons/${id}`);
  },

  /**
   * Regenerate AI analysis for a lesson
   */
  async regenerateAI(id: number | string): Promise<LessonLearned> {
    return apiClient.post<LessonLearned>(`/lessons/${id}/regenerate-ai`);
  },

  /**
   * Add attachments to an existing lesson
   */
  async addAttachments(
    id: number | string,
    files: File[]
  ): Promise<LessonLearned> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("attachments", file);
    });

    return apiClient.postFormData<LessonLearned>(
      `/lessons/${id}/add-attachments`,
      formData
    );
  },

  /**
   * Remove an attachment from a lesson
   */
  async removeAttachment(
    id: number | string,
    filename: string
  ): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(
      `/lessons/${id}/attachments/${filename}`
    );
  },
};
