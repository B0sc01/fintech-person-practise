"""Factor registry - centralized definitions of all factors in the system.

All factor definitions follow a standard structure:
- code: unique identifier (snake_case)
- name: English display name
- name_cn: Chinese display name
- category: momentum, value, quality, volatility, technical, size, sentiment
- sub_category: finer grouping
- description: what the factor measures and how to interpret it
- formula: mathematical expression
- polarity: "positive" (higher value predicts higher return), "negative" (lower value predicts higher return), or "neutral"
- data_requirements: list of fields needed from stock_daily
- parameters: dict of configurable params (window sizes, thresholds)
- source: "TA-Lib", "custom", "Alpha101", "academic_paper"
- paper_reference: academic citation if applicable
"""

FACTOR_REGISTRY: dict = {}


def register_factor(
    code, name, name_cn, category, sub_category="", description="",
    formula="", polarity="positive", data_requirements=None, parameters=None,
    source="custom", paper_reference="", python_function="",
):
    FACTOR_REGISTRY[code] = {
        "code": code, "name": name, "name_cn": name_cn,
        "category": category, "sub_category": sub_category,
        "description": description, "formula": formula,
        "polarity": polarity,
        "data_requirements": data_requirements or ["close"],
        "parameters": parameters or {},
        "source": source, "paper_reference": paper_reference,
        "python_function": python_function,
    }


# ============================================================================
# MOMENTUM FACTORS — Price momentum, volume momentum, industry momentum
# ============================================================================

register_factor(
    code="momentum_5d", name="5-Day Momentum", name_cn="5日动量",
    category="momentum", sub_category="price_momentum",
    description="5-day cumulative return. Short-term price trend. Higher = stronger recent upward trend.",
    formula="R_t = (P_t - P_{t-5}) / P_{t-5}",
    polarity="positive", parameters={"window": 5, "skip": 0},
    source="academic_paper", paper_reference="Jegadeesh and Titman (1993)",
)

register_factor(
    code="momentum_20d", name="20-Day Momentum", name_cn="20日动量",
    category="momentum", sub_category="price_momentum",
    description="20-day cumulative return skipping the most recent day (to avoid bid-ask bounce). Core momentum factor.",
    formula="R_t = (P_{t-1} - P_{t-21}) / P_{t-21}",
    polarity="positive", parameters={"window": 20, "skip": 1},
    source="academic_paper", paper_reference="Jegadeesh and Titman (1993)",
)

register_factor(
    code="momentum_60d", name="60-Day Momentum", name_cn="60日动量",
    category="momentum", sub_category="price_momentum",
    description="60-day cumulative return skipping the most recent day. Medium-term momentum.",
    formula="R_t = (P_{t-1} - P_{t-61}) / P_{t-61}",
    polarity="positive", parameters={"window": 60, "skip": 1},
    source="academic_paper", paper_reference="Carhart (1997)",
)

register_factor(
    code="momentum_120d", name="120-Day Momentum", name_cn="120日动量",
    category="momentum", sub_category="price_momentum",
    description="120-day cumulative return. Long-term momentum / trend following.",
    formula="R_t = (P_t - P_{t-120}) / P_{t-120}",
    polarity="positive", parameters={"window": 120},
    source="academic_paper",
)

register_factor(
    code="momentum_acceleration", name="Momentum Acceleration", name_cn="动量加速度",
    category="momentum", sub_category="price_momentum",
    description="Change in momentum: 20-day return minus 60-day return. Positive = momentum accelerating.",
    formula="Acc = Mom(20d) - Mom(60d)",
    polarity="positive", parameters={"window_short": 20, "window_long": 60},
    source="custom",
)

register_factor(
    code="return_reversal_5d", name="5-Day Reversal", name_cn="5日反转",
    category="momentum", sub_category="reversal",
    description="Short-term reversal: very recent 5-day return. Higher = more likely to reverse (negative premium).",
    formula="R_t = (P_t - P_{t-5}) / P_{t-5}",
    polarity="negative", parameters={"window": 5},
    source="academic_paper", paper_reference="Jegadeesh (1990)",
)

