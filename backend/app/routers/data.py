import threading
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_service import DataService
from app.schemas.stock import (
    ApiResponse,
    StockBasicOut,
    StockDailyOut,
    DataStatusOut,
    DownloadRequest,
    PaginatedResponse,
)

router = APIRouter(prefix="/data", tags=["data"])

_download_progress: dict = {"in_progress": False, "current": 0, "total": 0}


@router.get("/status", response_model=ApiResponse)
def data_status(db: Session = Depends(get_db)):
    svc = DataService(db)
    status = svc.get_status()
    status["download_in_progress"] = _download_progress["in_progress"]
    return ApiResponse(data=status)


@router.get("/stocks", response_model=ApiResponse)
def list_stocks(
    industry: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    svc = DataService(db)
    items, total = svc.get_stocks(industry, page, page_size)
    return ApiResponse(
        data={
            "items": [StockBasicOut.model_validate(s) for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/stocks/{ts_code}/daily", response_model=ApiResponse)
def get_stock_daily(
    ts_code: str,
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
):
    from datetime import date as date_type

    svc = DataService(db)
    sd = date_type.fromisoformat(start_date) if start_date else None
    ed = date_type.fromisoformat(end_date) if end_date else None
    rows = svc.get_daily_data(ts_code, sd, ed)
    return ApiResponse(data=[StockDailyOut.model_validate(r) for r in rows])


@router.post("/download/stock-list", response_model=ApiResponse)
def download_stock_list(db: Session = Depends(get_db)):
    svc = DataService(db)
    count = svc.download_stock_list()
    return ApiResponse(data={"count": count}, message=f"Downloaded {count} stocks")


@router.post("/download/daily", response_model=ApiResponse)
def download_daily(req: DownloadRequest, db: Session = Depends(get_db)):
    if _download_progress["in_progress"]:
        return ApiResponse(code=1, message="Download already in progress")

    _download_progress["in_progress"] = True
    _download_progress["current"] = 0
    _download_progress["total"] = 0

    def progress_cb(current, total):
        _download_progress["current"] = current
        _download_progress["total"] = total

    def run():
        svc = DataService(db)
        try:
            svc.download_daily_batch(
                req.start_date, req.end_date, req.stock_codes, progress_cb
            )
        finally:
            _download_progress["in_progress"] = False

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return ApiResponse(message="Download started", data={"status": "started"})


@router.get("/download/progress", response_model=ApiResponse)
def download_progress():
    return ApiResponse(data=_download_progress)


@router.get("/date-range", response_model=ApiResponse)
def date_range(db: Session = Depends(get_db)):
    svc = DataService(db)
    return ApiResponse(data=svc.get_date_range())


@router.get("/industries", response_model=ApiResponse)
def industries(db: Session = Depends(get_db)):
    svc = DataService(db)
    return ApiResponse(data=svc.get_industries())
