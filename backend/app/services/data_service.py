import time
from datetime import date, datetime
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.models.stock import StockBasic, StockDaily


def _to_baostock_code(ts_code: str) -> str:
    """Convert ts_code (e.g. 600000) to baostock format (sh.600000)."""
    if ts_code.startswith("6") or ts_code.startswith("9"):
        return f"sh.{ts_code}"
    return f"sz.{ts_code}"


def _from_baostock_code(bs_code: str) -> str:
    """Convert baostock format (sh.600000) to ts_code (600000)."""
    return bs_code.split(".", 1)[1] if "." in bs_code else bs_code


# A-share stock code prefixes (Shanghai / Shenzhen)
_A_SHARE_SH = ("60", "68")
_A_SHARE_SZ = ("00", "30", "002", "003", "004")


def _is_a_share(ts_code: str) -> bool:
    """Check if a ts_code is an A-share stock (not index, B-share, etc.)."""
    if ts_code.startswith(_A_SHARE_SH):
        return True
    if ts_code.startswith(_A_SHARE_SZ):
        return True
    # Shenzhen ChiNext / SME board prefixes after removing sh/sz
    return False


class DataService:
    def __init__(self, db: Session):
        self.db = db

    def get_status(self) -> dict:
        stock_count = self.db.query(func.count(StockBasic.id)).scalar()
        daily_count = self.db.query(func.count(StockDaily.id)).scalar()
        min_date = self.db.query(func.min(StockDaily.trade_date)).scalar()
        max_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        industry_count = (
            self.db.query(func.count(func.distinct(StockBasic.industry)))
            .filter(StockBasic.industry.isnot(None))
            .scalar()
        )
        return {
            "stock_count": stock_count,
            "daily_count": daily_count,
            "min_date": min_date,
            "max_date": max_date,
            "industry_count": industry_count,
        }

    def download_stock_list(self) -> int:
        """Download A-share stock list via baostock and upsert into stock_basic."""
        import baostock as bs

        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"baostock login failed: {lg.error_msg}")

        try:
            rs = bs.query_stock_basic(code_name="")
            if rs.error_code != "0":
                raise RuntimeError(f"baostock query failed: {rs.error_msg}")

            stocks = []
            while rs.next():
                row = rs.get_row_data()
                bs_code = row[0]        # sh.600000
                name = row[1]           # 浦发银行
                stock_type = row[4]     # "1" = stock, "2" = index
                if stock_type != "1":
                    continue
                ts_code = _from_baostock_code(bs_code)
                if not _is_a_share(ts_code):
                    continue
                stocks.append((ts_code, name))

            count = 0
            for ts_code, name in stocks:
                existing = (
                    self.db.query(StockBasic)
                    .filter(StockBasic.ts_code == ts_code)
                    .first()
                )
                if existing:
                    existing.name = name
                else:
                    self.db.add(StockBasic(ts_code=ts_code, name=name))
                count += 1

            self.db.commit()
            return count
        finally:
            bs.logout()

    def download_daily_batch(
        self,
        start_date: date,
        end_date: date,
        stock_codes: Optional[list[str]] = None,
        progress_callback=None,
    ) -> dict:
        """Download daily data for a set of stocks via baostock."""
        import baostock as bs

        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"baostock login failed: {lg.error_msg}")

        try:
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            if stock_codes is None:
                stocks = self.db.query(StockBasic.ts_code).all()
                stock_codes = [s[0] for s in stocks]

            total = len(stock_codes)
            success = 0
            failed = 0

            for i, code in enumerate(stock_codes):
                try:
                    bs_code = _to_baostock_code(code)
                    rs = bs.query_history_k_data_plus(
                        bs_code,
                        "date,open,high,low,close,preclose,volume,amount,turn",
                        start_date=start_str,
                        end_date=end_str,
                        frequency="d",
                        adjustflag="2",  # 前复权
                    )
                    if rs.error_code != "0":
                        failed += 1
                        continue

                    rows = []
                    while rs.next():
                        rows.append(rs.get_row_data())

                    if not rows:
                        failed += 1
                        continue

                    for row in rows:
                        trade_date_val = datetime.strptime(row[0], "%Y-%m-%d").date()
                        existing = (
                            self.db.query(StockDaily)
                            .filter(
                                StockDaily.ts_code == code,
                                StockDaily.trade_date == trade_date_val,
                            )
                            .first()
                        )
                        if existing is None:
                            self.db.add(
                                StockDaily(
                                    ts_code=code,
                                    trade_date=trade_date_val,
                                    open=float(row[1]) if row[1] else None,
                                    high=float(row[2]) if row[2] else None,
                                    low=float(row[3]) if row[3] else None,
                                    close=float(row[4]) if row[4] else None,
                                    pre_close=float(row[5]) if row[5] else None,
                                    volume=float(row[6]) if row[6] else None,
                                    amount=float(row[7]) if row[7] else None,
                                    turnover_rate=float(row[8]) if row[8] else None,
                                )
                            )
                    self.db.commit()
                    success += 1
                except Exception:
                    failed += 1

                if progress_callback and i % 10 == 0:
                    progress_callback(i, total)

                # baostock needs a small pause between queries
                if i % 3 == 0:
                    time.sleep(0.05)

            if progress_callback:
                progress_callback(total, total)

            return {"success": success, "failed": failed, "total": total}
        finally:
            bs.logout()

    def get_stocks(
        self, industry: Optional[str] = None, page: int = 1, page_size: int = 50
    ) -> tuple[list[StockBasic], int]:
        q = self.db.query(StockBasic)
        if industry:
            q = q.filter(StockBasic.industry == industry)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_daily_data(
        self,
        ts_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[StockDaily]:
        q = self.db.query(StockDaily).filter(StockDaily.ts_code == ts_code)
        if start_date:
            q = q.filter(StockDaily.trade_date >= start_date)
        if end_date:
            q = q.filter(StockDaily.trade_date <= end_date)
        return q.order_by(StockDaily.trade_date).all()

    def get_industries(self) -> list[str]:
        result = (
            self.db.query(StockBasic.industry)
            .filter(StockBasic.industry.isnot(None), StockBasic.industry != "")
            .distinct()
            .order_by(StockBasic.industry)
            .all()
        )
        return [r[0] for r in result]

    def load_daily_panel(
        self, start_date: date, end_date: date, fields: Optional[list[str]] = None
    ) -> pd.DataFrame:
        """Load daily data as a pivot panel DataFrame for factor computation."""
        if fields is None:
            fields = ["close", "open", "high", "low", "volume", "amount"]

        columns = ["ts_code", "trade_date"] + fields
        query_fields = [getattr(StockDaily, f) for f in fields]
        rows = (
            self.db.query(StockDaily.ts_code, StockDaily.trade_date, *query_fields)
            .filter(
                StockDaily.trade_date >= start_date,
                StockDaily.trade_date <= end_date,
            )
            .all()
        )
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=columns)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        return df

    def get_date_range(self) -> dict:
        min_date = self.db.query(func.min(StockDaily.trade_date)).scalar()
        max_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        return {"min_date": min_date, "max_date": max_date}
