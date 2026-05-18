from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.factor import FactorValues
from app.services.data_service import DataService


class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.ds = DataService(db)

    def compute_ic_series(
        self, factor_code: str, start_date: date, end_date: date, forward_period: int = 1
    ) -> list[dict]:
        """Compute daily cross-sectional IC (Pearson + Spearman) between factor value and forward return."""
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
            return []

        factor_df = pd.DataFrame(
            [(r.ts_code, r.trade_date, r.normalized_value) for r in rows],
            columns=["ts_code", "trade_date", "factor_value"],
        )

        # Load returns from daily data
        returns_df = self._compute_forward_returns(start_date, end_date, forward_period)
        if returns_df.empty:
            return []

        # Merge factor values with forward returns
        merged = factor_df.merge(returns_df, on=["ts_code", "trade_date"])
        if merged.empty:
            return []

        ic_series = []
        for trade_date, group in merged.groupby("trade_date"):
            if len(group) < 30:
                continue
            pearson = group["factor_value"].corr(group["forward_return"])
            spearman = group["factor_value"].corr(group["forward_return"], method="spearman")
            ic_series.append(
                {
                    "trade_date": str(trade_date),
                    "ic_pearson": float(pearson) if not np.isnan(pearson) else 0,
                    "ic_spearman": float(spearman) if not np.isnan(spearman) else 0,
                }
            )

        return ic_series

    def compute_ic_summary(self, ic_series: list[dict]) -> dict:
        """Summarize IC series statistics."""
        if not ic_series:
            return {
                "ic_mean": 0,
                "ic_std": 0,
                "ir": 0,
                "ic_positive_ratio": 0,
                "t_stat": 0,
            }

        ics = [d["ic_pearson"] for d in ic_series]
        ic_mean = np.mean(ics)
        ic_std = np.std(ics, ddof=1)
        ir = ic_mean / ic_std if ic_std > 0 else 0
        pos_ratio = sum(1 for x in ics if x > 0) / len(ics)
        t_stat = ic_mean / (ic_std / np.sqrt(len(ics))) if ic_std > 0 else 0

        return {
            "ic_mean": float(ic_mean),
            "ic_std": float(ic_std),
            "ir": float(ir),
            "ic_positive_ratio": float(pos_ratio),
            "t_stat": float(t_stat),
        }

    def _compute_forward_returns(
        self, start_date: date, end_date: date, forward_period: int = 1
    ) -> pd.DataFrame:
        """Compute forward N-day returns for all stocks."""
        df = self.ds.load_daily_panel(start_date, end_date, ["close"])
        if df.empty:
            return pd.DataFrame()

        pivot = df.pivot(index="trade_date", columns="ts_code", values="close")
        pivot = pivot.sort_index()

        # Forward return = (P_{t+N} - P_t) / P_t
        shifted = pivot.shift(-forward_period)
        returns = (shifted - pivot) / pivot

        result = returns.reset_index().melt(
            id_vars="trade_date", var_name="ts_code", value_name="forward_return"
        )
        result = result.dropna(subset=["forward_return"])
        result["trade_date"] = result["trade_date"].dt.date
        return result

    def compute_factor_heatmap(
        self, factor_codes: list[str], start_date: date, end_date: date
    ) -> dict:
        """Compute monthly average factor returns for heatmap display."""
        result = {"factors": factor_codes, "months": [], "data": []}
        if not factor_codes:
            return result

        # For each factor, compute monthly IC
        for fc in factor_codes:
            ic_series = self.compute_ic_series(fc, start_date, end_date)
            if not ic_series:
                result["data"].append([0])
                continue
            # Group by month
            df = pd.DataFrame(ic_series)
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df["month"] = df["trade_date"].dt.to_period("M")
            monthly = df.groupby("month")["ic_pearson"].mean().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            if not result["months"]:
                result["months"] = monthly["month"].tolist()
            result["data"].append(monthly["ic_pearson"].tolist())

        return result

    def compute_correlation_matrix(
        self,
        factor_codes: list[str],
        trade_date: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Compute cross-sectional factor correlation matrix."""
        if not factor_codes:
            return {"factors": [], "matrix": []}

        # Load factor values for the latest date in range, or specified date
        all_rows = []
        for fc in factor_codes:
            q = self.db.query(FactorValues).filter(
                FactorValues.factor_code == fc,
                FactorValues.normalized_value.isnot(None),
            )
            if trade_date:
                q = q.filter(FactorValues.trade_date == trade_date)
            elif start_date and end_date:
                q = q.filter(
                    FactorValues.trade_date >= start_date,
                    FactorValues.trade_date <= end_date,
                )
            rows = q.order_by(FactorValues.trade_date.desc()).limit(500).all()
            for r in rows:
                all_rows.append((fc, r.ts_code, r.trade_date, r.normalized_value))

        if not all_rows:
            n = len(factor_codes)
            matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
            return {"factors": factor_codes, "matrix": matrix}

        df = pd.DataFrame(all_rows, columns=["factor", "ts_code", "trade_date", "value"])
        pivot = df.pivot_table(
            index=["ts_code", "trade_date"], columns="factor", values="value", aggfunc="mean"
        ).dropna()

        if pivot.empty:
            n = len(factor_codes)
            matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
            return {"factors": factor_codes, "matrix": matrix}

        corr = pivot.corr()
        matrix = []
        for fc1 in factor_codes:
            row = []
            for fc2 in factor_codes:
                if fc1 in corr.index and fc2 in corr.columns:
                    row.append(round(float(corr.loc[fc1, fc2]), 4))
                else:
                    row.append(0.0)
            matrix.append(row)

        return {"factors": factor_codes, "matrix": matrix}

    def compute_factor_returns(
        self, factor_code: str, start_date: date, end_date: date, n_quantiles: int = 5
    ) -> dict:
        """Compute cumulative returns by factor quantile."""
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
            return {"factor_code": factor_code, "quantile_returns": {}, "cumulative_returns": {}}

        factor_df = pd.DataFrame(
            [(r.ts_code, r.trade_date, r.normalized_value) for r in rows],
            columns=["ts_code", "trade_date", "factor_value"],
        )

        # Assign quantile per date
        quantiles = factor_df.groupby("trade_date")["factor_value"].transform(
            lambda x: pd.qcut(x.rank(method="first"), n_quantiles, labels=False, duplicates="drop")
        )
        factor_df["quantile"] = quantiles
        factor_df = factor_df.dropna(subset=["quantile"])
        factor_df["quantile"] = factor_df["quantile"].astype(int)

        # Load daily returns
        returns_df = self._compute_forward_returns(start_date, end_date, 1)
        if returns_df.empty:
            return {"factor_code": factor_code, "quantile_returns": {}, "cumulative_returns": {}}

        merged = factor_df.merge(returns_df, on=["ts_code", "trade_date"])

        result = {"factor_code": factor_code, "quantile_returns": {}, "cumulative_returns": {}}

        for q in range(n_quantiles):
            q_data = merged[merged["quantile"] == q]
            if q_data.empty:
                continue
            daily = q_data.groupby("trade_date")["forward_return"].mean().reset_index()
            daily = daily.sort_values("trade_date")
            daily["cumulative"] = (1 + daily["forward_return"]).cumprod()
            result["quantile_returns"][q] = [
                {"date": str(r.trade_date), "daily_return": float(r.forward_return)}
                for _, r in daily.iterrows()
            ]
            result["cumulative_returns"][q] = [
                {"date": str(r.trade_date), "value": float(r.cumulative)}
                for _, r in daily.iterrows()
            ]

        return result
