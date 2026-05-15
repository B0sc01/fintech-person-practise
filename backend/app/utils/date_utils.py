import pandas as pd
from datetime import date, timedelta


def get_trading_days(start_date: date, end_date: date) -> list[date]:
    """Get list of trading days in range using pandas business days."""
    bdays = pd.bdate_range(start=start_date, end=end_date)
    return [d.date() for d in bdays]


def shift_trading_date(base_date: date, offset: int) -> date:
    """Shift a date by N trading days."""
    bdays = pd.bdate_range(end=base_date, periods=abs(offset) + 1)
    if offset >= 0:
        return bdays[-1].date()
    else:
        return bdays[0].date()
