from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class StockBasic(Base):
    __tablename__ = "stock_basic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(50), nullable=False)
    industry = Column(String(50))
    area = Column(String(20))
    list_date = Column(Date)
    delist_date = Column(Date)
    is_hs = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StockDaily(Base):
    __tablename__ = "stock_daily"
    __table_args__ = (UniqueConstraint("ts_code", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    turnover_rate = Column(Float)
    pe_ttm = Column(Float)
    pb = Column(Float)
    total_mv = Column(Float)
    circ_mv = Column(Float)