register_factor(
    code="volume_momentum_20d", name="Volume Momentum", name_cn="成交量动量",
    category="momentum", sub_category="volume_momentum",
    description="20-day change in average volume. Rising volume confirms price momentum.",
    formula="Vol_Mom = (AvgVol_5d - AvgVol_20d) / AvgVol_20d",
    polarity="positive", data_requirements=["close", "volume"], parameters={"window": 20},
    source="custom",
)

# ============================================================================
# VALUE FACTORS — Earnings-based, Asset-based, Cash-flow-based
# ============================================================================

register_factor(
    code="pe_ttm", name="P/E Ratio (TTM)", name_cn="市盈率TTM",
    category="value", sub_category="earnings_based",
    description="Price to TTM Earnings. Lower PE = cheaper valuation. Classic value factor.",
    formula="PE = Price / Earnings_per_share(TTM)",
    polarity="negative", data_requirements=["close", "pe_ttm"],
    source="academic_paper", paper_reference="Basu (1977)",
)

register_factor(
    code="pb_ratio", name="P/B Ratio", name_cn="市净率",
    category="value", sub_category="asset_based",
    description="Price to Book ratio. Lower PB = cheaper relative to book value. Fama-French value factor (HML).",
    formula="PB = Market_Cap / Book_Value",
    polarity="negative", data_requirements=["close", "pb"],
    source="academic_paper", paper_reference="Fama and French (1992)",
)

register_factor(
    code="earnings_yield", name="Earnings Yield", name_cn="盈利收益率",
    category="value", sub_category="earnings_based",
    description="Inverse of PE: E/P. Higher earnings yield = higher expected return.",
    formula="EY = 1 / PE",
    polarity="positive", data_requirements=["close", "pe_ttm"],
    source="custom",
)

register_factor(
    code="size_log_mv", name="Log Market Cap", name_cn="对数市值",
    category="value", sub_category="size",
    description="Natural log of total market capitalization. Smaller stocks tend to outperform (size premium).",
    formula="Size = ln(Total_Market_Value)",
    polarity="negative", data_requirements=["close", "total_mv"],
    source="academic_paper", paper_reference="Banz (1981)",
)

register_factor(
    code="dividend_yield", name="Dividend Yield", name_cn="股息率",
    category="value", sub_category="income",
    description="Trailing dividend yield. High dividend stocks tend to be value stocks.",
    formula="DY = DPS / Price",
    polarity="positive", data_requirements=["close"],
    source="custom",
)

# ============================================================================
# QUALITY FACTORS — Profitability, Earnings quality, Safety
# ============================================================================

register_factor(
    code="roe", name="ROE", name_cn="净资产收益率",
    category="quality", sub_category="profitability",
    description="Return on Equity: Net Income / Equity. Higher ROE = more profitable use of shareholder capital.",
    formula="ROE = Net_Income / Shareholder_Equity",
    polarity="positive", data_requirements=["close"],
    source="academic_paper", paper_reference="Piotroski (2000)",
)

register_factor(
    code="roa", name="ROA", name_cn="总资产收益率",
    category="quality", sub_category="profitability",
    description="Return on Assets. Higher ROA = more efficient use of total assets.",
    formula="ROA = Net_Income / Total_Assets",
    polarity="positive", data_requirements=["close"],
    source="academic_paper",
)

register_factor(
    code="gross_margin", name="Gross Margin", name_cn="毛利率",
    category="quality", sub_category="profitability",
    description="Gross profit / Revenue. Higher gross margin = stronger pricing power and competitive moat.",
    formula="GM = (Revenue - COGS) / Revenue",
    polarity="positive", data_requirements=["close"],
    source="academic_paper", paper_reference="Novy-Marx (2013)",
)

register_factor(
    code="debt_to_equity", name="Debt-to-Equity", name_cn="资产负债率",
    category="quality", sub_category="safety",
    description="Total Liabilities / Total Equity. Lower = less leveraged = safer. High leverage increases risk.",
    formula="DE = Total_Liabilities / Total_Equity",
    polarity="negative", data_requirements=["close"],
    source="custom",
)

