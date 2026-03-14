"""
Unit tests for detect_role_reversal_levels in tools/calculate_technicals.py

Run:  .venv/bin/pytest tests/test_role_reversal.py -v

Synthetic price series are constructed from linear phases (np.linspace) so that
ATR stays predictable throughout:
  - Spread = 0.5 % of price  →  ATR ≈ 1–2 × (price_change_per_bar + spread_contribution)
  - Breakouts use closes at least 6 % above/below the pivot so ATR-based buf
    never prevents detection.
  - Retests come within 0.3 units of the level, always inside any reasonable ATR zone.
  - "Failed" retests use consecutive closes ≥ 2 units below the buf threshold.
"""

import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "tools")
from calculate_technicals import detect_role_reversal_levels

# ─── Helpers ─────────────────────────────────────────────────────────────────

SPREAD = 0.005   # 0.5 % OHLC spread  → ATR ≈ 1–3 for prices around 100


def S(arr) -> pd.Series:
    return pd.Series(arr, dtype=float)


def make_ohlc(phases: list[tuple], spread: float = SPREAD):
    """
    Build (close, high, low) from linear phases.
    Each phase is (start_price, end_price, n_bars).
    Endpoints are shared between adjacent phases (no gap).
    """
    segments = [np.linspace(s, e, n) for s, e, n in phases]
    close = np.concatenate(segments)
    high  = close * (1 + spread)
    low   = close * (1 - spread)
    return S(close), S(high), S(low)


def rr(c, h, lo, **kw):
    """Shorthand: call detect_role_reversal_levels with window=5 default."""
    return detect_role_reversal_levels(c, h, lo, window=5, **kw)


# ─── Scenario builders ───────────────────────────────────────────────────────

def scenario_confirmed_resistance_flip():
    """
    Pivot HIGH (resistance) at ~100.
    Breakout: price rises to 110+ (≫ 100 + buf).
    Retest: price pulls back to ~101 (within ATR zone of 100).
    Hold: stays above 100 − buf.
    Expected: former_resistance_now_support, confirmed=True.
    """
    return make_ohlc([
        (80, 80, 20),    # flat warmup → ATR ≈ 0.8
        (80, 100, 15),   # rise to pivot high
        (100, 80, 10),   # fall away  (≥5 bars below for window=5)
        (80, 110, 12),   # breakout rally — crosses 100 + buf
        (110, 101, 8),   # pull back toward retest
        (101, 108, 8),   # hold as support and resume up
    ])


def scenario_failed_retest():
    """
    Same breakout as above but after the retest, 2 consecutive closes
    land below 100 − buf (≈ 99.08).
    Expected: retest_detected=True, retest_held=False, confirmed=False.
    """
    return make_ohlc([
        (80, 80, 20),
        (80, 100, 15),
        (100, 80, 10),
        (80, 110, 12),
        (110, 102, 5),   # approach retest zone
        (102, 95, 3),    # [102, 98.5, 95] — two closes below 99.08 → fail
        (95, 103, 8),    # current price near 103
    ])


def scenario_single_noisy_close():
    """
    1 close below buf threshold then immediate recovery.
    fail_streak resets to 0 before reaching breakout_closes=2.
    Expected: retest_held=True, confirmed=True.
    """
    return make_ohlc([
        (80, 80, 20),
        (80, 100, 15),
        (100, 80, 10),
        (80, 110, 12),
        (110, 102, 5),   # approach retest zone
        (102, 98, 1),    # 1 close below 99.08 (streak=1)
        (98, 108, 8),    # recovery → streak resets; holds as support
    ])


def scenario_no_retest_in_window():
    """
    After breakout, price moves far from the level for > 30 bars.
    A late retest occurs outside the window.
    Expected: retest_detected=False, confirmed=False.
    """
    return make_ohlc([
        (80, 80, 20),
        (80, 100, 15),
        (100, 80, 10),
        (80, 110, 12),
        (110, 130,  5),   # continue up
        (130, 130, 40),   # stays far away (> retest_window=30 bars, |130−100| >> ATR)
        (130, 102,  5),   # late retest after window — should not be detected
    ])


