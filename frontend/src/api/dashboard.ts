import { apiClient } from './client';
import type { ApiResponse } from './types';

export const dashboardApi = {
  overview: () => apiClient.get<any, ApiResponse>('/dashboard/overview'),
  indexPerformance: () => apiClient.get<any, ApiResponse>('/dashboard/index-performance'),
};
