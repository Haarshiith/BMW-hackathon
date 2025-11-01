import { apiClient } from "./api";
import type {
  SolutionSearchRequest,
  SolutionSearchResponse,
  SearchStatusResponse,
  SearchRefinementRequest,
  SearchRefinementResponse,
} from "@/types/solutionSearch";

export const solutionSearchService = {
  /**
   * Submit a new solution search request
   */
  async submitSolutionSearch(
    searchData: SolutionSearchRequest
  ): Promise<SolutionSearchResponse> {
    return apiClient.post<SolutionSearchResponse>(
      "/solution-search/submit",
      searchData
    );
  },

  /**
   * Get search results by search ID
   */
  async getSearchResults(searchId: number): Promise<SolutionSearchResponse> {
    return apiClient.get<SolutionSearchResponse>(
      `/solution-search/${searchId}`
    );
  },

  /**
   * Get search status and progress
   */
  async getSearchStatus(searchId: number): Promise<SearchStatusResponse> {
    return apiClient.get<SearchStatusResponse>(
      `/solution-search/${searchId}/status`
    );
  },

  /**
   * Poll search status until completion
   */
  async pollSearchStatus(
    searchId: number,
    onProgress?: (status: SearchStatusResponse) => void,
    maxAttempts: number = 30,
    intervalMs: number = 2000
  ): Promise<SolutionSearchResponse> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const status = await this.getSearchStatus(searchId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.status === "completed") {
          return await this.getSearchResults(searchId);
        }

        if (status.status === "failed") {
          throw new Error("Search failed");
        }

        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        attempts++;
      } catch (error) {
        if (attempts === maxAttempts - 1) {
          throw error;
        }
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        attempts++;
      }
    }

    throw new Error("Search timeout - please try again.");
  },

  /**
   * Refine search results
   */
  async refineSearch(
    refinementData: SearchRefinementRequest
  ): Promise<SearchRefinementResponse> {
    return apiClient.post<SearchRefinementResponse>(
      `/solution-search/${refinementData.search_id}/refine`,
      refinementData
    );
  },

  /**
   * Get search history for a user
   */
  async getSearchHistory(userName?: string): Promise<SolutionSearchResponse[]> {
    const params = userName ? { reporter_name: userName } : {};
    return apiClient.get<SolutionSearchResponse[]>("/solution-search/history", {
      params,
    });
  },

  /**
   * Save a solution for later use
   */
  async saveSolution(
    searchId: number,
    resultId: string,
    notes?: string
  ): Promise<{ success: boolean; saved_solution_id: number }> {
    return apiClient.post(`/solution-search/${searchId}/save`, {
      result_id: resultId,
      notes,
    });
  },

  /**
   * Get saved solutions
   */
  async getSavedSolutions(): Promise<
    Array<{
      id: number;
      search_id: number;
      result_id: string;
      notes?: string;
      saved_at: string;
      result: any;
    }>
  > {
    return apiClient.get("/solution-search/saved");
  },
};
