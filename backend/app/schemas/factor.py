from pydantic import BaseModel
from typing import Optional, Any
from datetime import date


class FactorCatalogOut(BaseModel):
    code: str
    name: str
    name_cn: Optional[str] = None
    category: str
    sub_category: Optional[str] = None
    description: Optional[str] = None
    formula: Optional[str] = None
    source: Optional[str] = None
    polarity: str
    data_requirements: Optional[Any] = None
    parameters: Optional[Any] = None
    paper_reference: Optional[str] = None
    status: str = "active"
    popularity: int = 0

    class Config:
        from_attributes = True


class FactorCategoryOut(BaseModel):
    category: str
    count: int


class FactorValuesOut(BaseModel):
    factor_code: str
    ts_code: str
    trade_date: date
    raw_value: Optional[float] = None
    normalized_value: Optional[float] = None
    percentile: Optional[float] = None

    class Config:
        from_attributes = True


class FactorComputeRequest(BaseModel):
    factor_code: str
    start_date: date
    end_date: date


class FactorDetailOut(FactorCatalogOut):
    recent_values: Optional[list] = None
    ic_summary: Optional[dict] = None
