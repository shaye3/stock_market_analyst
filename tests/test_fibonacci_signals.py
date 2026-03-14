"""
Unit tests for detect_fibonacci_signals in tools/calculate_technicals.py

Run:  .venv/bin/pytest tests/test_fibonacci_signals.py -v
"""
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, "tools")
from calculate_technicals import detect_fibonacci_signals

# ─── Shared constants ────────────────────────────────────────────────────────
SW_LO = 100.0
SW_HI = 200.0
FIB618_UP = SW_HI - 0.618 * (SW_HI - SW_LO)   # 138.2 — uptrend pullback target
FIB618_DN = SW_LO + 0.618 * (SW_HI - SW_LO)   # 161.8 — downtrend bounce target
FIB500    = SW_HI - 0.500 * (SW_HI - SW_LO)   # 150.0
FIB382    = SW_HI - 0.382 * (SW_HI - SW_LO)   # 161.8 → actually 161.8 for 38.2%
SPREAD    = 0.005

# ─── Helpers ─────────────────────────────────────────────────────────────────

def S(arr) -> pd.Series:
    return pd.Series(arr, dtype=float)


def make_ohlcv(phases: list[tuple], spread: float = SPREAD):
    """
    Build a synthetic OHLCV series from linear phases.
    Each phase is (start_price, end_price, n_bars).
    Joint bars (turning points) get an accentuated high or low
    to ensure they are detected as clean pivots.
    """
    segments, joints = [], []
    bar = 0
    for i, (start, end, nbars) in enumerate(phases):
        segments.append(np.linspace(start, end, nbars))
        bar += nbars
        if i < len(phases) - 1:
            joints.append(bar - 1)
    close = np.concatenate(segments)
    high  = close * (1 + spread)
    low   = close * (1 - spread)
    for j in joints:
        if j > 0 and close[j] > close[j - 1]:   # local max
            high[j] = close[j] * (1 + spread * 3)
        else:                                     # local min
            low[j]  = close[j] * (1 - spread * 3)
    volume = np.full(len(close), 1_000_000.0)
    return close, high, low, volume


def uptrend_at(pullback_to: float, rsi: float = 40.0, sma50_offset: float = -0.003):
    """Uptrend (decline→rise→pullback) ending at *pullback_to*."""
    c, h, l, v = make_ohlcv([(150, SW_LO, 25), (SW_LO, SW_HI, 40), (SW_HI, pullback_to, 30)])
    n = len(c)
    sma50 = pullback_to * (1 + sma50_offset)
    return (
        S(c), S(h), S(l), S(v), S(np.full(n, rsi)),
        S(np.full(n, pullback_to + 5)),  # sma20 — above level
        S(np.full(n, sma50)),            # sma50 — near level → confluence
        S(np.full(n, 80.0)),             # sma200
    )


