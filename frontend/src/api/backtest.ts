import { apiClient } from './client';
import type { ApiResponse } from './types';

export const screenerApi = {
  search: (data: Record<string, unknown>) =>
    apiClient.post<any, ApiResponse>('/screener/search', data),
};

export const backtestApi = {
  run: (data: Record<string, unknown>) =>
    apiClient.post<any, ApiResponse>('/backtest/run', data),
  get: (id: number) => apiClient.get<any, ApiResponse>(`/backtest/${id}`),
  list: () => apiClient.get<any, ApiResponse>('/backtest'),
};
