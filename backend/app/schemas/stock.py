from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class StockBasicOut(BaseModel):
    ts_code: str
    name: str
    industry: Optional[str] = None
    area: Optional[str] = None
    list_date: Optional[date] = None
    is_hs: bool = False

    class Config:
        from_attributes = True


class StockDailyOut(BaseModel):
    ts_code: str
    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    pre_close: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    total_mv: Optional[float] = None
    circ_mv: Optional[float] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class ApiResponse(BaseModel):
    code: int = 0
    data: Optional[dict | list] = None
    message: str = "ok"


class DataStatusOut(BaseModel):
    stock_count: int
    daily_count: int
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    industry_count: int
    download_in_progress: bool = False


class DownloadRequest(BaseModel):
    start_date: date
    end_date: date
    stock_codes: Optional[list[str]] = None
