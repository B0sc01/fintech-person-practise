from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.factor import FactorValues
from app.services.data_service import DataService


class BacktestService:
    def __init__(self, db: Session):
        self.db = db
        self.ds = DataService(db)

    def run_factor_quantile(
        self,
        factor_code: str,
        start_date: date,
        end_date: date,
        n_quantiles: int = 5,
        top_quantile: int = 1,
    ) -> dict:
        """Backtest long-only top-quantile factor strategy."""
        # Load factor values
        rows = (
            self.db.query(FactorValues)
            .filter(
                FactorValues.factor_code == factor_code,
                FactorValues.trade_date >= start_date,
                FactorValues.trade_date <= end_date,
                FactorValues.normalized_value.isnot(None),
            )
            .all()
        )
        if not rows:
            return {"error": "No factor data found"}

        factor_df = pd.DataFrame(
            [(r.ts_code, r.trade_date, r.normalized_value) for r in rows],
            columns=["ts_code", "trade_date", "factor_value"],
        )

        # Assign quantile ranks each day
        quantiles = factor_df.groupby("trade_date")["factor_value"].transform(
            lambda x: pd.qcut(x.rank(method="first"), n_quantiles, labels=False, duplicates="drop")
        )
        factor_df["quantile"] = quantiles
        factor_df = factor_df.dropna(subset=["quantile"])

        # Select top quantile
        target_q = n_quantiles - top_quantile
        top_stocks = factor_df[factor_df["quantile"] == target_q]

        # Load daily returns
        returns_df = self._get_daily_returns(start_date, end_date)
        if returns_df.empty:
            return {"error": "No return data found"}

        top_stocks = top_stocks.merge(returns_df, on=["ts_code", "trade_date"])

        # Equal-weighted portfolio daily returns
        portfolio = top_stocks.groupby("trade_date")["daily_return"].mean().sort_index()
        if portfolio.empty:
            return {"error": "Empty portfolio"}

        cumulative = (1 + portfolio).cumprod()
        total_return = float(cumulative.iloc[-1] - 1)
        n_days = len(portfolio)
        annual_return = float((1 + total_return) ** (252 / n_days) - 1) if n_days > 0 else 0
        volatility = float(portfolio.std() * np.sqrt(252))
        sharpe = float(annual_return / volatility) if volatility > 0 else 0
        max_dd = float((cumulative / cumulative.cummax() - 1).min())
        win_rate = float((portfolio > 0).sum() / n_days) if n_days > 0 else 0

        equity_curve = [
            {"date": str(idx), "value": float(cumulative[idx]), "drawdown": float(cumulative[idx] / cumulative.loc[:idx].max() - 1)}
            for idx in cumulative.index
        ]

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "equity_curve": equity_curve,
        }

    def _get_daily_returns(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get daily returns from OHLCV data."""
        df = self.ds.load_daily_panel(start_date, end_date, ["close"])
        if df.empty:
            return pd.DataFrame()

        pivot = df.pivot(index="trade_date", columns="ts_code", values="close")
        pivot = pivot.sort_index()
        returns = pivot.pct_change(fill_method=None)

        result = returns.reset_index().melt(
            id_vars="trade_date", var_name="ts_code", value_name="daily_return"
        )
        result = result.dropna(subset=["daily_return"])
        result["trade_date"] = result["trade_date"].dt.date
        return result
