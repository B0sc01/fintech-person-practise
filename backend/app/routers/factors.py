from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.factor import FactorCatalog, FactorValues
from app.schemas.factor import FactorCatalogOut, FactorDetailOut, FactorComputeRequest
from app.schemas.stock import ApiResponse

router = APIRouter(prefix="/factors", tags=["factors"])


@router.get("", response_model=ApiResponse)
def list_factors(
    category: str = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(FactorCatalog).filter(FactorCatalog.status == status)
    if category:
        q = q.filter(FactorCatalog.category == category)

    total = q.count()
    items = (
        q.order_by(FactorCatalog.category, FactorCatalog.popularity.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ApiResponse(
        data={
            "items": [FactorCatalogOut.model_validate(f).model_dump() for f in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/categories", response_model=ApiResponse)
def factor_categories(db: Session = Depends(get_db)):
    rows = (
        db.query(FactorCatalog.category, func.count(FactorCatalog.id).label("cnt"))
        .filter(FactorCatalog.status == "active")
        .group_by(FactorCatalog.category)
        .order_by(FactorCatalog.category)
        .all()
    )
    cats = [{"category": r[0], "count": r[1]} for r in rows]
    return ApiResponse(data=cats)


@router.get("/{factor_code}", response_model=ApiResponse)
def factor_detail(factor_code: str, db: Session = Depends(get_db)):
    factor = (
        db.query(FactorCatalog)
        .filter(FactorCatalog.code == factor_code)
        .first()
    )
    if not factor:
        return ApiResponse(code=1, message="Factor not found")

    detail = FactorCatalogOut.model_validate(factor).model_dump()

    recent_vals = (
        db.query(FactorValues)
        .filter(FactorValues.factor_code == factor_code)
        .order_by(FactorValues.trade_date.desc())
        .limit(100)
        .all()
    )
    detail["recent_values"] = [
        {
            "ts_code": v.ts_code,
            "trade_date": str(v.trade_date),
            "raw_value": v.raw_value,
            "normalized_value": v.normalized_value,
        }
        for v in recent_vals
    ]
    return ApiResponse(data=detail)


@router.get("/popular", response_model=ApiResponse)
def popular_factors(db: Session = Depends(get_db)):
    factors = (
        db.query(FactorCatalog)
        .filter(FactorCatalog.status == "active")
        .order_by(FactorCatalog.popularity.desc())
        .limit(10)
        .all()
    )
    return ApiResponse(
        data=[FactorCatalogOut.model_validate(f).model_dump() for f in factors]
    )


@router.post("/compute", response_model=ApiResponse)
def compute_factor(req: FactorComputeRequest, db: Session = Depends(get_db)):
    from app.services.factor_engine import FactorEngine

    engine = FactorEngine(db)
    try:
        count = engine.compute_factor_range(req.factor_code, req.start_date, req.end_date)
        return ApiResponse(
            message=f"Computed {count} rows",
            data={"rows_computed": count},
        )
    except ValueError as e:
        return ApiResponse(code=1, message=str(e))
