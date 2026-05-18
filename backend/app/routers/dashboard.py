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
    total_stocks = db.query(func.count(StockBasic.id)).scalar()
    latest_date = db.query(func.max(StockDaily.trade_date)).scalar()

    recent_data = None
    week_ago_data = None
    if latest_date:
        recent_data = (
            db.query(
                func.avg(StockDaily.close),
                func.sum(StockDaily.amount),
            )
            .filter(StockDaily.trade_date == latest_date)
            .first()
        )

        # Find trading day ~5 trading days ago
        prev_dates = (
            db.query(StockDaily.trade_date)
            .filter(StockDaily.trade_date < latest_date)
            .distinct()
            .order_by(StockDaily.trade_date.desc())
            .limit(5)
            .all()
        )
        if len(prev_dates) >= 5:
            week_ago_date = prev_dates[-1][0]
            week_ago_data = (
                db.query(func.avg(StockDaily.close))
                .filter(StockDaily.trade_date == week_ago_date)
                .scalar()
            )

    avg_close = float(recent_data[0]) if recent_data and recent_data[0] else 0
    prev_avg_close = float(week_ago_data) if week_ago_data else 0
    week_change_pct = ((avg_close - prev_avg_close) / prev_avg_close * 100) if prev_avg_close > 0 else 0

    return ApiResponse(
        data={
            "total_stocks": total_stocks,
            "latest_trade_date": str(latest_date) if latest_date else None,
            "avg_close": avg_close,
            "total_amount": float(recent_data[1]) if recent_data and recent_data[1] else 0,
            "week_change_pct": round(week_change_pct, 2),
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
