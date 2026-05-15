from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.factor import FactorValues
from app.models.stock import StockBasic
from app.schemas.backtest import ScreenerRequest


class ScreenerService:
    def __init__(self, db: Session):
        self.db = db

    def screen(self, req: ScreenerRequest) -> dict:
        """Screen stocks based on multiple factor conditions."""
        if not req.conditions:
            return {"items": [], "total": 0}

        # Get the latest date with factor data
        from sqlalchemy import func

        latest_date = (
            self.db.query(func.max(FactorValues.trade_date))
            .filter(FactorValues.factor_code == req.conditions[0].factor_code)
            .scalar()
        )
        if not latest_date:
            return {"items": [], "total": 0}

        # For each condition, get stocks that match
        stock_sets = []
        for cond in req.conditions:
            q = self.db.query(FactorValues.ts_code).filter(
                FactorValues.factor_code == cond.factor_code,
                FactorValues.trade_date == latest_date,
                FactorValues.normalized_value.isnot(None),
            )
            if cond.operator == "gt":
                q = q.filter(FactorValues.normalized_value > cond.value)
            elif cond.operator == "lt":
                q = q.filter(FactorValues.normalized_value < cond.value)
            elif cond.operator == "gte":
                q = q.filter(FactorValues.normalized_value >= cond.value)
            elif cond.operator == "lte":
                q = q.filter(FactorValues.normalized_value <= cond.value)

            codes = {r[0] for r in q.all()}
            stock_sets.append(codes)

        if not stock_sets:
            return {"items": [], "total": 0}

        if req.logic == "AND":
            result_codes = stock_sets[0]
            for s in stock_sets[1:]:
                result_codes = result_codes & s
        else:
            result_codes = set()
            for s in stock_sets:
                result_codes = result_codes | s

        # Get stock names
        stocks = (
            self.db.query(StockBasic)
            .filter(StockBasic.ts_code.in_(result_codes))
            .all()
        )
        name_map = {s.ts_code: s.name for s in stocks}

        # Get factor values for all matching stocks + requested factor codes
        factor_codes = [c.factor_code for c in req.conditions]
        fvs = (
            self.db.query(FactorValues)
            .filter(
                FactorValues.ts_code.in_(result_codes),
                FactorValues.factor_code.in_(factor_codes),
                FactorValues.trade_date == latest_date,
                FactorValues.normalized_value.isnot(None),
            )
            .all()
        )
        factor_map: dict[str, dict[str, float]] = {}
        for fv in fvs:
            factor_map.setdefault(fv.ts_code, {})[fv.factor_code] = fv.normalized_value

        items = []
        for code in result_codes:
            items.append({
                "ts_code": code,
                "stock_name": name_map.get(code, ""),
                "matching_factors": factor_map.get(code, {}),
            })

        total = len(items)

        # Paginate
        start = (req.page - 1) * req.page_size
        end = start + req.page_size
        items = items[start:end]

        return {"items": items, "total": total, "page": req.page, "page_size": req.page_size}
