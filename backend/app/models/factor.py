from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class FactorCatalog(Base):
    __tablename__ = "factor_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    name_cn = Column(String(100))
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50))
    description = Column(Text)
    formula = Column(Text)
    python_function = Column(String(100))
    parameters = Column(JSON)
    source = Column(String(100))
    paper_reference = Column(String(500))
    polarity = Column(String(10), nullable=False, default="positive")
    data_requirements = Column(JSON)
    status = Column(String(20), default="active")
    popularity = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FactorValues(Base):
    __tablename__ = "factor_values"
    __table_args__ = (UniqueConstraint("factor_code", "ts_code", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code = Column(String(50), nullable=False, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    raw_value = Column(Float)
    normalized_value = Column(Float)
    percentile = Column(Float)
