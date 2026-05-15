from pydantic import BaseModel
from typing import Optional
from datetime import date


class ICAnalysisParams(BaseModel):
    factor_codes: list[str]
    start_date: date
    end_date: date
    forward_period: int = 1


class ICAnalysisOut(BaseModel):
    factor_code: str
    ic_mean: float
    ic_std: float
    ir: float
    ic_positive_ratio: float
    t_stat: float
    ic_series: list[dict]


class HeatmapParams(BaseModel):
    factor_codes: list[str]
    start_date: date
    end_date: date


class CorrelationParams(BaseModel):
    factor_codes: list[str]
    trade_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CorrelationOut(BaseModel):
    factors: list[str]
    matrix: list[list[float]]
    trade_date: Optional[date] = None


class FactorReturnOut(BaseModel):
    factor_code: str
    quantile_returns: dict[int, list[dict]]
    cumulative_returns: dict[int, list[dict]]
