import { apiClient } from './client';
import type { ApiResponse } from './types';

export const factorsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<any, ApiResponse>('/factors', { params }),
  categories: () => apiClient.get<any, ApiResponse>('/factors/categories'),
  detail: (code: string) => apiClient.get<any, ApiResponse>(`/factors/${code}`),
  popular: () => apiClient.get<any, ApiResponse>('/factors/popular'),
  compute: (data: { factor_code: string; start_date: string; end_date: string }) =>
    apiClient.post<any, ApiResponse>('/factors/compute', data),
};
