from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import (
    ICAnalysisParams,
    HeatmapParams,
    CorrelationParams,
)
from app.schemas.stock import ApiResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/ic", response_model=ApiResponse)
def compute_ic(params: ICAnalysisParams, db: Session = Depends(get_db)):
    from app.services.analysis_service import AnalysisService

    svc = AnalysisService(db)
    results = []
    for fc in params.factor_codes:
        ic_series = svc.compute_ic_series(
            fc, params.start_date, params.end_date, params.forward_period
        )
        summary = svc.compute_ic_summary(ic_series)
        results.append(
            {
                "factor_code": fc,
                **summary,
                "ic_series": ic_series,
            }
        )
    return ApiResponse(data=results)


@router.post("/heatmap", response_model=ApiResponse)
def factor_heatmap(params: HeatmapParams, db: Session = Depends(get_db)):
    from app.services.analysis_service import AnalysisService

    svc = AnalysisService(db)
    data = svc.compute_factor_heatmap(
        params.factor_codes, params.start_date, params.end_date
    )
    return ApiResponse(data=data)


@router.post("/correlation", response_model=ApiResponse)
def factor_correlation(params: CorrelationParams, db: Session = Depends(get_db)):
    from app.services.analysis_service import AnalysisService

    svc = AnalysisService(db)
    result = svc.compute_correlation_matrix(
        params.factor_codes, params.trade_date, params.start_date, params.end_date
    )
    return ApiResponse(data=result)


@router.get("/factor-returns/{factor_code}", response_model=ApiResponse)
def factor_returns(
    factor_code: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    n_quantiles: int = Query(5, ge=2, le=10),
    db: Session = Depends(get_db),
):
    from datetime import date as date_type
    from app.services.analysis_service import AnalysisService

    svc = AnalysisService(db)
    sd = date_type.fromisoformat(start_date)
    ed = date_type.fromisoformat(end_date)
    result = svc.compute_factor_returns(factor_code, sd, ed, n_quantiles)
    return ApiResponse(data=result)