def downtrend_at(bounce_to: float, rsi: float = 60.0, sma50_offset: float = 0.003):
    """Downtrend (rise→fall→bounce) ending at *bounce_to*."""
    c, h, l, v = make_ohlcv([(150, SW_HI, 25), (SW_HI, SW_LO, 40), (SW_LO, bounce_to, 30)])
    n = len(c)
    sma50 = bounce_to * (1 + sma50_offset)
    return (
        S(c), S(h), S(l), S(v), S(np.full(n, rsi)),
        S(np.full(n, bounce_to + 10)),
        S(np.full(n, sma50)),
        S(np.full(n, 220.0)),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. ANCHOR DIRECTION
# ═══════════════════════════════════════════════════════════════════════════

class TestAnchorDirection:
    def test_uptrend_when_swing_high_after_swing_low(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r.get("anchor_direction") == "uptrend"

    def test_downtrend_when_swing_low_after_swing_high(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        assert r.get("anchor_direction") == "downtrend"


# ═══════════════════════════════════════════════════════════════════════════
# 2. RETRACEMENT LEVEL VALUES & ORDERING
# ═══════════════════════════════════════════════════════════════════════════

class TestRetracementLevels:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.r_up   = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        self.r_dn   = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        self.KEYS   = ["fib_0","fib_236","fib_382","fib_500","fib_618","fib_786","fib_100"]

    def test_seven_retracement_levels_present(self):
        assert len(self.r_up["retracement_levels"]) == 7

    def test_two_extension_levels_present(self):
        assert len(self.r_up["extension_levels"]) == 2

    def test_uptrend_levels_strictly_descending(self):
        vals = [self.r_up["retracement_levels"][k] for k in self.KEYS]
        assert vals == sorted(vals, reverse=True), f"Expected descending, got {vals}"

    def test_downtrend_levels_strictly_ascending(self):
        vals = [self.r_dn["retracement_levels"][k] for k in self.KEYS]
        assert vals == sorted(vals), f"Expected ascending, got {vals}"

    def test_uptrend_extensions_above_swing_high(self):
        swing_hi = self.r_up["swing_high"]
        assert self.r_up["extension_levels"]["fib_1272"] > swing_hi
        assert self.r_up["extension_levels"]["fib_1618"] > self.r_up["extension_levels"]["fib_1272"]

    def test_downtrend_extensions_below_swing_low(self):
        swing_lo = self.r_dn["swing_low"]
        assert self.r_dn["extension_levels"]["fib_1272"] < swing_lo
        assert self.r_dn["extension_levels"]["fib_1618"] < self.r_dn["extension_levels"]["fib_1272"]

    def test_fib_618_ratio_correct_uptrend(self):
        rl = self.r_up["retracement_levels"]
        move = rl["fib_0"] - rl["fib_100"]
        expected_618 = rl["fib_0"] - 0.618 * move
        assert abs(rl["fib_618"] - expected_618) < 0.01


# ═══════════════════════════════════════════════════════════════════════════
# 3. PRICE-AT-LEVEL DETECTION
# ═══════════════════════════════════════════════════════════════════════════

class TestPriceAtLevel:
    def test_at_golden_ratio_true_when_price_at_618(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["at_golden_ratio"] is True

    def test_at_golden_ratio_false_when_price_at_500(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB500))
        assert r["at_golden_ratio"] is False

    def test_fib_618_in_at_fib_levels(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert "fib_618" in r["at_fib_levels"]

    def test_fib_500_in_at_fib_levels(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB500))
        assert "fib_500" in r["at_fib_levels"]

    def test_nearest_retracement_is_fib_500_when_price_at_500(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB500))
        assert r["nearest_retracement"] == "fib_500"

    def test_nearest_retracement_pct_dist_near_zero_when_at_level(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert abs(r["nearest_retracement_pct_dist"]) < 1.5  # within entry_tol band


# ═══════════════════════════════════════════════════════════════════════════
# 4. ENTRY SIGNALS
# ═══════════════════════════════════════════════════════════════════════════

class TestEntrySignals:
    def test_bullish_entry_all_conditions_met(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP, rsi=40.0))
        assert r["entry_signal"] == "bullish_entry"

    def test_bearish_entry_all_conditions_met(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN, rsi=60.0))
        assert r["entry_signal"] == "bearish_entry"

    def test_no_entry_rsi_too_high_for_bull(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP, rsi=55.0))
        assert r["entry_signal"] == "none"
        assert r["entry_conditions"]["rsi_below_threshold"] is False

    def test_no_entry_rsi_too_low_for_bear(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN, rsi=40.0))
        assert r["entry_signal"] == "none"
        assert r["entry_conditions"]["rsi_above_threshold"] is False

    def test_no_entry_low_volume(self):
        c, h, l, v, rsi, s20, s50, s200 = uptrend_at(FIB618_UP, rsi=40.0)
        v_low = v.copy()
        v_low.iloc[-1] = float(v.mean()) * 0.80   # 80% of avg < threshold 85%
        r = detect_fibonacci_signals(c, h, l, v_low, rsi, s20, s50, s200)
        assert r["entry_signal"] == "none"
        assert r["entry_conditions"]["volume_confirmed"] is False

    def test_no_entry_price_far_from_all_levels(self):
        # Price ends at a level not matching any Fib (between fib_382 and fib_236)
        mid = SW_HI - 0.30 * (SW_HI - SW_LO)   # ~170, between 23.6% and 38.2%
        r = detect_fibonacci_signals(*uptrend_at(mid, rsi=40.0))
        assert r["entry_signal"] == "none"
        assert r["entry_conditions"]["price_at_level"] is False

    def test_entry_fires_without_ma_confluence(self):
        c, h, l, v, rsi, _, _, _ = uptrend_at(FIB618_UP, rsi=40.0)
        n = len(c)
        sma_far = S(np.full(n, 50.0))  # far from any Fib level
        r = detect_fibonacci_signals(c, h, l, v, rsi, sma_far, sma_far, sma_far)
        assert r["entry_signal"] == "bullish_entry"
        assert r["has_confluence_at_golden_ratio"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. MA CONFLUENCE
# ═══════════════════════════════════════════════════════════════════════════

class TestConfluence:
    def test_confluence_detected_when_sma_near_618(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP, sma50_offset=-0.003))
        assert r["has_confluence_at_golden_ratio"] is True
        assert any("fib_618" in tag for tag in r["confluence_levels"])

    def test_no_confluence_when_sma_far_from_618(self):
        c, h, l, v, rsi, _, _, _ = uptrend_at(FIB618_UP)
        n = len(c)
        sma_far = S(np.full(n, 50.0))
        r = detect_fibonacci_signals(c, h, l, v, rsi, sma_far, sma_far, sma_far)
        assert r["has_confluence_at_golden_ratio"] is False
        assert r["confluence_levels"] == []

    def test_multiple_sma_confluence_tags_returned(self):
        c, h, l, v, rsi, _, _, _ = uptrend_at(FIB618_UP)
        n = len(c)
        sma_at_618 = S(np.full(n, FIB618_UP * 0.998))  # within 1% of fib_618
        # All three SMAs near the level
        r = detect_fibonacci_signals(c, h, l, v, rsi, sma_at_618, sma_at_618, sma_at_618)
        tags_at_618 = [t for t in r["confluence_levels"] if "fib_618" in t]
        assert len(tags_at_618) == 3  # sma20, sma50, sma200


