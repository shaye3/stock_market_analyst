#!/usr/bin/env python3
"""
Calculate technical indicators for a stock ticker using yfinance + ta library.
Output: JSON with trend, momentum, volatility, volume, and price structure indicators.

Usage: python calculate_technicals.py AAPL [--period 1y]
"""

import sys
import json
import argparse
import warnings
import yfinance as yf
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


def safe_float(val) -> float | None:
    try:
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return None
        return round(float(val), 4)
    except Exception:
        return None


def safe_series_tail(series: pd.Series, n: int = 5) -> list:
    return [safe_float(x) for x in series.dropna().tail(n).tolist()]


def detect_support_resistance(close: pd.Series, window: int = 20) -> dict:
    """Pivot-based support/resistance detection with Fibonacci retracement levels."""
    highs = close.rolling(window).max()
    lows = close.rolling(window).min()
    current = float(close.iloc[-1])

    recent_close = close.tail(90)
    resistance_levels = []
    support_levels = []

    for i in range(window, len(recent_close) - window):
        val = float(recent_close.iloc[i])
        if val == float(highs.iloc[i + window - 1] if i + window - 1 < len(highs) else highs.iloc[-1]):
            resistance_levels.append(val)
        if val == float(lows.iloc[i + window - 1] if i + window - 1 < len(lows) else lows.iloc[-1]):
            support_levels.append(val)

    def cluster(levels, tol=0.01):
        if not levels:
            return []
        levels = sorted(set(levels))
        clusters = [[levels[0]]]
        for lv in levels[1:]:
            if abs(lv - clusters[-1][-1]) / clusters[-1][-1] < tol:
                clusters[-1].append(lv)
            else:
                clusters.append([lv])
        return [round(sum(c) / len(c), 2) for c in clusters]

    high_52w = round(float(close.tail(252).max()), 2)
    low_52w = round(float(close.tail(252).min()), 2)
    fib_range = high_52w - low_52w

    fib_levels = {
        "fib_0":   high_52w,
        "fib_236": round(high_52w - 0.236 * fib_range, 2),
        "fib_382": round(high_52w - 0.382 * fib_range, 2),
        "fib_500": round(high_52w - 0.500 * fib_range, 2),
        "fib_618": round(high_52w - 0.618 * fib_range, 2),
        "fib_786": round(high_52w - 0.786 * fib_range, 2),
        "fib_100": low_52w,
    }

    nearest_fib = min(fib_levels.items(), key=lambda x: abs(x[1] - current))
    nearest_fib_pct_dist = round((current - nearest_fib[1]) / nearest_fib[1] * 100, 2)

    return {
        "key_resistance": cluster(resistance_levels)[-3:] if resistance_levels else [],
        "key_support": cluster(support_levels)[:3] if support_levels else [],
        "52w_high": high_52w,
        "52w_low": low_52w,
        "current_price": round(current, 2),
        "pct_from_52w_high": round((current - high_52w) / high_52w * 100, 2),
        "pct_from_52w_low": round((current - low_52w) / low_52w * 100, 2),
        "fibonacci_levels": fib_levels,
        "nearest_fib_level": nearest_fib[0],
        "nearest_fib_price": nearest_fib[1],
        "nearest_fib_pct_distance": nearest_fib_pct_dist,
    }


