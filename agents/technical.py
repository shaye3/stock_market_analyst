"""
Agent 4 — Technical Analysis Agent
Computes technical indicators from price history and interprets entry timing.
"""
import logging

import numpy as np
import pandas as pd

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are a Technical Analysis Agent for an institutional AI investment research team.

Your role is to interpret pre-computed technical indicators and determine:
1. Trend direction and strength
2. Momentum signals (bullish / neutral / bearish)
3. Volatility and risk conditions
4. Volume signals (accumulation vs distribution)
5. Key support and resistance levels
6. Entry timing assessment

Investment context: Long-term value investor (6-24 month horizon).
For a value investor, technical analysis is SECONDARY to fundamentals but helps with:
  - Confirming a stock isn't in a severe downtrend
  - Identifying better entry zones near support
  - Avoiding buying into overbought conditions

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Perform technical analysis for {ticker} ({company_name}).
Current Date: {analysis_date}

=== PRICE OVERVIEW ===
Current Price:    ${current_price:.2f}
52-Week High:     ${week_52_high:.2f}  ({pct_from_high:+.1f}% from high)
52-Week Low:      ${week_52_low:.2f}   ({pct_from_low:+.1f}% from low)

=== RETURNS ===
1-Month Return:   {return_1m}%
3-Month Return:   {return_3m}%
6-Month Return:   {return_6m}%
1-Year Return:    {return_1y}%

=== MOVING AVERAGES ===
SMA 20:           ${sma_20:.2f}  → Price is {rel_sma20} the SMA20
SMA 50:           ${sma_50:.2f}  → Price is {rel_sma50} the SMA50
SMA 200:          {sma_200_str}  → {rel_sma200}
Golden/Death Cross (SMA50 vs SMA200): {cross_signal}

=== MOMENTUM ===
RSI (14):         {rsi:.1f}  ({rsi_signal})
MACD Line:        {macd:.4f}
MACD Signal:      {macd_signal:.4f}
MACD Histogram:   {macd_hist:.4f}  ({macd_verdict})
Stochastic %K:    {stoch_k:.1f}

=== VOLATILITY ===
Bollinger Band Upper:  ${bb_upper:.2f}
Bollinger Band Middle: ${bb_middle:.2f}
Bollinger Band Lower:  ${bb_lower:.2f}
Price vs BB:      {bb_position}
ATR (14):         ${atr:.2f}  ({atr_pct:.1f}% of price)

=== VOLUME ===
20-Day Avg Volume:  {avg_vol:,}
Recent Volume:      {recent_vol:,}
Volume Ratio:       {vol_ratio:.2f}x  ({vol_signal})
OBV Trend:          {obv_trend}

