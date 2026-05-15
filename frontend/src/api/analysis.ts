import { apiClient } from './client';
import type { ApiResponse } from './types';

export const analysisApi = {
  ic: (params: Record<string, unknown>) =>
    apiClient.post<any, ApiResponse>('/analysis/ic', params),
  heatmap: (params: Record<string, unknown>) =>
    apiClient.post<any, ApiResponse>('/analysis/heatmap', params),
  correlation: (params: Record<string, unknown>) =>
    apiClient.post<any, ApiResponse>('/analysis/correlation', params),
  factorReturns: (factorCode: string, params: Record<string, unknown>) =>
    apiClient.get<any, ApiResponse>(`/analysis/factor-returns/${factorCode}`, { params }),
};
