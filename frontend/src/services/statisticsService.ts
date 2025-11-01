// Statistics and analytics API calls

import { apiClient } from './api';
import { StatisticsOverview } from '@/types/api';

export const statisticsService = {
  /**
   * Get overall statistics
   */
  async getOverview(): Promise<StatisticsOverview> {
    return apiClient.get<StatisticsOverview>('/statistics/overview');
  },

  /**
   * Get statistics by severity
   */
  async getBySeverity(): Promise<Record<string, number>> {
    return apiClient.get<Record<string, number>>('/statistics/by-severity');
  },

  /**
   * Get statistics by department
   */
  async getByDepartment(): Promise<Record<string, number>> {
    return apiClient.get<Record<string, number>>('/statistics/by-department');
  },

  /**
   * Get recent trends
   */
  async getRecentTrends(days: number = 30): Promise<any> {
    return apiClient.get(`/statistics/trends?days=${days}`);
  },
};

