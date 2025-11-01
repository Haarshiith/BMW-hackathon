// Health check and system status API calls

import { apiClient } from "./api";
import { HealthCheck } from "@/types/api";

export const healthService = {
  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthCheck> {
    return apiClient.get<HealthCheck>("/health");
  },

  /**
   * Check detailed health status
   */
  async checkDetailedHealth(): Promise<HealthCheck> {
    return apiClient.get<HealthCheck>("/health/details");
  },
};