register_factor(
    code="asset_turnover", name="Asset Turnover", name_cn="资产周转率",
    category="quality", sub_category="efficiency",
    description="Revenue / Total Assets. Measures how efficiently a company uses its assets to generate sales.",
    formula="AT = Revenue / Avg_Total_Assets",
    polarity="positive", data_requirements=["close"],
    source="academic_paper", paper_reference="Piotroski (2000)",
)

# ============================================================================
# VOLATILITY FACTORS — Historical vol, downside vol, beta
# ============================================================================

register_factor(
    code="volatility_20d", name="20-Day Volatility", name_cn="20日波动率",
    category="volatility", sub_category="historical_vol",
    description="Annualized 20-day standard deviation of daily returns. Higher vol = riskier stock. Low vol anomaly: low vol stocks often outperform.",
    formula="sigma = std(daily_returns_20d) * sqrt(252)",
    polarity="negative", data_requirements=["close"], parameters={"window": 20},
    source="academic_paper", paper_reference="Ang, Hodrick, Xing, Zhang (2006)",
)

register_factor(
    code="volatility_60d", name="60-Day Volatility", name_cn="60日波动率",
    category="volatility", sub_category="historical_vol",
    description="Annualized 60-day return volatility. Medium-term risk measure.",
    formula="sigma = std(daily_returns_60d) * sqrt(252)",
    polarity="negative", data_requirements=["close"], parameters={"window": 60},
    source="custom",
)

register_factor(
    code="downside_volatility_20d", name="Downside Volatility", name_cn="下行波动率",
    category="volatility", sub_category="tail_risk",
    description="Volatility computed only from negative daily returns (downside deviation). Better risk measure than total vol.",
    formula="Downside_sigma = sqrt(mean(min(ret, 0)^2)) * sqrt(252)",
    polarity="negative", data_requirements=["close"], parameters={"window": 20},
    source="academic_paper", paper_reference="Sortino and Price (1994)",
)

register_factor(
    code="max_drawdown_60d", name="60-Day Max Drawdown", name_cn="60日最大回撤",
    category="volatility", sub_category="tail_risk",
    description="Maximum peak-to-trough decline over the past 60 days. Captures worst-case downside.",
    formula="MDD = max((Peak_t - Trough_t) / Peak_t) over 60d window",
    polarity="negative", data_requirements=["close"], parameters={"window": 60},
    source="custom",
)

register_factor(
    code="beta_60d", name="60-Day Beta", name_cn="60日Beta",
    category="volatility", sub_category="market_risk",
    description="Market sensitivity: covariance(stock_return, market_return) / var(market_return). Beta > 1 = more volatile than market.",
    formula="Beta = Cov(R_stock, R_market) / Var(R_market)",
    polarity="neutral", data_requirements=["close"], parameters={"window": 60},
    source="academic_paper", paper_reference="Sharpe (1964) CAPM",
)

register_factor(
    code="skewness_20d", name="20-Day Return Skewness", name_cn="20日收益偏度",
    category="volatility", sub_category="return_distribution",
    description="Skewness of daily returns over 20 days. Positive skew = lottery-like return profile (negative premium expected).",
    formula="Skew = E[(R - mu)^3] / sigma^3",
    polarity="negative", data_requirements=["close"], parameters={"window": 20},
    source="academic_paper", paper_reference="Barberis and Huang (2008)",
)

register_factor(
    code="kurtosis_20d", name="20-Day Return Kurtosis", name_cn="20日收益峰度",
    category="volatility", sub_category="return_distribution",
    description="Kurtosis of daily returns. High kurtosis = fat tails = higher crash risk.",
    formula="Kurt = E[(R - mu)^4] / sigma^4",
    polarity="negative", data_requirements=["close"], parameters={"window": 20},
    source="custom",
)

# ============================================================================
# TECHNICAL FACTORS — Trend, Mean-reversion, Pattern, Volume (via TA-Lib)
# ============================================================================

