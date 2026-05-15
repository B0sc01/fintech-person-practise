from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


class FactorIC(Base):
    __tablename__ = "factor_ic"
    __table_args__ = (UniqueConstraint("factor_code", "trade_date", "forward_period"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code = Column(String(50), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    ic_pearson = Column(Float)
    ic_spearman = Column(Float)
    forward_period = Column(Integer, default=1)


class FactorPerformance(Base):
    __tablename__ = "factor_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code = Column(String(50), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    ic_mean = Column(Float)
    ic_std = Column(Float)
    ir = Column(Float)
    ic_positive_ratio = Column(Float)
    t_stat = Column(Float)
    cumulative_return = Column(Float)
    annualized_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    forward_period = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class FactorCorrelation(Base):
    __tablename__ = "factor_correlation"
    __table_args__ = (UniqueConstraint("factor_code_1", "factor_code_2", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_code_1 = Column(String(50), nullable=False)
    factor_code_2 = Column(String(50), nullable=False)
    trade_date = Column(Date, nullable=False)
    correlation = Column(Float)


class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    start_date = Column(Date)
    end_date = Column(Date)
    total_return = Column(Float)
    annual_return = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    turnover = Column(Float)
    result_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
