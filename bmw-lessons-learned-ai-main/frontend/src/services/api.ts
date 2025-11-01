// Base API client with error handling and interceptors

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from "axios";
import { ErrorResponse } from "@/types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || "30000", 10);

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any auth tokens here if needed in the future
        // config.headers.Authorization = `Bearer ${token}`;
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        // Handle common errors
        if (error.response) {
          // Server responded with error
          const errorMessage =
            error.response.data?.detail ||
            error.response.data?.error ||
            "An error occurred";
          console.error("API Error:", errorMessage);

          // You can add custom error handling based on status codes
          switch (error.response.status) {
            case 400:
              console.error("Bad Request:", errorMessage);
              break;
            case 401:
              console.error("Unauthorized:", errorMessage);
              // Redirect to login if needed
              break;
            case 403:
              console.error("Forbidden:", errorMessage);
              break;
            case 404:
              console.error("Not Found:", errorMessage);
              break;
            case 422:
              console.error("Validation Error:", errorMessage);
              break;
            case 500:
              console.error("Server Error:", errorMessage);
              break;
            default:
              console.error("Error:", errorMessage);
          }

          throw new Error(errorMessage);
        } else if (error.request) {
          // Request made but no response
          console.error("Network Error: No response from server");
          throw new Error("Network error. Please check your connection.");
        } else {
          // Something else happened
          console.error("Error:", error.message);
          throw new Error(error.message);
        }
      }
    );
  }

  // Generic GET request
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  // Generic POST request
  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  // Generic PUT request
  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  // Generic PATCH request
  async patch<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  // Generic DELETE request
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // POST with FormData (for file uploads)
  async postFormData<T>(
    url: string,
    formData: FormData,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      ...config,
      headers: {
        "Content-Type": "multipart/form-data",
        ...config?.headers,
      },
    });
    return response.data;
  }

  // Get base URL
  getBaseURL(): string {
    return API_BASE_URL;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
