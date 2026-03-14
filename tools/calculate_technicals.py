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


def detect_role_reversal_levels(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    window: int = 10,
    lookback: int = 252,
    breakout_closes: int = 2,
    retest_window: int = 30,
    proximity_pct: float = 0.12,
) -> dict:
    """
    Detect S/R levels that have undergone a polarity flip (role reversal).

    Resistance → Support: price breaks convincingly above a former resistance;
                          that level now provides support on pullbacks.
    Support → Resistance: price breaks convincingly below a former support;
                          that level now caps rallies.

    Each returned level includes:
        price            – the level price
        original_role    – 'resistance' or 'support'
        current_role     – flipped role
        broken_bars_ago  – how long ago the breakout was confirmed
        retest_detected  – True if price has since returned to test the level
        retest_held      – True if the level held on retest (confirmed flip)
        confirmed        – retest_detected AND retest_held
    """
    n  = min(lookback, len(close))
    c  = close.tail(n).reset_index(drop=True)
    h  = high.tail(n).reset_index(drop=True)
    lo = low.tail(n).reset_index(drop=True)

    # ATR-14 for adaptive breakout buffer and retest-zone sizing
    tr = pd.concat([
        h - lo,
        (h - c.shift()).abs(),
        (lo - c.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    # ── 1. Identify pivot highs (resistance) and pivot lows (support) ─────────
    pivots = []
    for i in range(window, len(c) - window):
        val   = float(c.iloc[i])
        atr_i = float(atr.iloc[i]) if not pd.isna(atr.iloc[i]) else val * 0.01
        if (all(val >= float(c.iloc[i - j]) for j in range(1, window + 1)) and
                all(val >= float(c.iloc[i + j]) for j in range(1, window + 1))):
            pivots.append({'idx': i, 'price': val, 'atr': atr_i, 'role': 'resistance'})
        elif (all(val <= float(c.iloc[i - j]) for j in range(1, window + 1)) and
              all(val <= float(c.iloc[i + j]) for j in range(1, window + 1))):
            pivots.append({'idx': i, 'price': val, 'atr': atr_i, 'role': 'support'})

    # ── 2. Cluster nearby pivots (1 % price tolerance, keep most recent) ──────
    def cluster_pivots(pvts: list, tol: float = 0.01) -> list:
        if not pvts:
            return []
        pvts = sorted(pvts, key=lambda x: x['price'])
        groups: list = [[pvts[0]]]
        for p in pvts[1:]:
            if abs(p['price'] - groups[-1][-1]['price']) / groups[-1][-1]['price'] < tol:
                groups[-1].append(p)
            else:
                groups.append([p])
        return [max(g, key=lambda x: x['idx']) for g in groups]

    all_pivots = (
        cluster_pivots([p for p in pivots if p['role'] == 'resistance']) +
        cluster_pivots([p for p in pivots if p['role'] == 'support'])
    )

    # ── 3. Detect breakouts and retests for each pivot ────────────────────────
    current = float(c.iloc[-1])
    flipped = []

    for piv in all_pivots:
        idx   = piv['idx']
        price = piv['price']
        role  = piv['role']
        buf   = piv['atr'] * 0.5  # half-ATR confirmation buffer

        # Require `breakout_closes` consecutive closes past the level
        breakout_idx = None
        streak = 0
        if role == 'resistance':
            for j in range(idx + 1, len(c)):
                streak = streak + 1 if float(c.iloc[j]) > price + buf else 0
                if streak >= breakout_closes:
                    breakout_idx = j
                    break
        else:
            for j in range(idx + 1, len(c)):
                streak = streak + 1 if float(c.iloc[j]) < price - buf else 0
                if streak >= breakout_closes:
                    breakout_idx = j
                    break

        if breakout_idx is None:
            continue  # level never broken — not a flip candidate

        new_role    = 'support' if role == 'resistance' else 'resistance'
        atr_b       = float(atr.iloc[breakout_idx]) if not pd.isna(atr.iloc[breakout_idx]) else price * 0.01
        retest_zone = atr_b  # within 1 ATR = "retested"

        retest_detected = retest_held = False
        retest_scan_end = min(breakout_idx + 1 + retest_window, len(c))
        for j in range(breakout_idx + 1, retest_scan_end):
            if abs(float(c.iloc[j]) - price) <= retest_zone:
                retest_detected = True
                # "Held" = price does NOT produce `breakout_closes` consecutive
                # closes back through the level (symmetric with the breakout logic)
                fail_streak = 0
                retest_held  = True
                for k in range(j, min(j + retest_window, len(c))):
                    close_k = float(c.iloc[k])
                    failed  = (
                        close_k < price - buf if new_role == 'support'
                        else close_k > price + buf
                    )
                    if failed:
                        fail_streak += 1
                        if fail_streak >= breakout_closes:
                            retest_held = False
                            break
                    else:
                        fail_streak = 0
                break

        flipped.append({
            'price':           round(price, 2),
            'original_role':   role,
            'current_role':    new_role,
            'broken_bars_ago': len(c) - 1 - breakout_idx,
            'retest_detected': retest_detected,
            'retest_held':     retest_held,
            'confirmed':       retest_detected and retest_held,
        })

    # ── 4. Return only levels within proximity_pct of current price ───────────
    near = [f for f in flipped if abs(f['price'] - current) / current <= proximity_pct]

    return {
        # Closest below current price (former resistance, now support)
        'former_resistance_now_support': sorted(
            [f for f in near if f['current_role'] == 'support' and f['price'] <= current],
            key=lambda x: -x['price'],
        )[:3],
        # Closest above current price (former support, now resistance)
        'former_support_now_resistance': sorted(
            [f for f in near if f['current_role'] == 'resistance' and f['price'] >= current],
            key=lambda x: x['price'],
        )[:3],
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


def detect_fibonacci_signals(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    rsi: pd.Series,
    sma20: pd.Series,
    sma50: pd.Series,
    sma200: pd.Series,
    lookback: int = 90,
    window: int = 5,
    max_anchor_gap: int = 60,
    confluence_tol: float = 0.01,
    entry_tol: float = 0.015,
    rsi_bull_threshold: float = 45,
    rsi_bear_threshold: float = 55,
    volume_threshold: float = 0.85,
) -> dict:
    """
    Swing-anchored Fibonacci retracement/extension with entry signals.

    Detects recent swing high/low pivots, computes retracement and extension
    levels, checks MA confluence, and generates entry signals with stop-loss
    and target levels.
    """
    high_r = high.tail(lookback).reset_index(drop=True)
    low_r = low.tail(lookback).reset_index(drop=True)

    swing_highs = []  # (index_in_lookback_window, price)
    swing_lows = []

    for i in range(window, len(high_r) - window):
        h_val = float(high_r.iloc[i])
        l_val = float(low_r.iloc[i])
        if all(h_val >= float(high_r.iloc[i - j]) for j in range(1, window + 1)) and \
           all(h_val >= float(high_r.iloc[i + j]) for j in range(1, window + 1)):
            swing_highs.append((i, h_val))
        if all(l_val <= float(low_r.iloc[i - j]) for j in range(1, window + 1)) and \
           all(l_val <= float(low_r.iloc[i + j]) for j in range(1, window + 1)):
            swing_lows.append((i, l_val))

    if len(swing_highs) < 1 or len(swing_lows) < 1:
        return {"error": "insufficient_pivot_data", "entry_signal": "none"}

    # Find valid anchor pair: most recent swing high + most recent swing low
    # within max_anchor_gap bars of each other
    anchor_high = None
    anchor_low = None

    for hi in reversed(swing_highs):
        for lo in reversed(swing_lows):
            if abs(hi[0] - lo[0]) <= max_anchor_gap:
                anchor_high = hi
                anchor_low = lo
                break
        if anchor_high is not None:
            break

    if anchor_high is None or anchor_low is None:
        return {"error": "no_valid_anchor_pair", "entry_signal": "none"}

    last_high_idx, swing_high_price = anchor_high
    last_low_idx, swing_low_price = anchor_low

    move_size = swing_high_price - swing_low_price
    if move_size <= 0:
        return {"error": "degenerate_swing", "entry_signal": "none"}

    # Anchor direction: index of the more recent pivot determines trend direction
    if last_high_idx > last_low_idx:
        anchor_direction = "uptrend"
        move_start = swing_low_price
        move_end = swing_high_price
        bars_since_anchor = (lookback - 1) - last_high_idx
        # Retracements: pull back DOWN from move_end
        def retrace(ratio):
            return round(move_end - ratio * move_size, 4)
        # Extensions: project UP beyond move_end
        def extend(ratio):
            return round(move_end + ratio * move_size, 4)
    else:
        anchor_direction = "downtrend"
        move_start = swing_high_price
        move_end = swing_low_price
        bars_since_anchor = (lookback - 1) - last_low_idx
        # Retracements: bounce UP from move_end
        def retrace(ratio):
            return round(move_end + ratio * move_size, 4)
        # Extensions: project DOWN below move_end
        def extend(ratio):
            return round(move_end - ratio * move_size, 4)

    retracement_levels = {
        "fib_0":   round(move_end, 4),
        "fib_236": retrace(0.236),
        "fib_382": retrace(0.382),
        "fib_500": retrace(0.500),
        "fib_618": retrace(0.618),
        "fib_786": retrace(0.786),
        "fib_100": round(move_start, 4),
    }
    extension_levels = {
        "fib_1272": extend(0.272),   # 127.2% from move_end perspective
        "fib_1618": extend(0.618),   # 161.8% from move_end perspective
    }

    current_price = float(close.iloc[-1])

    # Nearest retracement level
    nearest_key = min(retracement_levels, key=lambda k: abs(retracement_levels[k] - current_price))
    nearest_price = retracement_levels[nearest_key]
    nearest_pct_dist = round((current_price - nearest_price) / nearest_price * 100, 4)

    # Which retracement levels is price at (within entry_tol)?
    at_fib_levels = [
        k for k, v in retracement_levels.items()
        if abs(current_price - v) / v <= entry_tol
    ]
    at_golden_ratio = "fib_618" in at_fib_levels

    # MA confluence: which Fib levels are within confluence_tol of SMA20/50/200?
    ma_values = {
        "sma20":  safe_float(sma20.iloc[-1]),
        "sma50":  safe_float(sma50.iloc[-1]),
        "sma200": safe_float(sma200.iloc[-1]),
    }
    confluence_levels = []
    all_levels = {**retracement_levels, **extension_levels}
    for fib_key, fib_price in all_levels.items():
        for ma_name, ma_val in ma_values.items():
            if ma_val is not None and abs(fib_price - ma_val) / ma_val <= confluence_tol:
                confluence_levels.append(f"{fib_key}_near_{ma_name}")

    # Explicit flag: 61.8% + MA confluence
    fib_618_price = retracement_levels["fib_618"]
    has_confluence_at_golden_ratio = any(
        ma_val is not None and abs(fib_618_price - ma_val) / ma_val <= confluence_tol
        for ma_val in ma_values.values()
    )

    # Entry signal conditions
    rsi_current = safe_float(rsi.iloc[-1])
    avg_vol_20 = float(volume.tail(20).mean())
    current_vol = float(volume.iloc[-1])
    vol_ok = (current_vol >= volume_threshold * avg_vol_20) if avg_vol_20 > 0 else False

    price_at_fib_level = len(at_fib_levels) > 0
    price_at_golden = at_golden_ratio

    bull_conditions = {
        "uptrend_anchor": anchor_direction == "uptrend",
        "price_at_level": price_at_fib_level,
        "rsi_below_threshold": rsi_current is not None and rsi_current < rsi_bull_threshold,
        "volume_confirmed": vol_ok,
    }
    bear_conditions = {
        "downtrend_anchor": anchor_direction == "downtrend",
        "price_at_level": price_at_fib_level,
        "rsi_above_threshold": rsi_current is not None and rsi_current > rsi_bear_threshold,
        "volume_confirmed": vol_ok,
    }

    if all(bull_conditions.values()):
        entry_signal = "bullish_entry"
        entry_conditions = bull_conditions
    elif all(bear_conditions.values()):
        entry_signal = "bearish_entry"
        entry_conditions = bear_conditions
    else:
        entry_signal = "none"
        entry_conditions = bull_conditions if anchor_direction == "uptrend" else bear_conditions

    # Stop-loss: next adverse Fib level
    retrace_keys = ["fib_0", "fib_236", "fib_382", "fib_500", "fib_618", "fib_786", "fib_100"]
    stop_loss_level = None
    if entry_signal == "bullish_entry" and at_fib_levels:
        # In uptrend pullback, entry near a level → stop is next level deeper (higher index)
        deepest_entry = max(
            (k for k in at_fib_levels if k in retrace_keys),
            key=lambda k: retrace_keys.index(k),
            default=None,
        )
        if deepest_entry:
            idx = retrace_keys.index(deepest_entry)
            if idx + 1 < len(retrace_keys):
                stop_loss_level = safe_float(retracement_levels[retrace_keys[idx + 1]])
    elif entry_signal == "bearish_entry" and at_fib_levels:
        # In downtrend bounce, entry near a level → stop is next level DEEPER into the bounce
        # (adverse direction = price rising further); downtrend levels are ascending so idx+1
        deepest_bounce_entry = max(
            (k for k in at_fib_levels if k in retrace_keys),
            key=lambda k: retrace_keys.index(k),
            default=None,
        )
        if deepest_bounce_entry:
            idx = retrace_keys.index(deepest_bounce_entry)
            if idx + 1 < len(retrace_keys):
                stop_loss_level = safe_float(retracement_levels[retrace_keys[idx + 1]])

    # Bars ago from end of full series (not the lookback window)
    total_bars = len(high)
    swing_high_bars_ago = total_bars - 1 - (total_bars - lookback + last_high_idx)
    swing_low_bars_ago = total_bars - 1 - (total_bars - lookback + last_low_idx)

    return {
        "anchor_direction":             anchor_direction,
        "swing_high":                   round(swing_high_price, 4),
        "swing_high_bars_ago":          int(swing_high_bars_ago),
        "swing_low":                    round(swing_low_price, 4),
        "swing_low_bars_ago":           int(swing_low_bars_ago),
        "bars_since_anchor":            int(bars_since_anchor),
        "retracement_levels":           retracement_levels,
        "extension_levels":             extension_levels,
        "current_price":                round(current_price, 4),
        "nearest_retracement":          nearest_key,
        "nearest_retracement_price":    round(nearest_price, 4),
        "nearest_retracement_pct_dist": nearest_pct_dist,
        "at_fib_levels":                at_fib_levels,
        "at_golden_ratio":              at_golden_ratio,
        "has_confluence_at_golden_ratio": has_confluence_at_golden_ratio,
        "confluence_levels":            confluence_levels,
        "entry_signal":                 entry_signal,
        "entry_conditions":             entry_conditions,
        "stop_loss_level":              stop_loss_level,
        "target_1_swing_end":           round(move_end, 4),
        "target_2_ext_1272":            extension_levels["fib_1272"],
        "target_3_ext_1618":            extension_levels["fib_1618"],
    }


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

    # ── Fibonacci Retracement ─────────────────────────────────────────────────
    result["fibonacci"] = detect_fibonacci_signals(
        close, high, low, volume, rsi,
        sma20, sma50, sma200,
    )

    # ── Price Structure ──────────────────────────────────────────────────────
    result["price_structure"] = detect_support_resistance(close)
    result["price_structure"]["role_reversal"] = detect_role_reversal_levels(close, high, low)

    # Deduplicate: remove key_resistance/key_support entries that have flipped roles.
    # A broken level should not appear with its old label alongside its new one.
    _rr = result["price_structure"]["role_reversal"]
    _flipped_prices = [f['price'] for group in _rr.values() for f in group]
    _tol = current_price * 0.005  # 0.5% proximity tolerance
    result["price_structure"]["key_resistance"] = [
        r for r in result["price_structure"]["key_resistance"]
        if not any(abs(r - fp) <= _tol for fp in _flipped_prices)
    ]
    result["price_structure"]["key_support"] = [
        s for s in result["price_structure"]["key_support"]
        if not any(abs(s - fp) <= _tol for fp in _flipped_prices)
    ]

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

    # Fibonacci entry — double weight when 61.8% + MA confluence
    fib_result = result.get("fibonacci", {})
    fib_entry = fib_result.get("entry_signal", "none")
    fib_golden_confluence = bool(fib_result.get("has_confluence_at_golden_ratio"))
    count("fibonacci_entry",
          fib_entry == "bullish_entry",
          fib_entry == "bearish_entry",
          weight=2 if fib_golden_confluence else 1)

    # Role-reversal structural levels — confirmed flip is a high-conviction signal
    # (former resistance holding as support = bullish; former support capping = bearish)
    _rr_score = result["price_structure"]["role_reversal"]
    count("role_reversal",
          any(f["confirmed"] for f in _rr_score["former_resistance_now_support"]),
          any(f["confirmed"] for f in _rr_score["former_support_now_resistance"]),
          weight=2)

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
