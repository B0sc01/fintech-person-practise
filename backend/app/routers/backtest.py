import json
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import BacktestJob
from app.schemas.backtest import BacktestRequest, BacktestResultOut
from app.schemas.stock import ApiResponse

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=ApiResponse)
def run_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    job = BacktestJob(
        name=req.name,
        strategy_type=req.strategy_type,
        parameters=json.loads(req.model_dump_json()),
        status="pending",
        start_date=req.start_date,
        end_date=req.end_date,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id

    def execute():
        from app.database import SessionLocal
        from app.services.backtest_service import BacktestService

        local_db = SessionLocal()
        try:
            svc = BacktestService(local_db)
            result = svc.run_factor_quantile(
                req.factor_code,
                req.start_date,
                req.end_date,
                req.n_quantiles,
                req.top_quantile,
            )
            bt_job = local_db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if bt_job:
                bt_job.status = "completed"
                bt_job.total_return = result.get("total_return")
                bt_job.annual_return = result.get("annual_return")
                bt_job.volatility = result.get("volatility")
                bt_job.sharpe_ratio = result.get("sharpe_ratio")
                bt_job.max_drawdown = result.get("max_drawdown")
                bt_job.win_rate = result.get("win_rate")
                bt_job.result_data = result
                bt_job.completed_at = datetime.now()
                local_db.commit()
        except Exception as exc:
            bt_job = local_db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if bt_job:
                bt_job.status = "failed"
                bt_job.error_message = str(exc)
                local_db.commit()
        finally:
            local_db.close()

    threading.Thread(target=execute, daemon=True).start()
    return ApiResponse(data={"job_id": job_id}, message="Backtest started")


@router.get("/{job_id}", response_model=ApiResponse)
def get_backtest(job_id: int, db: Session = Depends(get_db)):
    job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
    if not job:
        return ApiResponse(code=1, message="Backtest not found")

    data = BacktestResultOut.model_validate(job).model_dump()
    if job.result_data:
        data["equity_curve"] = job.result_data.get("equity_curve")
    return ApiResponse(data=data)


@router.get("", response_model=ApiResponse)
def list_backtests(db: Session = Depends(get_db)):
    jobs = (
        db.query(BacktestJob)
        .order_by(BacktestJob.created_at.desc())
        .limit(20)
        .all()
    )
    return ApiResponse(
        data=[BacktestResultOut.model_validate(j).model_dump() for j in jobs]
    )