def detect_trend(close: pd.Series, sma20: pd.Series, sma50: pd.Series, sma200: pd.Series) -> str:
    """
    Velocity-aware trend detection.

    Uses both the current SMA levels (static snapshot) AND their 5-bar slopes
    (direction) to produce a more accurate signal.  A stock can have
    s200 < s50 > price and look structurally bullish yet be in active
    deterioration — the slope data disambiguates that.

    Signal taxonomy (most bullish → most bearish):
        strong_uptrend              price > s20 > s50 > s200, all MAs rising
        strong_uptrend_losing_momentum  same stack but s20 already falling
        uptrend                     price > s50 > s200
        pullback_in_uptrend         price < s50, MAs still rising, s50 > s200
        pullback_weakening          price < s50, MAs declining, s50 > s200
        death_cross_forming         s20 within 0.5% of s50 from above, both falling
        topping                     s20 crossed below s50, both declining, s50 > s200
        developing_downtrend        price broke below s200, s50 still above it
        downtrend                   price < s50 < s200
        strong_downtrend            price < s20 < s50 < s200
        consolidation               price within 3% of s20, SMAs flat/tight
        mixed                       catch-all
    """
    current = float(close.iloc[-1])
    s20 = safe_float(sma20.iloc[-1])
    s50 = safe_float(sma50.iloc[-1])
    s200 = safe_float(sma200.iloc[-1])

    if not (s20 and s50 and s200):
        return "mixed"

    def ma_slope(series: pd.Series, n: int = 5) -> float:
        """Net change over last n bars (positive = rising, negative = falling)."""
        vals = series.dropna().tail(n)
        return float(vals.iloc[-1]) - float(vals.iloc[0]) if len(vals) >= 2 else 0.0

    slope20 = ma_slope(sma20)
    slope50 = ma_slope(sma50)

    gap_20_50 = s20 - s50          # positive → s20 above s50
    gap_20_50_pct = abs(gap_20_50) / s50

    # ── Perfect bull stack ────────────────────────────────────────────────────
    if current > s20 > s50 > s200:
        if slope20 > 0 and slope50 > 0:
            return "strong_uptrend"
        return "strong_uptrend_losing_momentum"

    # ── Price above s50 and s200 ──────────────────────────────────────────────
    if current > s50 > s200:
        return "uptrend"

    # ── Price below s50 but still above s200; medium-term structure intact ────
    if current < s50 and current > s200 and s50 > s200:
        # Case 1: s20 still above s50 but converging rapidly → imminent death cross
        if gap_20_50 >= 0 and gap_20_50_pct < 0.005 and slope20 < slope50:
            return "death_cross_forming"
        # Case 2: s20 already crossed below s50
        if s20 < s50:
            if slope50 < 0 and slope20 < 0:
                return "topping"            # both MAs declining → major reversal risk
            return "pullback_weakening"     # short MA dipped but medium MA not yet bearish
        # Case 3: s20 still above s50 but both declining → weakening pullback
        if slope20 < 0 and slope50 < 0:
            return "pullback_weakening"
        # Case 4: MAs still rising or flat → healthy pullback to support
        return "pullback_in_uptrend"

    # ── Price below s200 ──────────────────────────────────────────────────────
    if current < s200:
        if current < s20 < s50 < s200:
            return "strong_downtrend"
        if s50 < s200:
            return "downtrend"
        return "developing_downtrend"   # price broke s200 but s50 still above it

    # ── Sideways / consolidation ──────────────────────────────────────────────
    if abs(current - s20) / s20 < 0.03:
        return "consolidation"

    return "mixed"


def detect_divergence(close: pd.Series, indicator: pd.Series, window: int = 5, lookback: int = 60) -> dict:
    """
    Detect regular and hidden divergence between price and a momentum indicator.

    Regular bullish:  price lower low  + indicator higher low  → reversal up
    Regular bearish:  price higher high + indicator lower high  → reversal down
    Hidden  bullish:  price higher low  + indicator lower low   → uptrend continuation
    Hidden  bearish:  price lower high  + indicator higher high → downtrend continuation
    """
    close_r = close.tail(lookback).reset_index(drop=True)
    ind_r = indicator.tail(lookback).reset_index(drop=True)

    price_peaks = []
    price_troughs = []

    for i in range(window, len(close_r) - window):
        val = float(close_r.iloc[i])
        ind_val = safe_float(ind_r.iloc[i])
        if ind_val is None:
            continue
        if all(val >= float(close_r.iloc[i - j]) for j in range(1, window + 1)) and \
           all(val >= float(close_r.iloc[i + j]) for j in range(1, window + 1)):
            price_peaks.append((i, val, ind_val))
        if all(val <= float(close_r.iloc[i - j]) for j in range(1, window + 1)) and \
           all(val <= float(close_r.iloc[i + j]) for j in range(1, window + 1)):
            price_troughs.append((i, val, ind_val))

    result = {
        "regular_bullish": False, "regular_bearish": False,
        "hidden_bullish": False,  "hidden_bearish": False,
        "signal": "none",
    }

    if len(price_peaks) >= 2:
        p1, p2 = price_peaks[-2], price_peaks[-1]
        if p2[1] > p1[1] and p2[2] < p1[2]:
            result["regular_bearish"] = True
            result["signal"] = "regular_bearish"
        elif p2[1] < p1[1] and p2[2] > p1[2]:
            result["hidden_bearish"] = True
            if result["signal"] == "none":
                result["signal"] = "hidden_bearish"

    if len(price_troughs) >= 2:
        t1, t2 = price_troughs[-2], price_troughs[-1]
        if t2[1] < t1[1] and t2[2] > t1[2]:
            result["regular_bullish"] = True
            result["signal"] = "regular_bullish"
        elif t2[1] > t1[1] and t2[2] < t1[2]:
            result["hidden_bullish"] = True
            if result["signal"] == "none":
                result["signal"] = "hidden_bullish"

    return result


