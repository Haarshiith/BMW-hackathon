// File upload and management API calls

import { apiClient } from "./api";
import { FileUploadResponse, MultipleFileUploadResponse } from "@/types/api";

export const fileService = {
  /**
   * Upload a single file
   */
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return apiClient.postFormData<FileUploadResponse>(
      "/files/upload",
      formData
    );
  },

  /**
   * Upload multiple files
   */
  async uploadMultipleFiles(
    files: File[]
  ): Promise<MultipleFileUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    return apiClient.postFormData<MultipleFileUploadResponse>(
      "/files/upload-multiple",
      formData
    );
  },

  /**
   * Delete a file
   */
  async deleteFile(
    filename: string
  ): Promise<{ message: string; success: boolean }> {
    return apiClient.delete<{ message: string; success: boolean }>(
      `/files/${filename}`
    );
  },

  /**
   * Get file information
   */
  async getFileInfo(filename: string): Promise<FileUploadResponse> {
    return apiClient.get<FileUploadResponse>(`/files/${filename}/info`);
  },

  /**
   * Get upload configuration
   */
  async getUploadConfig(): Promise<{
    max_file_size: number;
    max_files_per_upload: number;
    allowed_file_types: string[];
  }> {
    return apiClient.get("/files/config");
  },

  /**
   * Get file URL for display/download
   */
  getFileUrl(filename: string): string {
    return `${apiClient
      .getBaseURL()
      .replace("/api/v1", "")}/uploads/${filename}`;
  },

  /**
   * Validate file before upload (client-side)
   */
  validateFile(
    file: File,
    maxSize: number = 10 * 1024 * 1024, // 10MB default
    allowedTypes: string[] = ["image/jpeg", "image/png", "application/pdf"]
  ): { valid: boolean; error?: string } {
    // Check file size
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size exceeds maximum allowed size (${(
          maxSize /
          1024 /
          1024
        ).toFixed(0)}MB)`,
      };
    }

    // Check file type
    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type not allowed. Allowed types: ${allowedTypes.join(
          ", "
        )}`,
      };
    }

    return { valid: true };
  },

  /**
   * Validate multiple files
   */
  validateFiles(
    files: File[],
    maxFiles: number = 5,
    maxSize: number = 10 * 1024 * 1024,
    allowedTypes: string[] = ["image/jpeg", "image/png", "application/pdf"]
  ): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check number of files
    if (files.length > maxFiles) {
      errors.push(`Maximum ${maxFiles} files allowed`);
      return { valid: false, errors };
    }

    // Validate each file
    files.forEach((file) => {
      const validation = this.validateFile(file, maxSize, allowedTypes);
      if (!validation.valid && validation.error) {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  },
};
