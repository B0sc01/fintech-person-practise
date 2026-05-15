import { apiClient } from './client';
import type { ApiResponse } from './types';

export const dataApi = {
  status: () => apiClient.get<any, ApiResponse>('/data/status'),
  stocks: (params: Record<string, unknown>) =>
    apiClient.get<any, ApiResponse>('/data/stocks', { params }),
  stockDaily: (tsCode: string, params?: Record<string, unknown>) =>
    apiClient.get<any, ApiResponse>(`/data/stocks/${tsCode}/daily`, { params }),
  downloadStockList: () => apiClient.post<any, ApiResponse>('/data/download/stock-list'),
  downloadDaily: (data: { start_date: string; end_date: string }) =>
    apiClient.post<any, ApiResponse>('/data/download/daily', data),
  downloadProgress: () => apiClient.get<any, ApiResponse>('/data/download/progress'),
  dateRange: () => apiClient.get<any, ApiResponse>('/data/date-range'),
  industries: () => apiClient.get<any, ApiResponse>('/data/industries'),
};