def detect_recent_crossover(line1: pd.Series, line2: pd.Series, lookback: int = 10) -> dict:
    """
    Scan the last `lookback` bars for the most recent crossover between line1 and line2.
    Returns the crossover type ('bullish'/'bearish'/'none') and bars_ago.
    """
    diff = line1 - line2
    for i in range(1, min(lookback + 1, len(diff))):
        curr_diff = safe_float(diff.iloc[-i])
        prev_diff = safe_float(diff.iloc[-(i + 1)])
        if curr_diff is None or prev_diff is None:
            continue
        if prev_diff < 0 and curr_diff > 0:
            return {"type": "bullish", "bars_ago": i}
        elif prev_diff > 0 and curr_diff < 0:
            return {"type": "bearish", "bars_ago": i}
    return {"type": "none", "bars_ago": None}


def calculate_technicals(ticker: str, period: str = "1y") -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    if hist.empty:
        return {"error": f"No data for {ticker}"}

    close = hist["Close"]
    high = hist["High"]
    low = hist["Low"]
    volume = hist["Volume"]
    open_ = hist["Open"]

    result = {"ticker": ticker.upper(), "period": period, "data_points": len(close)}

    # ── Trend Indicators ─────────────────────────────────────────────────────
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()

    # ADX (Average Directional Index) — measures trend strength
    if TA_AVAILABLE:
        adx_ind = ta.trend.ADXIndicator(high, low, close, window=14)
        adx = adx_ind.adx()
        adx_pos = adx_ind.adx_pos()   # +DI (bullish directional movement)
        adx_neg = adx_ind.adx_neg()   # -DI (bearish directional movement)
    else:
        # Wilder's manual ADX
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr14_adx = tr.ewm(alpha=1 / 14, adjust=False).mean()
        adx_pos = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr14_adx
        adx_neg = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False).mean() / atr14_adx
        dx = 100 * (adx_pos - adx_neg).abs() / (adx_pos + adx_neg).replace(0, np.nan)
        adx = dx.ewm(alpha=1 / 14, adjust=False).mean()

    adx_val = safe_float(adx.iloc[-1])
    adx_pos_val = safe_float(adx_pos.iloc[-1])
    adx_neg_val = safe_float(adx_neg.iloc[-1])

    # Golden Cross / Death Cross — scan last 20 bars for most recent event
    golden_cross = None
    death_cross = None
    golden_cross_bars_ago = None
    death_cross_bars_ago = None
    if len(sma50.dropna()) > 5 and len(sma200.dropna()) > 5:
        sma50_valid = sma50.dropna()
        sma200_valid = sma200.dropna()
        common_idx = sma50_valid.index.intersection(sma200_valid.index)
        scan_bars = min(20, len(common_idx) - 1)
        for i in range(1, scan_bars + 1):
            prev_diff = float(sma50_valid[common_idx[-(i + 1)]]) - float(sma200_valid[common_idx[-(i + 1)]])
            curr_diff = float(sma50_valid[common_idx[-i]]) - float(sma200_valid[common_idx[-i]])
            if prev_diff < 0 and curr_diff > 0 and golden_cross is None:
                golden_cross = str(common_idx[-i])[:10]
                golden_cross_bars_ago = i
            elif prev_diff > 0 and curr_diff < 0 and death_cross is None:
                death_cross = str(common_idx[-i])[:10]
                death_cross_bars_ago = i
            if golden_cross and death_cross:
                break

    # Parabolic SAR — trend reversal / trailing stop signal
    psar_val = None
    psar_signal = "unavailable"
    if TA_AVAILABLE:
        psar_ind = ta.trend.PSARIndicator(high, low, close)
        psar = psar_ind.psar()
        psar_val = safe_float(psar.iloc[-1])
        if psar_val is not None:
            psar_signal = "bullish" if float(close.iloc[-1]) > psar_val else "bearish"

    result["trend"] = {
        "sma_20": safe_float(sma20.iloc[-1]),
        "sma_50": safe_float(sma50.iloc[-1]),
        "sma_200": safe_float(sma200.iloc[-1]),
        "ema_12": safe_float(ema12.iloc[-1]),
        "ema_26": safe_float(ema26.iloc[-1]),
        "ema_50": safe_float(ema50.iloc[-1]),
        "price_vs_sma20":  safe_float((float(close.iloc[-1]) - float(sma20.iloc[-1]))  / float(sma20.iloc[-1])  * 100) if safe_float(sma20.iloc[-1])  else None,
        "price_vs_sma50":  safe_float((float(close.iloc[-1]) - float(sma50.iloc[-1]))  / float(sma50.iloc[-1])  * 100) if safe_float(sma50.iloc[-1])  else None,
        "price_vs_sma200": safe_float((float(close.iloc[-1]) - float(sma200.iloc[-1])) / float(sma200.iloc[-1]) * 100) if safe_float(sma200.iloc[-1]) else None,
        "golden_cross_date":      golden_cross,
        "golden_cross_bars_ago":  golden_cross_bars_ago,
        "death_cross_date":       death_cross,
        "death_cross_bars_ago":   death_cross_bars_ago,
        "trend_signal": detect_trend(close, sma20, sma50, sma200),
        # ADX
        "adx_14":       adx_val,
        "adx_pos_di":   adx_pos_val,
        "adx_neg_di":   adx_neg_val,
        "trend_strength": (
            "strong_trending" if adx_val and adx_val > 25
            else "weak_trending" if adx_val and adx_val > 20
            else "ranging"       if adx_val
            else "unknown"
        ),
        "adx_di_signal": (
            "bullish" if adx_pos_val and adx_neg_val and adx_pos_val > adx_neg_val
            else "bearish" if adx_pos_val and adx_neg_val
            else "unknown"
        ),
        # Parabolic SAR
        "parabolic_sar":        psar_val,
        "parabolic_sar_signal": psar_signal,
        "sma20_last5":  safe_series_tail(sma20),
        "sma50_last5":  safe_series_tail(sma50),
        "sma200_last5": safe_series_tail(sma200),
    }

    # ── Momentum Indicators ──────────────────────────────────────────────────
    if TA_AVAILABLE:
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd_ind = ta.trend.MACD(close)
        macd_line = macd_ind.macd()
        macd_signal_line = macd_ind.macd_signal()
        macd_hist = macd_ind.macd_diff()
        stoch = ta.momentum.StochasticOscillator(high, low, close)
        stoch_k = stoch.stoch()
        stoch_d = stoch.stoch_signal()
    else:
        # Manual RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        # Manual MACD
        macd_line = ema12 - ema26
        macd_signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - macd_signal_line
        stoch_k = stoch_d = pd.Series([None] * len(close))

    rsi_current = safe_float(rsi.iloc[-1])

    # MACD recent crossover event (last 10 bars)
    macd_crossover_event = detect_recent_crossover(macd_line, macd_signal_line, lookback=10)
    macd_fresh_crossover = macd_crossover_event["bars_ago"] is not None and macd_crossover_event["bars_ago"] <= 5

    # RSI and MACD divergence vs price
    rsi_divergence = detect_divergence(close, rsi, window=5, lookback=60)
    macd_divergence = detect_divergence(close, macd_line, window=5, lookback=60)

    # MFI (Money Flow Index) — volume-weighted RSI
    if TA_AVAILABLE:
        mfi = ta.volume.MFIIndicator(high, low, close, volume, window=14).money_flow_index()
    else:
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume
        prev_tp = typical_price.shift(1)
        positive_flow = raw_money_flow.where(typical_price > prev_tp, 0.0)
        negative_flow = raw_money_flow.where(typical_price <= prev_tp, 0.0)
        pos_sum = positive_flow.rolling(14).sum()
        neg_sum = negative_flow.rolling(14).sum()
        money_ratio = pos_sum / neg_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + money_ratio))

    mfi_current = safe_float(mfi.iloc[-1])

    result["momentum"] = {
        "rsi_14": rsi_current,
        "rsi_signal": (
            "overbought" if rsi_current and rsi_current > 70
            else "oversold" if rsi_current and rsi_current < 30
            else "neutral"
        ),
        "rsi_last5": safe_series_tail(rsi),
        "rsi_divergence":        rsi_divergence["signal"],
        "rsi_divergence_detail": rsi_divergence,
        "macd_line":      safe_float(macd_line.iloc[-1]),
        "macd_signal":    safe_float(macd_signal_line.iloc[-1]),
        "macd_histogram": safe_float(macd_hist.iloc[-1]),
        "macd_crossover_state": (
            "bullish" if safe_float(macd_line.iloc[-1]) and safe_float(macd_signal_line.iloc[-1])
            and float(macd_line.iloc[-1]) > float(macd_signal_line.iloc[-1])
            else "bearish"
        ),
        "macd_crossover_event":   macd_crossover_event,
        "macd_fresh_crossover":   macd_fresh_crossover,
        "macd_hist_last5":        safe_series_tail(macd_hist),
        "macd_divergence":        macd_divergence["signal"],
        "macd_divergence_detail": macd_divergence,
        "stoch_k": safe_float(stoch_k.iloc[-1]) if TA_AVAILABLE else None,
        "stoch_d": safe_float(stoch_d.iloc[-1]) if TA_AVAILABLE else None,
        "stoch_signal": (
            "overbought" if TA_AVAILABLE and safe_float(stoch_k.iloc[-1]) and float(stoch_k.iloc[-1]) > 80
            else "oversold" if TA_AVAILABLE and safe_float(stoch_k.iloc[-1]) and float(stoch_k.iloc[-1]) < 20
            else "neutral"
        ),
        "mfi_14": mfi_current,
        "mfi_signal": (
            "overbought" if mfi_current and mfi_current > 80
            else "oversold" if mfi_current and mfi_current < 20
            else "neutral"
        ),
    }

    # ── Volatility ───────────────────────────────────────────────────────────
    if TA_AVAILABLE:
        bb = ta.volatility.BollingerBands(close, window=20)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_mid = bb.bollinger_mavg()
        bb_width = bb.bollinger_wband()
        atr_ind = ta.volatility.AverageTrueRange(high, low, close, window=14)
        atr = atr_ind.average_true_range()
    else:
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        bb_width = (bb_upper - bb_lower) / bb_mid * 100
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

    current_price = float(close.iloc[-1])
    bb_upper_val = safe_float(bb_upper.iloc[-1])
    bb_lower_val = safe_float(bb_lower.iloc[-1])

    result["volatility"] = {
        "bollinger_upper": bb_upper_val,
        "bollinger_mid":   safe_float(bb_mid.iloc[-1]),
        "bollinger_lower": bb_lower_val,
        "bollinger_width": safe_float(bb_width.iloc[-1]),
        "price_vs_bb": (
            "above_upper" if bb_upper_val and current_price > bb_upper_val
            else "below_lower" if bb_lower_val and current_price < bb_lower_val
            else "within_bands"
        ),
        "atr_14":          safe_float(atr.iloc[-1]),
        "atr_pct_of_price": safe_float(float(atr.iloc[-1]) / current_price * 100) if safe_float(atr.iloc[-1]) else None,
        "hist_volatility_30d": safe_float(close.pct_change().tail(30).std() * (252 ** 0.5) * 100),
    }

    # ── Volume ───────────────────────────────────────────────────────────────
    avg_vol_20 = float(volume.tail(20).mean())
    avg_vol_50 = float(volume.tail(50).mean())
    current_vol = float(volume.iloc[-1])

    if TA_AVAILABLE:
        obv = ta.volume.OnBalanceVolumeIndicator(close, volume).on_balance_volume()
    else:
        obv = (volume * close.pct_change().apply(lambda x: 1 if x > 0 else -1)).cumsum()

    result["volume"] = {
        "current_volume":       int(current_vol),
        "avg_volume_20d":       int(avg_vol_20),
        "avg_volume_50d":       int(avg_vol_50),
        "volume_ratio_vs_avg":  safe_float(current_vol / avg_vol_20) if avg_vol_20 else None,
        "volume_trend":         "increasing" if avg_vol_20 > avg_vol_50 else "decreasing",
        "obv_current":          safe_float(obv.iloc[-1]),
        "obv_trend":            "bullish" if float(obv.iloc[-1]) > float(obv.tail(20).mean()) else "bearish",
        "volume_last5":         [int(x) for x in volume.tail(5).tolist()],
    }

    # ── Price Structure ──────────────────────────────────────────────────────
    result["price_structure"] = detect_support_resistance(close)

    # ── Summary Signal ───────────────────────────────────────────────────────
    bullish_signals = 0
    bearish_signals = 0
    total_signals = 0
    signal_detail = {}

    def count(name: str, cond_bull: bool, cond_bear: bool, weight: int = 1):
        nonlocal bullish_signals, bearish_signals, total_signals
        for _ in range(weight):
            total_signals += 1
            if cond_bull:
                bullish_signals += 1
            elif cond_bear:
                bearish_signals += 1
        signal_detail[name] = "bullish" if cond_bull else ("bearish" if cond_bear else "neutral")

    trend_sig = result["trend"]["trend_signal"]
    trend_strength = result["trend"]["trend_strength"]
    adx_di_sig = result["trend"]["adx_di_signal"]
    trend_is_valid = trend_strength in ("strong_trending", "weak_trending")

    # SMA trend
    # Uptrend signals gated by ADX (avoid false signals in choppy/ranging markets).
    # Bearish reversal signals (death cross, topping) are always counted — a
    # death cross is a death cross regardless of ADX regime.
    count("sma_trend",
          trend_is_valid and trend_sig in ("strong_uptrend", "uptrend", "pullback_in_uptrend"),
          trend_sig in ("strong_downtrend", "downtrend", "developing_downtrend",
                        "death_cross_forming", "topping", "pullback_weakening"))

    # ADX DI crossover (+DI vs -DI direction)
    count("adx_di",
          adx_di_sig == "bullish",
          adx_di_sig == "bearish")

    # Parabolic SAR
    count("parabolic_sar",
          result["trend"]["parabolic_sar_signal"] == "bullish",
          result["trend"]["parabolic_sar_signal"] == "bearish")

    # RSI — trend-aligned: oversold in uptrend = buy, overbought in downtrend = sell
    rsi_sig = result["momentum"]["rsi_signal"]
    count("rsi",
          rsi_sig == "oversold"   and trend_sig not in ("strong_downtrend", "downtrend"),
          rsi_sig == "overbought" and trend_sig not in ("strong_uptrend",   "uptrend"))

    # MACD crossover event — fresh crossovers (≤5 bars) carry double weight
    macd_event = result["momentum"]["macd_crossover_event"]
    count("macd_crossover",
          macd_event["type"] == "bullish",
          macd_event["type"] == "bearish",
          weight=2 if macd_fresh_crossover else 1)

    # RSI divergence — strong reversal signal (double weight)
    rsi_div = result["momentum"]["rsi_divergence"]
    count("rsi_divergence",
          rsi_div == "regular_bullish",
          rsi_div == "regular_bearish",
          weight=2)

    # MACD divergence (double weight)
    macd_div = result["momentum"]["macd_divergence"]
    count("macd_divergence",
          macd_div == "regular_bullish",
          macd_div == "regular_bearish",
          weight=2)

    # MFI — volume-confirmed momentum (trend-aligned)
    mfi_sig = result["momentum"]["mfi_signal"]
    count("mfi",
          mfi_sig == "oversold"   and trend_sig not in ("strong_downtrend", "downtrend"),
          mfi_sig == "overbought" and trend_sig not in ("strong_uptrend",   "uptrend"))

    # OBV trend
    count("obv_trend",
          result["volume"]["obv_trend"] == "bullish",
          result["volume"]["obv_trend"] == "bearish")

    # Bollinger Bands (price at extremes)
    count("bollinger",
          result["volatility"]["price_vs_bb"] == "below_lower",
          result["volatility"]["price_vs_bb"] == "above_upper")

    score = bullish_signals / total_signals if total_signals > 0 else 0.5

    result["summary"] = {
        "bullish_signals":  bullish_signals,
        "bearish_signals":  bearish_signals,
        "neutral_signals":  total_signals - bullish_signals - bearish_signals,
        "total_signals":    total_signals,
        "technical_score":  round(score, 2),
        "overall_signal": (
            "strong_buy" if score >= 0.8
            else "buy"   if score >= 0.6
            else "sell"  if score <= 0.2
            else "avoid" if score <= 0.4
            else "neutral"
        ),
        "timing_assessment": (
            "favorable_entry"   if score >= 0.6
            else "unfavorable_entry" if score <= 0.4
            else "wait_for_clarity"
        ),
        "trend_quality":  trend_strength,
        "signal_detail":  signal_detail,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Calculate technical indicators")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("--period", default="1y", help="Period: 1y, 2y, 6mo, etc.")
    args = parser.parse_args()

    result = calculate_technicals(args.ticker, args.period)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