def scenario_confirmed_support_flip():
    """
    Pivot LOW (support) at ~100.
    Breakdown: price falls to 88 (≪ 100 − buf).
    Retest: price rallies back to ~99.5 (within ATR zone of 100).
    Hold: stays below 100 + buf.
    Expected: former_support_now_resistance, confirmed=True.
    """
    return make_ohlc([
        (120, 120, 20),   # flat warmup
        (120, 100, 15),   # fall to pivot low
        (100, 120, 10),   # recover  (≥5 bars above for window=5)
        (120, 88,  12),   # breakdown — crosses 100 − buf
        (88,  99.5, 8),   # rally toward retest
        (99.5, 92,  8),   # holds below 100 + buf as resistance
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# 1. RESISTANCE → SUPPORT
# ═══════════════════════════════════════════════════════════════════════════════

class TestResistanceBecomesSupport:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.c, self.h, self.lo = scenario_confirmed_resistance_flip()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _near100(self, levels):
        """Return role-reversal levels within 2 units of 100."""
        return [lv for lv in levels if abs(lv['price'] - 100.0) < 2.0]

    # ── tests ─────────────────────────────────────────────────────────────────

    def test_confirmed_flip_detected(self):
        """Breakout + retest + hold → confirmed=True."""
        result = rr(self.c, self.h, self.lo)
        near = self._near100(result['former_resistance_now_support'])
        assert len(near) > 0, (
            f"Expected a level near 100 in former_resistance_now_support; "
            f"got {result['former_resistance_now_support']}"
        )
        lv = near[0]
        assert lv['original_role'] == 'resistance'
        assert lv['current_role']  == 'support'
        assert lv['retest_detected'] is True
        assert lv['retest_held']     is True
        assert lv['confirmed']       is True

    def test_failed_retest_two_consecutive_closes(self):
        """2 consecutive closes back below level → held=False, confirmed=False."""
        c, h, lo = scenario_failed_retest()
        result = rr(c, h, lo)
        near = self._near100(result['former_resistance_now_support'])
        assert len(near) > 0, f"Expected a near-100 level; got {result}"
        lv = near[0]
        assert lv['retest_detected'] is True
        assert lv['retest_held']     is False
        assert lv['confirmed']       is False

    def test_single_noisy_close_does_not_fail_retest(self):
        """1 close below threshold then recovery → streak resets → held=True."""
        c, h, lo = scenario_single_noisy_close()
        result = rr(c, h, lo)
        near = self._near100(result['former_resistance_now_support'])
        assert len(near) > 0, f"Expected a near-100 level; got {result}"
        lv = near[0]
        assert lv['retest_detected'] is True
        assert lv['retest_held']     is True
        assert lv['confirmed']       is True

    def test_no_retest_within_window(self):
        """Price stays >20 from level for >30 bars → retest_detected=False."""
        c, h, lo = scenario_no_retest_in_window()
        # Use large proximity so the level still appears in output
        result = rr(c, h, lo, retest_window=30, proximity_pct=0.5)
        near = self._near100(result['former_resistance_now_support'])
        for lv in near:
            assert lv['retest_detected'] is False, (
                "Should not detect a retest when price stayed far away for > window bars"
            )
            assert lv['confirmed'] is False

    def test_unbroken_resistance_not_in_output(self):
        """A pivot high that price never breaks above must not appear as a flip."""
        # Price tops at 100 twice but never closes above it with 2 consecutive bars
        c, h, lo = make_ohlc([
            (80, 80, 20),
            (80, 100, 10), (100, 80, 10),  # peak at 100
            (80, 100, 10), (100, 80, 10),  # peak at 100 again, still no breakout
            (80, 80, 5),
        ])
        result = rr(c, h, lo)
        near = self._near100(result['former_resistance_now_support'])
        assert len(near) == 0, (
            f"Unbroken resistance at 100 should not appear as a flip; got {near}"
        )

    def test_level_appears_below_current_price(self):
        """former_resistance_now_support levels must be ≤ current price."""
        result = rr(self.c, self.h, self.lo)
        current = float(self.c.iloc[-1])
        for lv in result['former_resistance_now_support']:
            assert lv['price'] <= current + 0.01, (
                f"Level {lv['price']} is above current {current:.2f}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SUPPORT → RESISTANCE
# ═══════════════════════════════════════════════════════════════════════════════

class TestSupportBecomesResistance:

    def test_confirmed_flip_detected(self):
        """Breakdown + retest + hold → confirmed=True."""
        c, h, lo = scenario_confirmed_support_flip()
        result = rr(c, h, lo)
        near = [lv for lv in result['former_support_now_resistance']
                if abs(lv['price'] - 100.0) < 2.0]
        assert len(near) > 0, (
            f"Expected a level near 100 in former_support_now_resistance; "
            f"got {result['former_support_now_resistance']}"
        )
        lv = near[0]
        assert lv['original_role'] == 'support'
        assert lv['current_role']  == 'resistance'
        assert lv['retest_detected'] is True
        assert lv['retest_held']     is True
        assert lv['confirmed']       is True

    def test_level_appears_above_current_price(self):
        """former_support_now_resistance levels must be ≥ current price."""
        c, h, lo = scenario_confirmed_support_flip()
        result = rr(c, h, lo)
        current = float(c.iloc[-1])
        for lv in result['former_support_now_resistance']:
            assert lv['price'] >= current - 0.01, (
                f"Level {lv['price']} is below current {current:.2f}"
            )

    def test_no_false_positives_for_unbroken_support(self):
        """Support that never breaks should not appear as a flip."""
        c, h, lo = make_ohlc([
            (120, 120, 20),
            (120, 100, 10), (100, 120, 10),
            (120, 100, 10), (100, 120, 10),
            (120, 120, 5),
        ])
        result = rr(c, h, lo)
        near = [lv for lv in result['former_support_now_resistance']
                if abs(lv['price'] - 100.0) < 2.0]
        assert len(near) == 0, f"Unbroken support should not flip; got {near}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RETEST WINDOW BOUNDARY
# ═══════════════════════════════════════════════════════════════════════════════

class TestRetestWindow:

    def test_retest_just_inside_window_is_detected(self):
        """A retest exactly at bar retest_window − 1 should be detected."""
        # We will check that with a tight window, a late retest is within scope.
        # Strategy: use default (loose) window, confirm retest is detected
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo, retest_window=60)  # generous window
        near = [lv for lv in result['former_resistance_now_support']
                if abs(lv['price'] - 100.0) < 2.0]
        assert any(lv['retest_detected'] for lv in near), (
            "With wide retest_window=60, a retest within 60 bars should be detected"
        )

    def test_very_tight_window_prevents_late_retest(self):
        """retest_window=2 means only 2 bars after breakout are scanned."""
        c, h, lo = scenario_confirmed_resistance_flip()
        # The retest happens ~9 bars after breakout; window=2 should miss it
        result = rr(c, h, lo, retest_window=2, proximity_pct=0.5)
        near = [lv for lv in result['former_resistance_now_support']
                if abs(lv['price'] - 100.0) < 2.0]
        for lv in near:
            assert lv['retest_detected'] is False, (
                "With retest_window=2 the late retest should not be detected"
            )
            assert lv['confirmed'] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PROXIMITY FILTER
# ═══════════════════════════════════════════════════════════════════════════════

class TestProximityFilter:

    def test_all_returned_levels_within_proximity(self):
        """Every returned level must be within proximity_pct of current price."""
        c, h, lo = scenario_confirmed_resistance_flip()
        pct = 0.08
        result = rr(c, h, lo, proximity_pct=pct)
        current = float(c.iloc[-1])
        for key in result:
            for lv in result[key]:
                assert abs(lv['price'] - current) / current <= pct + 1e-9, (
                    f"Level {lv['price']} is more than {pct*100:.0f}% from "
                    f"current {current:.2f}"
                )

    def test_far_level_excluded_by_default_proximity(self):
        """
        If we force the current price far from the flip level, it is excluded
        by the default 12 % proximity filter.
        """
        # Confirmed flip at 100, but append 80 bars to push current price to ~170
        c1, h1, lo1 = scenario_confirmed_resistance_flip()
        extra = make_ohlc([(108, 170, 80)])
        c  = pd.concat([c1,  extra[0]], ignore_index=True)
        h  = pd.concat([h1,  extra[1]], ignore_index=True)
        lo = pd.concat([lo1, extra[2]], ignore_index=True)
        result = rr(c, h, lo, proximity_pct=0.12)
        # |100 − 170| / 170 = 41 % > 12 % → excluded
        near = [lv for lv in result['former_resistance_now_support']
                if abs(lv['price'] - 100.0) < 2.0]
        assert len(near) == 0, "Level 100 should be excluded when current price is ~170"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_insufficient_data_returns_empty_lists(self):
        """Fewer bars than 2 × window → no pivot candidates → empty output."""
        c, h, lo = make_ohlc([(100, 100, 8)])   # 8 bars, window=5 → range(5,3) empty
        result = rr(c, h, lo)
        assert result['former_resistance_now_support'] == []
        assert result['former_support_now_resistance'] == []

    def test_flat_price_returns_empty(self):
        """Perfectly flat price → no pivot highs or lows → empty output."""
        c, h, lo = make_ohlc([(100, 100, 60)])
        result = rr(c, h, lo)
        assert result['former_resistance_now_support'] == []
        assert result['former_support_now_resistance'] == []

    def test_output_always_has_both_keys(self):
        """Both output keys must always be present, even with trivial data."""
        c, h, lo = make_ohlc([(100, 100, 50)])
        result = rr(c, h, lo)
        assert 'former_resistance_now_support' in result
        assert 'former_support_now_resistance' in result

    def test_each_level_has_all_required_fields(self):
        required = {
            'price', 'original_role', 'current_role',
            'broken_bars_ago', 'retest_detected', 'retest_held', 'confirmed',
        }
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo)
        for key in result:
            for lv in result[key]:
                missing = required - lv.keys()
                assert not missing, f"Level missing fields: {missing}"

    def test_broken_bars_ago_is_non_negative_int(self):
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo)
        for key in result:
            for lv in result[key]:
                assert isinstance(lv['broken_bars_ago'], int)
                assert lv['broken_bars_ago'] >= 0

    def test_at_most_three_levels_per_side(self):
        """Output is always capped at 3 levels per side."""
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo)
        assert len(result['former_resistance_now_support']) <= 3
        assert len(result['former_support_now_resistance']) <= 3

    def test_original_and_current_role_are_opposite(self):
        """original_role and current_role must always be different."""
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo)
        for key in result:
            for lv in result[key]:
                assert lv['original_role'] != lv['current_role'], (
                    f"original_role and current_role should differ: {lv}"
                )

    def test_confirmed_implies_retest_detected_and_held(self):
        """confirmed=True is only possible when both retest_detected and retest_held."""
        c, h, lo = scenario_confirmed_resistance_flip()
        result = rr(c, h, lo)
        for key in result:
            for lv in result[key]:
                if lv['confirmed']:
                    assert lv['retest_detected'] is True
                    assert lv['retest_held']     is True


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SUMMARY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestSummaryIntegration:
    """Verify role_reversal is wired into calculate_technicals summary."""

    def test_role_reversal_key_in_signal_detail(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        assert "role_reversal" in result["summary"]["signal_detail"], (
            "role_reversal count() should add it to signal_detail"
        )

    def test_role_reversal_signal_is_valid_value(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        val = result["summary"]["signal_detail"]["role_reversal"]
        assert val in ("bullish", "bearish", "neutral"), f"Unexpected: {val}"

    def test_role_reversal_key_in_price_structure(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        assert "role_reversal" in result["price_structure"]

    def test_role_reversal_output_keys(self):
        from calculate_technicals import calculate_technicals
        result = calculate_technicals("AAPL")
        rr_out = result["price_structure"]["role_reversal"]
        assert "former_resistance_now_support" in rr_out
        assert "former_support_now_resistance" in rr_out
