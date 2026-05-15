export interface ScreenerCondition {
  factor_code: string;
  operator: string;
  value: number;
}

export interface ScreenerRequest {
  conditions: ScreenerCondition[];
  logic: 'AND' | 'OR';
  sort_by?: string;
  sort_order: 'asc' | 'desc';
  page: number;
  page_size: number;
}

export interface BacktestRequest {
  name: string;
  factor_code: string;
  strategy_type: 'factor_quantile';
  start_date: string;
  end_date: string;
  n_quantiles: number;
  top_quantile: number;
  rebalance_freq: string;
}

export interface BacktestResult {
  id: number;
  name: string;
  status: string;
  total_return?: number;
  annual_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  win_rate?: number;
  equity_curve?: { date: string; value: number; drawdown?: number }[];
  error_message?: string;
}
