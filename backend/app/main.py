from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import dashboard, factors, analysis, screener, backtest, data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.services.factor_engine import FactorEngine
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        engine = FactorEngine(db)
        seeded = engine.seed_factor_catalog()
        if seeded > 0:
            import logging
            logging.getLogger("uvicorn").info(f"Seeded {seeded} factors into catalog")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(factors.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(screener.router, prefix=settings.API_V1_PREFIX)
app.include_router(backtest.router, prefix=settings.API_V1_PREFIX)
app.include_router(data.router, prefix=settings.API_V1_PREFIX)


@app.get(f"{settings.API_V1_PREFIX}/health")
def health_check():
    return {"code": 0, "message": "ok"}
