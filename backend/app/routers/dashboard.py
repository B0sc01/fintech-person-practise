from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.database import get_db
from app.models.stock import StockDaily, StockBasic
from app.schemas.stock import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=ApiResponse)
def dashboard_overview(db: Session = Depends(get_db)):
    today = date.today()
    week_ago = today - timedelta(days=7)

    total_stocks = db.query(func.count(StockBasic.id)).scalar()
    latest_date = db.query(func.max(StockDaily.trade_date)).scalar()

    recent_data = []
    if latest_date:
        recent_data = (
            db.query(
                func.avg(StockDaily.close),
                func.sum(StockDaily.amount),
            )
            .filter(StockDaily.trade_date == latest_date)
            .first()
        )

    return ApiResponse(
        data={
            "total_stocks": total_stocks,
            "latest_trade_date": str(latest_date) if latest_date else None,
            "avg_close": float(recent_data[0]) if recent_data and recent_data[0] else 0,
            "total_amount": float(recent_data[1]) if recent_data and recent_data[1] else 0,
        }
    )


@router.get("/index-performance", response_model=ApiResponse)
def index_performance(db: Session = Depends(get_db)):
    """Aggregated daily performance across all stocks as a proxy for market index."""
    rows = (
        db.query(
            StockDaily.trade_date,
            func.avg(StockDaily.close).label("avg_close"),
            func.sum(StockDaily.amount).label("total_amount"),
            func.count(func.distinct(StockDaily.ts_code)).label("stock_count"),
        )
        .filter(StockDaily.trade_date >= date.today() - timedelta(days=60))
        .group_by(StockDaily.trade_date)
        .order_by(StockDaily.trade_date)
        .all()
    )
    data = [
        {
            "date": str(r.trade_date),
            "avg_close": float(r.avg_close) if r.avg_close else 0,
            "total_amount": float(r.total_amount) if r.total_amount else 0,
            "stock_count": r.stock_count,
        }
        for r in rows
    ]
    return ApiResponse(data=data)
