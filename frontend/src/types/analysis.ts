export interface ICAnalysis {
  factor_code: string;
  ic_mean: number;
  ic_std: number;
  ir: number;
  ic_positive_ratio: number;
  t_stat: number;
  ic_series: ICSeriesPoint[];
}

export interface ICSeriesPoint {
  trade_date: string;
  ic_pearson: number;
  ic_spearman: number;
}

export interface HeatmapData {
  factors: string[];
  months: string[];
  data: number[][];
}

export interface CorrelationData {
  factors: string[];
  matrix: number[][];
  trade_date?: string;
}

export interface FactorReturn {
  factor_code: string;
  quantile_returns: Record<number, { date: string; daily_return: number }[]>;
  cumulative_returns: Record<number, { date: string; value: number }[]>;
}