# ═══════════════════════════════════════════════════════════════════════════
# 6. STOP-LOSS PLACEMENT
# ═══════════════════════════════════════════════════════════════════════════

class TestStopLoss:
    def test_stop_loss_set_on_bullish_entry(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["stop_loss_level"] is not None

    def test_stop_loss_set_on_bearish_entry(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        assert r["stop_loss_level"] is not None

    def test_stop_loss_none_when_no_entry(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP, rsi=60.0))
        assert r["stop_loss_level"] is None

    def test_stop_loss_deeper_than_entry_in_uptrend(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        # entry at fib_618 → stop at fib_786 which is below fib_618 in uptrend
        assert r["stop_loss_level"] < r["retracement_levels"]["fib_618"]

    def test_stop_loss_above_entry_in_downtrend(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        # Short at fib_618 bounce → stop at fib_786 (deeper bounce = higher price in downtrend model)
        # Adverse direction for a short = price rising → stop must be ABOVE the entry price
        assert r["stop_loss_level"] > r["retracement_levels"]["fib_618"]


# ═══════════════════════════════════════════════════════════════════════════
# 7. TARGETS
# ═══════════════════════════════════════════════════════════════════════════

class TestTargets:
    def test_target1_is_move_end_uptrend(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert abs(r["target_1_swing_end"] - r["swing_high"]) < 0.01

    def test_target1_is_move_end_downtrend(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        assert abs(r["target_1_swing_end"] - r["swing_low"]) < 0.01

    def test_target2_is_1272_extension(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["target_2_ext_1272"] == r["extension_levels"]["fib_1272"]

    def test_target3_is_1618_extension(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["target_3_ext_1618"] == r["extension_levels"]["fib_1618"]

    def test_targets_ascending_in_uptrend(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["target_1_swing_end"] < r["target_2_ext_1272"] < r["target_3_ext_1618"]

    def test_targets_descending_in_downtrend(self):
        r = detect_fibonacci_signals(*downtrend_at(FIB618_DN))
        assert r["target_1_swing_end"] > r["target_2_ext_1272"] > r["target_3_ext_1618"]


# ═══════════════════════════════════════════════════════════════════════════
# 8. BARS METADATA
# ═══════════════════════════════════════════════════════════════════════════

class TestBarsMetadata:
    def test_bars_since_anchor_is_int(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert isinstance(r["bars_since_anchor"], int)

    def test_bars_since_anchor_matches_pullback_length(self):
        # Pullback phase is 30 bars → bars_since_anchor should be ~29
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert 0 <= r["bars_since_anchor"] < 35

    def test_swing_high_bars_ago_positive(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["swing_high_bars_ago"] >= 0

    def test_swing_low_bars_ago_positive(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        assert r["swing_low_bars_ago"] >= 0


# ═══════════════════════════════════════════════════════════════════════════
# 9. EDGE CASES & ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_short_series_returns_insufficient_pivot_data(self):
        short = S(np.array([100.0] * 10))
        r = detect_fibonacci_signals(short, short, short, short, short, short, short, short)
        assert r["error"] == "insufficient_pivot_data"
        assert r["entry_signal"] == "none"

    def test_anchor_gap_too_large_returns_error(self):
        # Two phases: decline (swing_low at bar 24) then rise to bar 79 (swing_high)
        # Gap in lookback window = ~55 bars; max_anchor_gap=20 → no valid pair.
        c, h, l, v = make_ohlcv([(200, 100, 25), (100, 200, 55), (200, 195, 10)])
        n = len(c)
        sma = S(np.full(n, 150.0))
        r = detect_fibonacci_signals(S(c), S(h), S(l), S(v),
                                     S(np.full(n, 40.0)), sma, sma, sma,
                                     max_anchor_gap=20)
        assert r.get("error") in ("no_valid_anchor_pair", "insufficient_pivot_data")

    def test_all_required_output_keys_present(self):
        r = detect_fibonacci_signals(*uptrend_at(FIB618_UP))
        required = [
            "anchor_direction", "swing_high", "swing_high_bars_ago",
            "swing_low", "swing_low_bars_ago", "bars_since_anchor",
            "retracement_levels", "extension_levels", "current_price",
            "nearest_retracement", "nearest_retracement_price",
            "nearest_retracement_pct_dist", "at_fib_levels",
            "at_golden_ratio", "has_confluence_at_golden_ratio",
            "confluence_levels", "entry_signal", "entry_conditions",
            "stop_loss_level", "target_1_swing_end",
            "target_2_ext_1272", "target_3_ext_1618",
        ]
        missing = [k for k in required if k not in r]
        assert missing == [], f"Missing keys: {missing}"


# ═══════════════════════════════════════════════════════════════════════════
# 10. SUMMARY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class TestSummaryIntegration:
    """Verify fibonacci_entry is wired into calculate_technicals summary."""

    def test_summary_fibonacci_entry_key_exists(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        assert "fibonacci_entry" in result["summary"]["signal_detail"]

    def test_summary_fibonacci_entry_valid_value(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        val = result["summary"]["signal_detail"]["fibonacci_entry"]
        assert val in ("bullish", "bearish", "neutral"), f"Unexpected: {val}"

    def test_fibonacci_section_present_in_output(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        assert "fibonacci" in result
        assert "entry_signal" in result["fibonacci"]
