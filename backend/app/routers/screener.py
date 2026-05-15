from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.backtest import ScreenerRequest
from app.schemas.stock import ApiResponse

router = APIRouter(prefix="/screener", tags=["screener"])


@router.post("/search", response_model=ApiResponse)
def screen_stocks(req: ScreenerRequest, db: Session = Depends(get_db)):
    from app.services.screener_service import ScreenerService

    svc = ScreenerService(db)
    results = svc.screen(req)
    return ApiResponse(data=results)