register_factor(
    code="rsi_14", name="RSI (14)", name_cn="相对强弱指标14",
    category="technical", sub_category="oscillator",
    description="Relative Strength Index: measures speed and change of price movements. >70 = overbought (potential reversal down). <30 = oversold (potential reversal up).",
    formula="RSI = 100 - 100/(1 + RS), RS = avg_gain_14 / avg_loss_14",
    polarity="negative", data_requirements=["close"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="macd_dif", name="MACD DIF", name_cn="MACD离差值",
    category="technical", sub_category="trend",
    description="MACD DIF line: 12-day EMA minus 26-day EMA. Positive = bullish trend. Cross above signal line = buy, cross below = sell.",
    formula="DIF = EMA(12) - EMA(26)",
    polarity="positive", data_requirements=["close"], parameters={"fast": 12, "slow": 26},
    source="TA-Lib",
)

register_factor(
    code="macd_signal", name="MACD Signal", name_cn="MACD信号线",
    category="technical", sub_category="trend",
    description="MACD Signal line: 9-day EMA of DIF. Used for trading signals.",
    formula="Signal = EMA(DIF, 9)",
    polarity="positive", data_requirements=["close"], parameters={"signal": 9},
    source="TA-Lib",
)

register_factor(
    code="macd_histogram", name="MACD Histogram", name_cn="MACD柱",
    category="technical", sub_category="trend",
    description="MACD Histogram = DIF - Signal. Divergence between DIF and signal line. Widening histogram = strengthening trend.",
    formula="Histogram = DIF - Signal",
    polarity="positive", data_requirements=["close"],
    source="TA-Lib",
)

register_factor(
    code="bb_width", name="Bollinger Band Width", name_cn="布林带宽度",
    category="technical", sub_category="volatility_technical",
    description="Bollinger Band width = (Upper - Lower) / Middle. Wide bands = high volatility. Narrow bands = potential breakout ahead.",
    formula="BB_Width = (BB_Upper - BB_Lower) / SMA(20)",
    polarity="positive", data_requirements=["close"], parameters={"timeperiod": 20, "nbdev": 2},
    source="TA-Lib",
)

register_factor(
    code="bb_pct_b", name="Bollinger %B", name_cn="布林带%B",
    category="technical", sub_category="mean_reversion",
    description="%B = (Close - Lower) / (Upper - Lower). >1 = above upper band (overbought). <0 = below lower band (oversold). Reversion play.",
    formula="%B = (Close - BB_Lower) / (BB_Upper - BB_Lower)",
    polarity="negative", data_requirements=["close"], parameters={"timeperiod": 20},
    source="TA-Lib",
)

register_factor(
    code="sma_5", name="SMA (5)", name_cn="5日均线",
    category="technical", sub_category="moving_average",
    description="5-day Simple Moving Average. Very short-term trend indicator.",
    formula="SMA_5 = avg(Close, 5)",
    polarity="positive", data_requirements=["close"], parameters={"window": 5},
    source="TA-Lib",
)

register_factor(
    code="sma_20", name="SMA (20)", name_cn="20日均线",
    category="technical", sub_category="moving_average",
    description="20-day SMA. Short-term trend. Close above SMA = bullish, below = bearish.",
    formula="SMA_20 = avg(Close, 20)",
    polarity="positive", data_requirements=["close"], parameters={"window": 20},
    source="TA-Lib",
)

register_factor(
    code="sma_60", name="SMA (60)", name_cn="60日均线",
    category="technical", sub_category="moving_average",
    description="60-day SMA. Medium-term trend indicator. Widely used in Chinese A-share markets.",
    formula="SMA_60 = avg(Close, 60)",
    polarity="positive", data_requirements=["close"], parameters={"window": 60},
    source="TA-Lib",
)

register_factor(
    code="sma_ratio_5_20", name="SMA 5/20 Ratio", name_cn="均线比值5/20",
    category="technical", sub_category="moving_average_cross",
    description="Ratio of 5-day SMA to 20-day SMA. >1 = short-term trend above medium-term = bullish.",
    formula="Ratio = SMA_5 / SMA_20",
    polarity="positive", data_requirements=["close"],
    source="custom",
)

register_factor(
    code="sma_ratio_20_60", name="SMA 20/60 Ratio", name_cn="均线比值20/60",
    category="technical", sub_category="moving_average_cross",
    description="Ratio of 20-day SMA to 60-day SMA. Golden cross / dead cross proxy.",
    formula="Ratio = SMA_20 / SMA_60",
    polarity="positive", data_requirements=["close"],
    source="custom",
)

register_factor(
    code="atr_14", name="ATR (14)", name_cn="平均真实波幅14",
    category="technical", sub_category="volatility_technical",
    description="Average True Range: measures market volatility. High ATR = high volatility, wide stops needed. Low ATR = quiet market.",
    formula="ATR = EMA(True_Range, 14)",
    polarity="neutral", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="obv_ratio", name="OBV Ratio", name_cn="能量潮比值",
    category="technical", sub_category="volume",
    description="On-Balance Volume: cumulative volume with sign based on price direction. OBV/20d avg OBV = relative volume pressure.",
    formula="OBV_t = OBV_{t-1} + sign(Close_t - Close_{t-1}) * Volume_t",
    polarity="positive", data_requirements=["close", "volume"],
    source="TA-Lib",
)

register_factor(
    code="williams_r_14", name="Williams %R (14)", name_cn="威廉指标14",
    category="technical", sub_category="oscillator",
    description="Williams %R: similar to Stochastic. -80 to -100 = oversold (buy signal). 0 to -20 = overbought (sell signal).",
    formula="%R = (HighestHigh_14 - Close) / (HighestHigh_14 - LowestLow_14) * -100",
    polarity="negative", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="stoch_k_14", name="Stochastic %K (14)", name_cn="随机指标K14",
    category="technical", sub_category="oscillator",
    description="Stochastic oscillator %K line. >80 = overbought. <20 = oversold.",
    formula="%K = (Close - Low_14) / (High_14 - Low_14) * 100",
    polarity="negative", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="stoch_d_3", name="Stochastic %D (3)", name_cn="随机指标D3",
    category="technical", sub_category="oscillator",
    description="Stochastic %D: 3-day SMA of %K. Slower, smoother signal. Cross above/below %K generates signals.",
    formula="%D = SMA(%K, 3)",
    polarity="negative", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14, "slow_period": 3},
    source="TA-Lib",
)

