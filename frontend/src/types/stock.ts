export interface StockBasic {
  ts_code: string;
  name: string;
  industry?: string;
  area?: string;
  list_date?: string;
  is_hs: boolean;
}

export interface StockDaily {
  ts_code: string;
  trade_date: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  pre_close?: number;
  volume?: number;
  amount?: number;
  turnover_rate?: number;
}

export interface DataStatus {
  stock_count: number;
  daily_count: number;
  min_date?: string;
  max_date?: string;
  industry_count: number;
  download_in_progress: boolean;
}
