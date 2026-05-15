from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.factor_library import get_factor_registry
from app.models.factor import FactorCatalog


class FactorEngine:
    def __init__(self, db: Session):
        self.db = db

    def seed_factor_catalog(self) -> int:
        """Insert all factors from the registry into factor_catalog table."""
        registry = get_factor_registry()
        count = 0
        for code, meta in registry.items():
            existing = self.db.query(FactorCatalog).filter(FactorCatalog.code == code).first()
            if existing:
                continue
            self.db.add(
                FactorCatalog(
                    code=code,
                    name=meta["name"],
                    name_cn=meta["name_cn"],
                    category=meta["category"],
                    sub_category=meta.get("sub_category", ""),
                    description=meta.get("description", ""),
                    formula=meta.get("formula", ""),
                    source=meta.get("source", "custom"),
                    polarity=meta.get("polarity", "positive"),
                    data_requirements=meta.get("data_requirements", []),
                    parameters=meta.get("parameters", {}),
                    paper_reference=meta.get("paper_reference", ""),
                    python_function=meta.get("python_function", ""),
                    status="active",
                )
            )
            count += 1
        self.db.commit()
        return count

    def compute_factor_range(
        self, factor_code: str, start_date: date, end_date: date
    ) -> int:
        """Compute a factor for all stocks across a date range."""
        registry = get_factor_registry()
        if factor_code not in registry:
            raise ValueError(f"Unknown factor: {factor_code}")

        from app.services.data_service import DataService

        ds = DataService(self.db)
        df = ds.load_daily_panel(start_date, end_date, ["close", "open", "high", "low", "volume"])
        if df.empty:
            return 0

        trading_days = sorted(df["trade_date"].unique())
        total = 0
        for td in trading_days:
            count = self._compute_single_date(factor_code, pd.Timestamp(td).date(), df)
            total += count

        # Update popularity count
        self.db.query(FactorCatalog).filter(FactorCatalog.code == factor_code).update(
            {FactorCatalog.popularity: FactorCatalog.popularity + 1}
        )
        self.db.commit()

        return total

    def _compute_single_date(
        self, factor_code: str, trade_date: date, df: pd.DataFrame
    ) -> int:
        """Compute factor values for all stocks on a single date."""
        registry = get_factor_registry()
        meta = registry[factor_code]
        source = meta.get("source", "custom")

        # Pivot data panels
        close_pivot = self._pivot(df, "close")
        open_pivot = self._pivot(df, "open")
        high_pivot = self._pivot(df, "high")
        low_pivot = self._pivot(df, "low")
        volume_pivot = self._pivot(df, "volume")

        stocks = close_pivot.columns.tolist()
        if not stocks:
            return 0

        try:
            if source == "TA-Lib":
                raw_array = self._compute_talib(factor_code, meta, close_pivot, high_pivot, low_pivot, volume_pivot)
            elif source == "Alpha101":
                raw_array = self._compute_alpha101(factor_code, meta, close_pivot, open_pivot, high_pivot, low_pivot, volume_pivot)
            else:
                raw_array = self._compute_custom(factor_code, meta, close_pivot, open_pivot, high_pivot, low_pivot, volume_pivot)
        except Exception:
            return 0

        if raw_array is None:
            return 0

        raw_values = raw_array[-1] if raw_array.ndim == 2 else raw_array
        if len(raw_values) != len(stocks):
            return 0

        return self._insert_values(factor_code, trade_date, stocks, raw_values)

    def _pivot(self, df: pd.DataFrame, field: str) -> pd.DataFrame:
        piv = df.pivot(index="trade_date", columns="ts_code", values=field)
        return piv.sort_index()

    # ---- TA-Lib dispatch ----
    def _compute_talib(self, code, meta, close, high, low, volume) -> np.ndarray | None:
        try:
            import talib
        except ImportError:
            return None

        values = close.values.astype(np.float64)
        n_cols = values.shape[1]
        params = meta.get("parameters", {})
        tp = params.get("timeperiod", 14)
        result = np.full_like(values, np.nan)

        talib_map = {
            "rsi": lambda v, tp: talib.RSI(v.T, timeperiod=tp).T if v.ndim == 2 else talib.RSI(v, timeperiod=tp),
            "macd": lambda v, **kw: talib.MACD(v.T, fastperiod=kw.get("fast", 12), slowperiod=kw.get("slow", 26), signalperiod=kw.get("signal", 9)),
            "bb_": lambda v, tp: talib.BBANDS(v.T, timeperiod=tp, nbdevup=params.get("nbdev", 2), nbdevdn=params.get("nbdev", 2), matype=0),
            "atr": lambda v, tp: talib.ATR(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), timeperiod=tp),
            "obv": lambda v, **kw: talib.OBV(v.T, volume.values.T.astype(np.float64)),
            "williams": lambda v, tp: talib.WILLR(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), timeperiod=tp),
            "stoch": lambda v, tp: talib.STOCH(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), fastk_period=tp, slowk_period=params.get("slowk", 3), slowd_period=params.get("slowd", 3)),
            "cci": lambda v, tp: talib.CCI(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), timeperiod=tp),
            "adx": lambda v, tp: talib.ADX(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), timeperiod=tp),
            "mfi": lambda v, tp: talib.MFI(high.values.T.astype(np.float64), low.values.T.astype(np.float64), close.values.T.astype(np.float64), volume.values.T.astype(np.float64), timeperiod=tp),
            "roc": lambda v, tp: talib.ROC(v.T, timeperiod=tp).T,
            "ema": lambda v, tp: talib.EMA(v.T, timeperiod=tp).T,
            "trix": lambda v, tp: talib.TRIX(v.T, timeperiod=tp).T,
        }

        for key, fn in talib_map.items():
            if code.startswith(key):
                if key in ("macd",):
                    macd_result, signal, hist = fn(values, **params)
                    if code.endswith("_dif"):
                        return macd_result.T if macd_result.ndim == 2 else macd_result
                    elif code.endswith("_signal"):
                        return signal.T if signal.ndim == 2 else signal
                    else:
                        return hist.T if hist.ndim == 2 else hist
                if key == "stoch" and code == "stoch_k_14":
                    k, d = fn(values, tp)
                    return k.T
                if key == "stoch" and code == "stoch_d_3":
                    k, d = fn(values, tp)
                    return d.T
                if key == "bb_" and code == "bb_pct_b":
                    upper, middle, lower = fn(values, tp)
                    result = (values - lower) / (upper - lower + 1e-10)
                    return result
                if key == "bb_" and code == "bb_width":
                    upper, middle, lower = fn(values, tp)
                    result = (upper - lower) / (middle + 1e-10)
                    return result
                raw = fn(values, tp)
                if isinstance(raw, tuple):
                    raw = raw[0]
                return raw.T if raw.ndim == 2 and raw.shape[0] == values.shape[1] else raw

        return result

    # ---- Alpha101 stub ----
    def _compute_alpha101(self, code, meta, close, open_, high, low, volume) -> np.ndarray | None:
        values = close.values.astype(np.float64)
        alpha_handlers = {
            "alpha101": lambda c, o, h, l, v: (c - o) / ((h - l) + 0.001),
            "alpha003": lambda c, o, h, l, v: -1 * self._rolling_corr(
                self._rank(o), self._rank(v), 10
            ),
        }
        handler = alpha_handlers.get(code)
        if handler:
            return handler(values, open_.values.astype(np.float64) if open_ is not None else None,
                          high.values.astype(np.float64) if high is not None else None,
                          low.values.astype(np.float64) if low is not None else None,
                          volume.values.astype(np.float64) if volume is not None else None)
        # Default for unimplemented alphas: return close as placeholder
        return values

    # ---- Custom factors ----
    def _compute_custom(self, code, meta, close, open_, high, low, volume) -> np.ndarray | None:
        values = close.values.astype(np.float64) if close is not None else None
        if values is None:
            return None

        window = meta.get("parameters", {}).get("window", 20)
        n_rows, n_cols = values.shape

        # --- Momentum family ---
        if code.startswith("momentum_"):
            skip = meta.get("parameters", {}).get("skip", 0)
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_vals = values[:, col]
                valid = ~np.isnan(col_vals)
                if valid.sum() <= window:
                    continue
                valid_vals = col_vals[valid]
                ret = np.full(len(valid_vals), np.nan)
                for i in range(window, len(valid_vals)):
                    ret[i] = (valid_vals[i - skip] - valid_vals[i - window]) / (valid_vals[i - window] + 1e-10)
                full = np.full(len(col_vals), np.nan)
                full[valid] = ret
                result[:, col] = full
            return result

        if code == "momentum_acceleration":
            mom20 = self._momentum_array(values, 20, 1)
            mom60 = self._momentum_array(values, 60, 1)
            return mom20 - mom60

        if code == "return_reversal_5d":
            return -1 * self._momentum_array(values, 5, 0)

        if code == "volume_momentum_20d":
            if volume is None:
                return None
            vol = volume.values.astype(np.float64) if hasattr(volume, 'values') else volume
            avg5 = pd.DataFrame(vol).rolling(5).mean().values
            avg20 = pd.DataFrame(vol).rolling(20).mean().values
            return (avg5 - avg20) / (avg20 + 1e-10)

        # --- Volatility family ---
        if code.startswith("volatility_") and not code.startswith("volatility_ratio"):
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 1:
                    continue
                v = c[valid]
                r = np.diff(np.log(v + 1e-10))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full

            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = pd.Series(returns[:, col])
                rolling_std = col_r.rolling(window).std().values * np.sqrt(252)
                result[:, col] = rolling_std
            return result

        if code == "downside_volatility_20d":
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 1:
                    continue
                v = c[valid]
                r = np.diff(np.log(v + 1e-10))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = pd.Series(returns[:, col])
                downside = col_r.apply(lambda x: x if x < 0 else 0)
                rolling_down = downside.rolling(window).std().values * np.sqrt(252)
                result[:, col] = rolling_down
            return result

        if code == "max_drawdown_60d":
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_v = pd.Series(values[:, col]).dropna()
                if len(col_v) < window:
                    continue
                cummax = col_v.expanding().max()
                drawdown = (col_v - cummax) / (cummax + 1e-10)
                rolling_mdd = drawdown.rolling(window).min().values
                full = np.full(len(values[:, col]), np.nan)
                idx = col_v.index.tolist()
                full[idx[-len(rolling_mdd):]] = rolling_mdd
                result[:, col] = full
            return result

        if code == "beta_60d":
            if values.shape[0] < window:
                return None
            mkt_return = np.nanmean(
                np.diff(np.log(values + 1e-10), axis=0), axis=1
            )
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = np.diff(np.log(values[:, col] + 1e-10))
                col_r = np.concatenate([[np.nan], col_r])
                for t in range(window, len(col_r)):
                    if np.isnan(col_r[t]):
                        continue
                    stock = col_r[t - window:t]
                    mkt = mkt_return[t - window:t]
                    mask = ~np.isnan(stock) & ~np.isnan(mkt)
                    if mask.sum() < 10:
                        continue
                    cov = np.cov(stock[mask], mkt[mask])[0, 1]
                    var = np.var(mkt[mask])
                    result[t, col] = cov / var if var > 0 else np.nan
            return result

        if code == "skewness_20d":
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 2:
                    continue
                v = c[valid]
                r = np.diff(np.log(v + 1e-10))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = pd.Series(returns[:, col])
                result[:, col] = col_r.rolling(window).skew().values
            return result

        if code == "kurtosis_20d":
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 2:
                    continue
                v = c[valid]
                r = np.diff(np.log(v + 1e-10))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full
            result = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = pd.Series(returns[:, col])
                result[:, col] = col_r.rolling(window).kurt().values
            return result

        # --- SMA ratio family ---
        if code.startswith("sma_ratio_"):
            if code == "sma_ratio_5_20":
                sma5 = pd.DataFrame(values).rolling(5, min_periods=1).mean().values
                sma20 = pd.DataFrame(values).rolling(20, min_periods=1).mean().values
                return sma5 / (sma20 + 1e-10)
            if code == "sma_ratio_20_60":
                sma20 = pd.DataFrame(values).rolling(20, min_periods=1).mean().values
                sma60 = pd.DataFrame(values).rolling(60, min_periods=1).mean().values
                return sma20 / (sma60 + 1e-10)

        if code.startswith("sma_"):
            w = meta.get("parameters", {}).get("window", 20)
            sma = pd.DataFrame(values).rolling(w, min_periods=1).mean().values
            return values / (sma + 1e-10)

        # --- Size / Liquidity ---
        if code == "turnover_rate_avg_20d":
            if volume is None:
                return None
            vol = volume.values.astype(np.float64) if hasattr(volume, 'values') else volume
            return pd.DataFrame(vol).rolling(20).mean().values

        if code == "amihud_illiq_20d":
            if volume is None:
                return None
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 1:
                    continue
                v = c[valid]
                r = np.abs(np.diff(np.log(v + 1e-10)))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full
            vol = volume.values.astype(np.float64) if hasattr(volume, 'values') else volume
            dollar_vol = vol * values
            illiq = returns / (dollar_vol + 1e-10)
            return pd.DataFrame(illiq).rolling(20).mean().values

        # --- Sentiment ---
        if code == "close_to_high_20d":
            if high is None or low is None:
                return None
            h = high.values.astype(np.float64) if hasattr(high, 'values') else high
            l = low.values.astype(np.float64) if hasattr(low, 'values') else low
            hh = pd.DataFrame(h).rolling(20).max().values
            ll = pd.DataFrame(l).rolling(20).min().values
            return (values - ll) / (hh - ll + 1e-10)

        if code == "intraday_volatility_5d":
            if high is None or low is None:
                return None
            h = high.values.astype(np.float64) if hasattr(high, 'values') else high
            l = low.values.astype(np.float64) if hasattr(low, 'values') else low
            daily_range = (h - l) / (values + 1e-10)
            return pd.DataFrame(daily_range).rolling(5).mean().values

        if code == "price_gap_5d":
            if open_ is None:
                return None
            o = open_.values.astype(np.float64) if hasattr(open_, 'values') else open_
            shifted = pd.DataFrame(values).shift(5).values
            return (o - shifted) / (shifted + 1e-10)

        if code == "turnover_anomaly_20d":
            if volume is None:
                return None
            vol = volume.values.astype(np.float64) if hasattr(volume, 'values') else volume
            avg60 = pd.DataFrame(vol).rolling(60).mean().values
            return vol / (avg60 + 1e-10)

        if code == "circ_mv_ratio":
            return values  # placeholder — needs circ_mv + total_mv from DB

        # Value factors — need PE/PB data from DB, return placeholder for now
        if code in ("pe_ttm", "pb_ratio", "earnings_yield", "size_log_mv", "dividend_yield",
                    "roe", "roa", "gross_margin", "debt_to_equity", "asset_turnover"):
            return values

        # Combo
        if code == "momentum_quality_combo":
            mom = self._momentum_array(values, 20, 1)
            z_mom = (mom - np.nanmean(mom, axis=1, keepdims=True)) / (np.nanstd(mom, axis=1, keepdims=True) + 1e-10)
            z_qual = (values - np.nanmean(values, axis=1, keepdims=True)) / (np.nanstd(values, axis=1, keepdims=True) + 1e-10)
            return 0.5 * z_mom + 0.5 * z_qual

        if code == "value_volatility_combo":
            returns = np.full_like(values, np.nan)
            for col in range(n_cols):
                c = values[:, col]
                valid = ~np.isnan(c)
                if valid.sum() <= 1:
                    continue
                v = c[valid]
                r = np.diff(np.log(v + 1e-10))
                full = np.full(len(c), np.nan)
                full[valid] = np.concatenate([[np.nan], r])
                returns[:, col] = full
            vol20 = np.full_like(values, np.nan)
            for col in range(n_cols):
                col_r = pd.Series(returns[:, col])
                vol20[:, col] = col_r.rolling(20).std().values * np.sqrt(252)
            z_val = (values - np.nanmean(values, axis=1, keepdims=True)) / (np.nanstd(values, axis=1, keepdims=True) + 1e-10)
            z_vol = (-vol20 - np.nanmean(-vol20, axis=1, keepdims=True)) / (np.nanstd(-vol20, axis=1, keepdims=True) + 1e-10)
            return 0.5 * z_val + 0.5 * z_vol

        # Default: return latest raw values
        return values

    # ---- Helpers ----
    def _momentum_array(self, values, window, skip):
        result = np.full_like(values, np.nan)
        for col in range(values.shape[1]):
            col_vals = values[:, col]
            valid = ~np.isnan(col_vals)
            if valid.sum() <= window:
                continue
            valid_vals = col_vals[valid]
            ret = np.full(len(valid_vals), np.nan)
            for i in range(window, len(valid_vals)):
                ret[i] = (valid_vals[i - skip] - valid_vals[i - window]) / (valid_vals[i - window] + 1e-10)
            full = np.full(len(col_vals), np.nan)
            full[valid] = ret
            result[:, col] = full
        return result

    def _rank(self, arr):
        result = np.full_like(arr, np.nan)
        for t in range(arr.shape[0]):
            row = arr[t]
            valid = ~np.isnan(row)
            if valid.sum() < 2:
                continue
            result[t, valid] = pd.Series(row[valid]).rank(pct=True).values
        return result

    def _rolling_corr(self, a, b, window):
        result = np.full_like(a, np.nan)
        for col in range(a.shape[1]):
            a_col = pd.Series(a[:, col])
            b_col = pd.Series(b[:, col])
            result[:, col] = a_col.rolling(window).corr(b_col).values
        return result

    # ---- Insert results ----
    def _insert_values(self, factor_code: str, trade_date: date, stocks: list[str], raw_values: np.ndarray) -> int:
        valid_mask = ~np.isnan(raw_values)
        z_scores = np.full_like(raw_values, np.nan)
        if valid_mask.sum() > 1:
            z_scores[valid_mask] = (
                raw_values[valid_mask] - np.nanmean(raw_values[valid_mask])
            ) / np.nanstd(raw_values[valid_mask])

        percentiles = np.full_like(raw_values, np.nan)
        if valid_mask.sum() > 1:
            percentiles[valid_mask] = pd.Series(raw_values[valid_mask]).rank(pct=True).values

        insert_data = []
        for i, ts_code in enumerate(stocks):
            if not np.isnan(raw_values[i]):
                insert_data.append({
                    "factor_code": factor_code,
                    "ts_code": ts_code,
                    "trade_date": trade_date,
                    "raw_value": float(raw_values[i]),
                    "normalized_value": float(z_scores[i]) if not np.isnan(z_scores[i]) else None,
                    "percentile": float(percentiles[i]) if not np.isnan(percentiles[i]) else None,
                })

        if insert_data:
            self.db.execute(
                text(
                    """INSERT OR REPLACE INTO factor_values
                    (factor_code, ts_code, trade_date, raw_value, normalized_value, percentile)
                    VALUES (:factor_code, :ts_code, :trade_date, :raw_value, :normalized_value, :percentile)"""
                ),
                insert_data,
            )
            self.db.commit()

        return len(insert_data)