register_factor(
    code="cci_14", name="CCI (14)", name_cn="商品通道指数14",
    category="technical", sub_category="oscillator",
    description="Commodity Channel Index. >100 = strong uptrend, <-100 = strong downtrend. Measures deviation from statistical mean.",
    formula="CCI = (Typical_Price - SMA_TP_14) / (0.015 * Mean_Deviation_14)",
    polarity="positive", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="adx_14", name="ADX (14)", name_cn="平均趋向指数14",
    category="technical", sub_category="trend_strength",
    description="Average Directional Index: measures trend strength (not direction). ADX > 25 = strong trend. ADX < 20 = weak/range-bound.",
    formula="ADX = EMA(DX, 14), where DX = |DI+ - DI-| / (DI+ + DI-)",
    polarity="positive", data_requirements=["close", "high", "low"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="mfi_14", name="MFI (14)", name_cn="资金流量指标14",
    category="technical", sub_category="volume_oscillator",
    description="Money Flow Index: volume-weighted RSI. >80 = overbought, <20 = oversold. Confirms price with volume.",
    formula="MFI = 100 - 100/(1 + Money_Ratio), Money_Ratio = Positive_MF_14 / Negative_MF_14",
    polarity="negative", data_requirements=["close", "high", "low", "volume"], parameters={"timeperiod": 14},
    source="TA-Lib",
)

register_factor(
    code="roc_10", name="ROC (10)", name_cn="变动率10",
    category="technical", sub_category="momentum_technical",
    description="Rate of Change: 10-day percentage price change. Similar to momentum but expressed as percentage.",
    formula="ROC = (Close_t - Close_{t-10}) / Close_{t-10} * 100",
    polarity="positive", data_requirements=["close"], parameters={"timeperiod": 10},
    source="TA-Lib",
)

register_factor(
    code="ema_12", name="EMA (12)", name_cn="12日指数均线",
    category="technical", sub_category="moving_average",
    description="12-day Exponential Moving Average. Weights recent prices more heavily than SMA. Faster to react.",
    formula="EMA_12 = alpha * Close + (1-alpha) * EMA_{prev}, alpha = 2/(12+1)",
    polarity="positive", data_requirements=["close"], parameters={"timeperiod": 12},
    source="TA-Lib",
)

register_factor(
    code="ema_26", name="EMA (26)", name_cn="26日指数均线",
    category="technical", sub_category="moving_average",
    description="26-day EMA. Often used as the slow line in MACD calculations.",
    formula="EMA_26 = alpha * Close + (1-alpha) * EMA_{prev}, alpha = 2/(26+1)",
    polarity="positive", data_requirements=["close"], parameters={"timeperiod": 26},
    source="TA-Lib",
)

register_factor(
    code="trix_15", name="TRIX (15)", name_cn="三重指数均线15",
    category="technical", sub_category="trend",
    description="Triple-smoothed EMA rate of change. Removes short-term noise. Oscillator crossing zero = trend change.",
    formula="TRIX = ROC(EMA(EMA(EMA(Close, 15), 15), 15), 1)",
    polarity="positive", data_requirements=["close"], parameters={"timeperiod": 15},
    source="TA-Lib",
)

# ============================================================================
# SIZE & LIQUIDITY FACTORS
# ============================================================================

register_factor(
    code="turnover_rate_avg_20d", name="Avg Turnover Rate (20d)", name_cn="20日平均换手率",
    category="size", sub_category="liquidity",
    description="Average daily turnover rate over 20 days. Higher turnover = more liquid, more actively traded.",
    formula="Avg_TO = mean(Turnover_Rate, 20)",
    polarity="negative", data_requirements=["close", "turnover_rate"], parameters={"window": 20},
    source="custom",
)

register_factor(
    code="turnover_variability_20d", name="Turnover Variability", name_cn="换手率波动",
    category="size", sub_category="liquidity",
    description="Standard deviation of turnover rate over 20 days. High variability = unstable liquidity = risk.",
    formula="TO_Vol = std(Turnover_Rate, 20)",
    polarity="negative", data_requirements=["close", "turnover_rate"], parameters={"window": 20},
    source="custom",
)

register_factor(
    code="amihud_illiq_20d", name="Amihud Illiquidity", name_cn="Amihud非流动性",
    category="size", sub_category="liquidity",
    description="Amihud illiquidity: avg(|return| / dollar_volume). Higher value = less liquid = higher expected return (liquidity premium).",
    formula="ILLIQ = mean(|ret_d| / volume_d * close_d) over 20 days",
    polarity="positive", data_requirements=["close", "volume"], parameters={"window": 20},
    source="academic_paper", paper_reference="Amihud (2002)",
)

register_factor(
    code="circ_mv_ratio", name="Circulating MV Ratio", name_cn="流通市值占比",
    category="size", sub_category="market_cap",
    description="Ratio of circulating market cap to total market cap. Lower ratio = more locked shares = higher float-related risk.",
    formula="Circ_Ratio = Circ_MV / Total_MV",
    polarity="positive", data_requirements=["close", "circ_mv", "total_mv"],
    source="custom",
)

# ============================================================================
# SENTIMENT / BEHAVIORAL FACTORS
# ============================================================================

register_factor(
    code="turnover_anomaly_20d", name="Turnover Anomaly", name_cn="换手率异常",
    category="sentiment", sub_category="attention",
    description="Abnormal turnover: current turnover / avg 60d turnover. High abnormal turnover = heightened investor attention, often precedes reversal.",
    formula="Ab_TO = Turnover_t / mean(Turnover, 60d)",
    polarity="negative", data_requirements=["close", "turnover_rate"], parameters={"window": 20},
    source="academic_paper", paper_reference="Barber and Odean (2008)",
)

register_factor(
    code="price_gap_5d", name="Price Gap (5d)", name_cn="价格缺口5日",
    category="sentiment", sub_category="price_pattern",
    description="Today's open vs. 5-day ago close, normalized. Large gap up may indicate overnight sentiment shock.",
    formula="Gap = (Open_t - Close_{t-5}) / Close_{t-5}",
    polarity="negative", data_requirements=["open", "close"],
    source="custom",
)

register_factor(
    code="close_to_high_20d", name="Close-to-High Ratio", name_cn="收盘价/20日最高价",
    category="sentiment", sub_category="price_position",
    description="Current close relative to 20-day high. Near 1 = at/ near highs (strong momentum). Near 0 = near lows (weak).",
    formula="Close_adj = (Close - Low_20d) / (High_20d - Low_20d)",
    polarity="positive", data_requirements=["close", "high", "low"], parameters={"window": 20},
    source="custom",
)

register_factor(
    code="intraday_volatility_5d", name="Intraday Volatility (5d)", name_cn="日内波动率5日",
    category="sentiment", sub_category="microstructure",
    description="Average daily (High-Low)/Close over 5 days. Higher intraday range = more uncertainty/disagreement.",
    formula="IVol = mean((High - Low) / Close, 5)",
    polarity="negative", data_requirements=["close", "high", "low"], parameters={"window": 5},
    source="custom",
)

# ============================================================================
# WORLDQUANT ALPHA101 SUBSET — Selected price/volume-only factors
# ============================================================================

register_factor(
    code="alpha001", name="WorldQuant Alpha 001", name_cn="Alpha001",
    category="momentum", sub_category="alpha101",
    description="Alpha001: Rank of signed power of returns, rolling argmax. Identifies stocks with strongest recent positive price jumps.",
    formula="rank(Ts_ArgMax(SignedPower(returns, 2), 5)) - 0.5",
    polarity="positive", data_requirements=["close"],
    source="Alpha101",
)

register_factor(
    code="alpha003", name="WorldQuant Alpha 003", name_cn="Alpha003",
    category="momentum", sub_category="alpha101",
    description="Alpha003: Negative correlation of open and volume rank. Identifies opening-price/volume divergence patterns.",
    formula="-1 * correlation(rank(open), rank(volume), 10)",
    polarity="positive", data_requirements=["open", "volume"],
    source="Alpha101",
)

register_factor(
    code="alpha005", name="WorldQuant Alpha 005", name_cn="Alpha005",
    category="volatility", sub_category="alpha101",
    description="Alpha005: Ts_Rank of volume to advance-decline ratio. Volume-weighted market breadth indicator.",
    formula="rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap))))",
    polarity="positive", data_requirements=["close", "open"],
    source="Alpha101",
)

register_factor(
    code="alpha007", name="WorldQuant Alpha 007", name_cn="Alpha007",
    category="momentum", sub_category="alpha101",
    description="Alpha007: Advancing volume vs. returning price action over a short window.",
    formula="((rank(ts_max(vwap - close, 3)) + rank(ts_min(vwap - close, 3))) * rank(delta(volume, 3))) / 3",
    polarity="positive", data_requirements=["close", "volume"],
    source="Alpha101",
)

register_factor(
    code="alpha009", name="WorldQuant Alpha 009", name_cn="Alpha009",
    category="momentum", sub_category="alpha101",
    description="Alpha009: Short-term price oscillation combined with volume delta.",
    formula="((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))",
    polarity="positive", data_requirements=["close"],
    source="Alpha101",
)

register_factor(
    code="alpha010", name="WorldQuant Alpha 010", name_cn="Alpha010",
    category="momentum", sub_category="alpha101",
    description="Alpha010: Rank of return conditioned on overnight vs. intraday return components.",
    formula="rank((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(close, 1) : (-1 * delta(close, 1))))",
    polarity="positive", data_requirements=["close"],
    source="Alpha101",
)

register_factor(
    code="alpha012", name="WorldQuant Alpha 012", name_cn="Alpha012",
    category="volatility", sub_category="alpha101",
    description="Alpha012: Sign of volume delta multiplied by price change — captures volume-confirmed moves.",
    formula="sign(delta(volume, 1)) * (-1 * delta(close, 1))",
    polarity="positive", data_requirements=["close", "volume"],
    source="Alpha101",
)

register_factor(
    code="alpha020", name="WorldQuant Alpha 020", name_cn="Alpha020",
    category="technical", sub_category="alpha101",
    description="Alpha020: Open-price short-term ranking with delay. Measures opening-price patterns.",
    formula="(rank(open - delay(high, 1))) * (rank(open - delay(close, 1))) * (rank(open - delay(low, 1)))",
    polarity="negative", data_requirements=["close", "open", "high", "low"],
    source="Alpha101",
)

register_factor(
    code="alpha023", name="WorldQuant Alpha 023", name_cn="Alpha023",
    category="momentum", sub_category="alpha101",
    description="Alpha023: High minus close scaled by return. Captures intraday mean-reversion signal.",
    formula="((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0",
    polarity="positive", data_requirements=["close", "high"],
    source="Alpha101",
)

register_factor(
    code="alpha032", name="WorldQuant Alpha 032", name_cn="Alpha032",
    category="momentum", sub_category="alpha101",
    description="Alpha032: Price-volume correlation and rank product. Volume-price confirmation signal.",
    formula="(scale(((sum(close, 7) / 7) - close)) + 20 * scale(correlation(vwap, delay(close, 5), 230)))",
    polarity="positive", data_requirements=["close"],
    source="Alpha101",
)

register_factor(
    code="alpha041", name="WorldQuant Alpha 041", name_cn="Alpha041",
    category="momentum", sub_category="alpha101",
    description="Alpha041: Rank of vwap / high product. Relative value positioning indicator.",
    formula="rank(((high * low) ** 0.5) - vwap)",
    polarity="positive", data_requirements=["close", "high", "low"],
    source="Alpha101",
)

register_factor(
    code="alpha053", name="WorldQuant Alpha 053", name_cn="Alpha053",
    category="momentum", sub_category="alpha101",
    description="Alpha053: Count of close > delay(close) combined with rank. Trend persistence indicator.",
    formula="(-1 * delta(min(low, 5), 6)) / correlation(low, volume, 6)",
    polarity="positive", data_requirements=["close", "low", "volume"],
    source="Alpha101",
)

register_factor(
    code="alpha101", name="WorldQuant Alpha 101", name_cn="Alpha101",
    category="momentum", sub_category="alpha101",
    description="Alpha101: Close minus open scaled by high-low range, wrapped in rank. Gap/range ratio signal.",
    formula="(close - open) / ((high - low) + 0.001)",
    polarity="positive", data_requirements=["close", "open", "high", "low"],
    source="Alpha101",
)

# ============================================================================
# COMBINED / SYNTHETIC FACTORS
# ============================================================================

register_factor(
    code="momentum_quality_combo", name="Momentum-Quality Combo", name_cn="动量质量组合",
    category="quality", sub_category="composite",
    description="Simple average of 20d momentum and gross margin proxy. Combines trend with fundamental quality.",
    formula="Combo = 0.5 * z(Mom20d) + 0.5 * z(Revenue/Assets)",
    polarity="positive", data_requirements=["close"],
    source="custom",
)

register_factor(
    code="value_volatility_combo", name="Value-Volatility Combo", name_cn="价值波动组合",
    category="value", sub_category="composite",
    description="Combined value (low PE) and low volatility signal. Quality value stocks that are not too volatile.",
    formula="Combo = 0.5 * z(1/PE) + 0.5 * z(-Vol20d)",
    polarity="positive", data_requirements=["close"],
    source="custom",
)


def get_factor_registry() -> dict:
    return FACTOR_REGISTRY


def seed_factor_catalog_entries() -> list[dict]:
    """Return all factor definitions as a list of dicts suitable for DB insertion."""
    return list(FACTOR_REGISTRY.values())
