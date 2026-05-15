export interface FactorCatalog {
  code: string;
  name: string;
  name_cn?: string;
  category: string;
  sub_category?: string;
  description?: string;
  formula?: string;
  source?: string;
  polarity: string;
  data_requirements?: string[];
  parameters?: Record<string, unknown>;
  paper_reference?: string;
  status: string;
  popularity: number;
}

export interface FactorDetail extends FactorCatalog {
  recent_values?: FactorValue[];
  ic_summary?: Record<string, number>;
}

export interface FactorValue {
  ts_code: string;
  trade_date: string;
  raw_value: number;
  normalized_value: number;
  percentile?: number;
}

export interface FactorCategory {
  category: string;
  count: number;
}