Return a JSON object with EXACTLY this structure:
{{
  "trend_direction": "strong_uptrend|uptrend|sideways|downtrend|strong_downtrend",
  "trend_strength": "strong|moderate|weak",
  "trend_analysis": "2-3 sentence description of the trend",

  "momentum_signal": "bullish|neutral|bearish",
  "rsi_interpretation": "overbought|neutral|oversold",
  "macd_interpretation": "bullish crossover|bullish|neutral|bearish|bearish crossover",
  "momentum_notes": "Key momentum observations",

  "volatility_level": "low|normal|high|extreme",
  "volatility_notes": "Bollinger band and ATR analysis",

  "volume_signal": "accumulation|neutral|distribution",
  "volume_notes": "Volume trend assessment",

  "support_level": <float - estimated near support>,
  "resistance_level": <float - estimated near resistance>,
  "key_level_notes": "Analysis of support/resistance levels",

  "entry_timing": "strong_entry|good_entry|neutral|wait_for_pullback|risky",
  "entry_timing_rationale": "Why this timing assessment for a value investor",
  "suggested_entry_zone": "Brief description of ideal entry price range",

  "technical_score": <integer 1-10, 10=most technically attractive>,
  "technical_summary": "2-3 sentence overall technical assessment for a long-term investor"
}}"""


def _compute_indicators(price_history: list) -> dict:
    """Compute all technical indicators from raw price history."""
    if not price_history or len(price_history) < 20:
        return {"error": "Insufficient price history (< 20 data points)"}

    try:
        import ta
    except ImportError:
        return {"error": "ta library not installed. Run: pip install ta"}

    df = pd.DataFrame(price_history)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)
    n = len(df)

    ind = {}

    # ── Price reference ──────────────────────────────────────────────────────
    ind["current_price"] = round(float(close.iloc[-1]), 2)

    def ret(days):
        if n >= days + 1:
            return round((float(close.iloc[-1]) / float(close.iloc[-(days + 1)]) - 1) * 100, 2)
        return None

    ind["return_1m"] = ret(22)
    ind["return_3m"] = ret(66)
    ind["return_6m"] = ret(132)
    ind["return_1y"] = ret(252)

    # ── 52-week high/low ─────────────────────────────────────────────────────
    lookback = min(252, n)
    ind["week_52_high"] = round(float(high.tail(lookback).max()), 2)
    ind["week_52_low"] = round(float(low.tail(lookback).min()), 2)
    ind["pct_from_high"] = round((float(close.iloc[-1]) / ind["week_52_high"] - 1) * 100, 2)
    ind["pct_from_low"] = round((float(close.iloc[-1]) / ind["week_52_low"] - 1) * 100, 2)

    # ── Moving averages ──────────────────────────────────────────────────────
    ind["sma_20"] = round(float(ta.trend.sma_indicator(close, 20).iloc[-1]), 2)
    ind["sma_50"] = round(float(ta.trend.sma_indicator(close, 50).iloc[-1]), 2) if n >= 50 else None
    ind["sma_200"] = round(float(ta.trend.sma_indicator(close, 200).iloc[-1]), 2) if n >= 200 else None
    ind["above_sma_20"] = float(close.iloc[-1]) > ind["sma_20"]
    ind["above_sma_50"] = float(close.iloc[-1]) > ind["sma_50"] if ind["sma_50"] else None
    ind["above_sma_200"] = float(close.iloc[-1]) > ind["sma_200"] if ind["sma_200"] else None
    if ind["sma_50"] and ind["sma_200"]:
        ind["golden_cross"] = ind["sma_50"] > ind["sma_200"]

    # ── Momentum ─────────────────────────────────────────────────────────────
    ind["rsi"] = round(float(ta.momentum.rsi(close, 14).iloc[-1]), 1)

    macd_obj = ta.trend.MACD(close)
    ind["macd"] = round(float(macd_obj.macd().iloc[-1]), 4)
    ind["macd_signal"] = round(float(macd_obj.macd_signal().iloc[-1]), 4)
    ind["macd_histogram"] = round(float(macd_obj.macd_diff().iloc[-1]), 4)

    stoch = ta.momentum.StochasticOscillator(high, low, close)
    ind["stoch_k"] = round(float(stoch.stoch().iloc[-1]), 1)

    # ── Bollinger Bands ──────────────────────────────────────────────────────
    bb = ta.volatility.BollingerBands(close)
    ind["bb_upper"] = round(float(bb.bollinger_hband().iloc[-1]), 2)
    ind["bb_middle"] = round(float(bb.bollinger_mavg().iloc[-1]), 2)
    ind["bb_lower"] = round(float(bb.bollinger_lband().iloc[-1]), 2)

    # ── ATR ──────────────────────────────────────────────────────────────────
    ind["atr"] = round(float(ta.volatility.average_true_range(high, low, close, 14).iloc[-1]), 2)
    ind["atr_pct"] = round(ind["atr"] / float(close.iloc[-1]) * 100, 2)

    # ── Volume ───────────────────────────────────────────────────────────────
    avg_vol = float(volume.rolling(20).mean().iloc[-1])
    recent_vol = float(volume.iloc[-1])
    ind["avg_volume_20d"] = int(avg_vol)
    ind["recent_volume"] = int(recent_vol)
    ind["volume_ratio"] = round(recent_vol / avg_vol, 2) if avg_vol > 0 else 1.0

    obv = ta.volume.on_balance_volume(close, volume)
    ind["obv_trend"] = "rising" if float(obv.iloc[-1]) > float(obv.iloc[-20]) else "falling"

    return ind


def _format_optional(val, fmt="{:.2f}", default="N/A"):
    if val is None:
        return default
    try:
        return fmt.format(val)
    except (TypeError, ValueError):
        return default


def technical_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Technical Analysis Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    price_history = state.get("price_history", [])
    analysis_date = state.get("analysis_date", "")

    ind = _compute_indicators(price_history)

    if "error" in ind:
        logger.warning("Technical indicators error for %s: %s", ticker, ind["error"])
        return {"technical_analysis": {"error": ind["error"], "technical_score": 5, "entry_timing": "neutral"}}

    # Derived signal labels
    rsi = ind.get("rsi", 50)
    rsi_signal = "overbought (>70)" if rsi > 70 else "oversold (<30)" if rsi < 30 else "neutral (30-70)"

    macd_hist = ind.get("macd_histogram", 0)
    macd_verdict = "bullish momentum" if macd_hist > 0 else "bearish momentum"

    sma_200_str = f"${ind['sma_200']:.2f}" if ind.get("sma_200") else "N/A (< 200 days of data)"
    rel_sma200 = ""
    if ind.get("above_sma_200") is not None:
        rel_sma200 = "Price ABOVE SMA200 (bullish)" if ind["above_sma_200"] else "Price BELOW SMA200 (bearish)"
    else:
        rel_sma200 = "Insufficient data for SMA200"

    cross_signal = "N/A"
    if "golden_cross" in ind:
        cross_signal = "GOLDEN CROSS (SMA50 > SMA200, bullish)" if ind["golden_cross"] else "DEATH CROSS (SMA50 < SMA200, bearish)"

    bb_price = ind.get("current_price", 0)
    bb_upper = ind.get("bb_upper", 0)
    bb_lower = ind.get("bb_lower", 0)
    bb_mid = ind.get("bb_middle", 0)
    if bb_upper and bb_lower:
        if bb_price >= bb_upper * 0.98:
            bb_position = "Near/above upper band (overbought)"
        elif bb_price <= bb_lower * 1.02:
            bb_position = "Near/below lower band (oversold)"
        else:
            bb_position = f"Middle of bands (${bb_lower:.2f} - ${bb_upper:.2f})"
    else:
        bb_position = "N/A"

    vol_ratio = ind.get("volume_ratio", 1)
    vol_signal = "high volume spike" if vol_ratio > 2 else "above average" if vol_ratio > 1.3 else "normal" if vol_ratio > 0.7 else "low volume"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        analysis_date=analysis_date,
        current_price=ind.get("current_price", 0),
        week_52_high=ind.get("week_52_high", 0),
        week_52_low=ind.get("week_52_low", 0),
        pct_from_high=ind.get("pct_from_high", 0),
        pct_from_low=ind.get("pct_from_low", 0),
        return_1m=_format_optional(ind.get("return_1m"), "{:+.1f}"),
        return_3m=_format_optional(ind.get("return_3m"), "{:+.1f}"),
        return_6m=_format_optional(ind.get("return_6m"), "{:+.1f}"),
        return_1y=_format_optional(ind.get("return_1y"), "{:+.1f}"),
        sma_20=ind.get("sma_20", 0),
        sma_50=ind.get("sma_50") or 0,
        rel_sma20="ABOVE" if ind.get("above_sma_20") else "BELOW",
        rel_sma50="ABOVE" if ind.get("above_sma_50") else ("BELOW" if ind.get("above_sma_50") is False else "N/A"),
        sma_200_str=sma_200_str,
        rel_sma200=rel_sma200,
        cross_signal=cross_signal,
        rsi=rsi,
        rsi_signal=rsi_signal,
        macd=ind.get("macd", 0),
        macd_signal=ind.get("macd_signal", 0),
        macd_hist=ind.get("macd_histogram", 0),
        macd_verdict=macd_verdict,
        stoch_k=ind.get("stoch_k", 50),
        bb_upper=ind.get("bb_upper", 0),
        bb_middle=ind.get("bb_middle", 0),
        bb_lower=ind.get("bb_lower", 0),
        bb_position=bb_position,
        atr=ind.get("atr", 0),
        atr_pct=ind.get("atr_pct", 0),
        avg_vol=ind.get("avg_volume_20d", 0),
        recent_vol=ind.get("recent_volume", 0),
        vol_ratio=vol_ratio,
        vol_signal=vol_signal,
        obv_trend=ind.get("obv_trend", "N/A"),
    )

    logger.info("Running Technical Analysis Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    # Attach raw indicator data for reference
    result["_indicators"] = {k: v for k, v in ind.items() if not k.startswith("_")}

    return {"technical_analysis": result}
