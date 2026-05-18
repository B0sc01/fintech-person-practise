from pydantic import BaseModel
from typing import Optional
from datetime import date


class ScreenerCondition(BaseModel):
    factor_code: str
    operator: str
    value: float


class ScreenerRequest(BaseModel):
    conditions: list[ScreenerCondition] = []
    logic: str = "AND"
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = 1
    page_size: int = 50


class ScreenerResultOut(BaseModel):
    ts_code: str
    stock_name: Optional[str] = None
    matching_factors: dict
    sort_value: Optional[float] = None


class BacktestRequest(BaseModel):
    name: str
    factor_code: str
    strategy_type: str = "factor_quantile"
    start_date: date
    end_date: date
    n_quantiles: int = 5
    top_quantile: int = 1
    rebalance_freq: str = "daily"


class BacktestResultOut(BaseModel):
    id: int
    name: str
    status: str
    total_return: Optional[float] = None
    annual_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    equity_curve: Optional[list[dict]] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
