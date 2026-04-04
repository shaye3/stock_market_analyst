# calculate_technicals.py — Technical Analysis Tool

Fetches OHLCV price history for any stock ticker and computes a comprehensive
set of technical indicators, outputting a structured JSON report designed for
buy/sell timing decisions.

---

## Dependencies

| Package | Role |
|---|---|
| `yfinance` | OHLCV data source |
| `pandas` | Series computation |
| `numpy` | Math helpers |
| `ta` *(optional)* | Preferred indicator library; all indicators fall back to manual implementations if unavailable |

---

## Usage

### CLI
```bash
python tools/calculate_technicals.py AAPL
python tools/calculate_technicals.py NVDA --period 2y
python tools/calculate_technicals.py MSFT --period 6mo
```

**Arguments**

| Argument | Default | Description |
|---|---|---|
| `ticker` | *(required)* | Stock ticker symbol (case-insensitive) |
| `--period` | `1y` | History window: `1y`, `2y`, `6mo`, `3mo`, etc. |

### Python API
```python
from tools.calculate_technicals import calculate_technicals

result = calculate_technicals("AAPL", period="1y")
# result is a plain dict — serialize or pass directly to analysis agents
```

---

## Output Structure

The function returns a single `dict` with seven top-level sections:

```
{
  "ticker":          "AAPL",
  "period":          "1y",
  "data_points":     252,
  "trend":           { ... },
  "momentum":        { ... },
  "volatility":      { ... },
  "volume":          { ... },
  "fibonacci":       { ... },      ← swing-anchored Fibonacci retracement + entry signal
  "price_structure": { ... },
  "summary":         { ... }
}
```

---

## Section Reference

### `trend`

Moving averages, directional indicators, and SMA-derived trend signals.

| Field | Type | Description |
|---|---|---|
| `sma_20` | float | 20-day Simple Moving Average |
| `sma_50` | float | 50-day Simple Moving Average |
| `sma_200` | float | 200-day Simple Moving Average |
| `ema_12` | float | 12-day Exponential Moving Average |
| `ema_26` | float | 26-day Exponential Moving Average |
| `ema_50` | float | 50-day Exponential Moving Average |
| `price_vs_sma20` | float | % deviation of current price from SMA20 |
| `price_vs_sma50` | float | % deviation of current price from SMA50 |
| `price_vs_sma200` | float | % deviation of current price from SMA200 |
| `golden_cross_date` | str \| null | Date of most recent SMA50 × SMA200 bullish crossover (within last 20 bars) |
| `golden_cross_bars_ago` | int \| null | Trading days since the golden cross |
| `death_cross_date` | str \| null | Date of most recent SMA50 × SMA200 bearish crossover (within last 20 bars) |
| `death_cross_bars_ago` | int \| null | Trading days since the death cross |
| `trend_signal` | str | Velocity-aware trend classification (see **Trend Signal Taxonomy** below) |
| `adx_14` | float | ADX(14) — trend strength (0–100) |
| `adx_pos_di` | float | +DI: bullish directional movement |
| `adx_neg_di` | float | −DI: bearish directional movement |
| `trend_strength` | str | ADX regime: `strong_trending` / `weak_trending` / `ranging` / `unknown` |
| `adx_di_signal` | str | `bullish` (+DI > −DI) or `bearish` (+DI < −DI) |
| `parabolic_sar` | float \| null | Current Parabolic SAR price level |
| `parabolic_sar_signal` | str | `bullish` (price > SAR) / `bearish` (price < SAR) / `unavailable` |
| `sma20_last5` | float[] | Last 5 SMA20 values (oldest → newest) |
| `sma50_last5` | float[] | Last 5 SMA50 values |
| `sma200_last5` | float[] | Last 5 SMA200 values |

#### Trend Signal Taxonomy

The `trend_signal` field uses both current MA levels **and** 5-bar MA slopes to classify
the market regime. Signals are ordered from most bullish to most bearish:

| Signal | Meaning | Trading Implication |
|---|---|---|
| `strong_uptrend` | price > SMA20 > SMA50 > SMA200, all MAs rising | Hold / add to longs |
| `strong_uptrend_losing_momentum` | Same perfect stack, but SMA20 already falling | Consider partial exit / tighten stops |
| `uptrend` | price > SMA50 > SMA200 | Bullish bias, look for entries on pullbacks |
| `pullback_in_uptrend` | price < SMA50, MAs still rising, SMA50 > SMA200 | Potential buy zone — dip in intact uptrend |
| `pullback_weakening` | price < SMA50, MAs declining, SMA50 > SMA200 | Avoid new longs — dip-buying is risky |
| `death_cross_forming` | SMA20 within 0.5% of SMA50, both falling fast | Bearish warning — exit or hedge |
| `topping` | SMA20 crossed below SMA50, both declining, SMA50 > SMA200 | Distribution phase — reduce exposure |
| `developing_downtrend` | Price broke below SMA200, SMA50 still above it | Early-stage trend change — avoid longs |
| `downtrend` | price < SMA50 < SMA200 | Bearish bias |
| `strong_downtrend` | price < SMA20 < SMA50 < SMA200 | Short / stay flat |
| `consolidation` | Price within ±3% of SMA20, MAs flat | Wait for breakout direction |
| `mixed` | No clear pattern | Insufficient data / unusual configuration |

#### ADX Interpretation

| ADX Value | Meaning |
|---|---|
| < 20 | Market is ranging / choppy — trend signals are unreliable |
| 20–25 | Weak trend developing |
| > 25 | Trend is strong — follow trend-based signals |
| > 40 | Very strong trend — momentum may be exhausting |

---

### `momentum`

Oscillators and crossover signals for timing entries and exits.

| Field | Type | Description |
|---|---|---|
| `rsi_14` | float | RSI(14) value (0–100) |
| `rsi_signal` | str | `overbought` (>70) / `oversold` (<30) / `neutral` |
| `rsi_last5` | float[] | Last 5 RSI values |
| `rsi_divergence` | str | Divergence signal vs price (see **Divergence Values**) |
| `rsi_divergence_detail` | dict | Full divergence breakdown with boolean flags |
| `macd_line` | float | MACD line (EMA12 − EMA26) |
| `macd_signal` | float | MACD signal line (9-bar EMA of MACD line) |
| `macd_histogram` | float | MACD histogram (line − signal) |
| `macd_crossover_state` | str | Current state: `bullish` (line > signal) or `bearish` |
| `macd_crossover_event` | dict | `{type, bars_ago}` — most recent crossover within last 10 bars |
| `macd_fresh_crossover` | bool | `true` if a crossover occurred within the last 5 bars |
| `macd_hist_last5` | float[] | Last 5 histogram values (growing = strengthening momentum) |
| `macd_divergence` | str | Divergence signal vs price |
| `macd_divergence_detail` | dict | Full divergence breakdown |
| `stoch_k` | float \| null | Stochastic %K (requires `ta` library) |
| `stoch_d` | float \| null | Stochastic %D signal line |
| `stoch_signal` | str | `overbought` (>80) / `oversold` (<20) / `neutral` |
| `mfi_14` | float | Money Flow Index(14) — volume-weighted RSI (0–100) |
| `mfi_signal` | str | `overbought` (>80) / `oversold` (<20) / `neutral` |

#### Divergence Values

Applies to both `rsi_divergence` and `macd_divergence`:

| Value | Condition | Implication |
|---|---|---|
| `regular_bullish` | Price lower low + indicator higher low | Reversal up — strong buy signal |
| `regular_bearish` | Price higher high + indicator lower high | Reversal down — strong sell signal |
| `hidden_bullish` | Price higher low + indicator lower low | Uptrend continuation |
| `hidden_bearish` | Price lower high + indicator higher high | Downtrend continuation |
| `none` | No divergence detected in the last 60 bars | No divergence signal |

#### MACD Crossover Event

```json
"macd_crossover_event": {
  "type": "bearish",   // "bullish" | "bearish" | "none"
  "bars_ago": 10       // trading days since the crossover; null if "none"
}
```

Fresh crossovers (`bars_ago` ≤ 5) carry **2× weight** in the summary score.

---

### `volatility`

Measures of price range and deviation to assess risk and identify extremes.

| Field | Type | Description |
|---|---|---|
| `bollinger_upper` | float | Upper Bollinger Band (SMA20 + 2σ) |
| `bollinger_mid` | float | Middle band (SMA20) |
| `bollinger_lower` | float | Lower Bollinger Band (SMA20 − 2σ) |
| `bollinger_width` | float | Band width as % of middle band — proxy for volatility expansion/contraction |
| `price_vs_bb` | str | `above_upper` / `below_lower` / `within_bands` |
| `atr_14` | float | Average True Range(14) — average daily price range in dollars |
| `atr_pct_of_price` | float | ATR as % of current price — normalized volatility |
| `hist_volatility_30d` | float | Annualized historical volatility over last 30 days (%) |

**Bollinger Band signals used in scoring:**
- `below_lower` → bullish (price at statistical low, potential mean-reversion buy)
- `above_upper` → bearish (price at statistical high, potential mean-reversion sell)

---

### `volume`

Measures of buying/selling pressure and institutional participation.

| Field | Type | Description |
|---|---|---|
| `current_volume` | int | Most recent session volume |
| `avg_volume_20d` | int | 20-day average volume |
| `avg_volume_50d` | int | 50-day average volume |
| `volume_ratio_vs_avg` | float | Current / 20d avg (>1.5 = high conviction move) |
| `volume_trend` | str | `increasing` (20d avg > 50d avg) or `decreasing` |
| `obv_current` | float | On-Balance Volume — cumulative volume flow |
| `obv_trend` | str | `bullish` (OBV > 20-day OBV mean) or `bearish` |
| `volume_last5` | int[] | Raw volume for the last 5 sessions |

---

### `fibonacci`

Swing-anchored Fibonacci retracement and extension analysis with a full entry signal system.

> **Important distinction from `price_structure.fibonacci_levels`:**
> `price_structure.fibonacci_levels` contains *static* levels anchored to the 52-week high/low.
> The `fibonacci` section here uses *dynamic* swing pivots detected from recent price action,
> producing levels that adapt as the market moves and explicitly identifying entry setups.

#### How it works — five-stage pipeline

**Stage 1 — Swing pivot detection**

Scans the last `lookback=90` bars of the high and low series for local pivot points using a symmetric `window=5` neighborhood check:
- Swing high at bar `i`: `high[i]` ≥ all `high[i±j]` for `j` in 1..5
- Swing low at bar `i`: `low[i]` ≤ all `low[i±j]` for `j` in 1..5

At least one swing high and one swing low must be found; otherwise the function returns `{"error": "insufficient_pivot_data"}`.

**Stage 2 — Anchor pair selection**

Takes the most recent swing high and most recent swing low detected in the lookback window. Enforces `max_anchor_gap=60`: the two pivots must be within 60 bars of each other. If the gap is too wide, the function walks backward through the shorter list to find a valid pair. If none exists, it returns `{"error": "no_valid_anchor_pair"}`.

**Stage 3 — Direction and level computation**

Compares the bar index of the chosen swing high against the swing low to determine which move just happened:

| Condition | `anchor_direction` | `move_start` | `move_end` | Interpretation |
|---|---|---|---|---|
| `swing_high_idx > swing_low_idx` | `"uptrend"` | swing low | swing high | Last move was UP; price is now pulling back |
| `swing_low_idx > swing_high_idx` | `"downtrend"` | swing high | swing low | Last move was DOWN; price is now bouncing |

`move_size = abs(swing_high − swing_low)`

**Retracement levels** — measured from `move_end` back toward `move_start`:

| Key | Ratio | Uptrend price | Downtrend price |
|---|---|---|---|
| `fib_0` | 0% | = swing_high (top of move) | = swing_low (bottom of move) |
| `fib_236` | 23.6% | swing_high − 0.236 × size | swing_low + 0.236 × size |
| `fib_382` | 38.2% | swing_high − 0.382 × size | swing_low + 0.382 × size |
| `fib_500` | 50.0% | swing_high − 0.500 × size | swing_low + 0.500 × size |
| `fib_618` | 61.8% | swing_high − 0.618 × size | swing_low + 0.618 × size |
| `fib_786` | 78.6% | swing_high − 0.786 × size | swing_low + 0.786 × size |
| `fib_100` | 100% | = swing_low (base of move) | = swing_high (peak of move) |

**Extension levels** — projected beyond `move_end` to identify profit targets:

| Key | Ratio | Uptrend (above swing_high) | Downtrend (below swing_low) |
|---|---|---|---|
| `fib_1272` | 127.2% | swing_high + 0.272 × size | swing_low − 0.272 × size |
| `fib_1618` | 161.8% | swing_high + 0.618 × size | swing_low − 0.618 × size |

> **Level ordering:**
> - Uptrend: `fib_0` (highest) > `fib_236` > … > `fib_100` (lowest). Extensions are above `fib_0`.
> - Downtrend: `fib_0` (lowest) < `fib_236` < … < `fib_100` (highest). Extensions are below `fib_0`.

**Stage 4 — MA confluence detection**

For every Fibonacci level (both retracement and extension), checks whether any of SMA20, SMA50, or SMA200 falls within `confluence_tol=1%`. Matching pairs are reported as strings like `"fib_618_near_sma50"`.

The flag `has_confluence_at_golden_ratio` is `true` when the 61.8% level specifically is within 1% of at least one key MA. This is the highest-conviction setup because two independent analytical frameworks (Fibonacci and moving averages) are pointing to the same price zone simultaneously.

**Stage 5 — Entry signal generation**

A signal fires only when **all four conditions** are met simultaneously:

| Condition | Bullish (uptrend pullback) | Bearish (downtrend bounce) |
|---|---|---|
| Anchor direction | `anchor_direction == "uptrend"` | `anchor_direction == "downtrend"` |
| Price at level | Current price within 1.5% of any retracement level | Same |
| RSI gate | `RSI < 45` (momentum not yet overbought on pullback) | `RSI > 55` (momentum not yet oversold on bounce) |
| Volume confirmation | Current volume ≥ 85% of 20-day average | Same |

`entry_conditions` always reports each boolean individually so partial setups are transparent.

**Stop-loss placement**

Placed at the next Fibonacci level in the *adverse* direction:

| Setup | Entry level | Stop level |
|---|---|---|
| Bullish entry (long) | `fib_618` retracement | `fib_786` — if price breaks deeper, the pullback thesis is invalidated |
| Bearish entry (short) | `fib_618` bounce | `fib_786` — if price rallies further, the bounce-short thesis is invalidated |

In the swing-anchored model, "adverse" always means the next level at a *higher index* in `retrace_keys` because that represents the next structural level the trade must not breach.

**Staleness** — `bars_since_anchor` counts bars elapsed since `move_end` (the most recent pivot). Signals where `bars_since_anchor > 20` are increasingly stale; the setup has had significant time for conditions to change.

#### Output fields

| Field | Type | Description |
|---|---|---|
| `anchor_direction` | str | `"uptrend"` or `"downtrend"` |
| `swing_high` | float | Price of the detected swing high pivot (intrabar high) |
| `swing_high_bars_ago` | int | Bars ago the swing high occurred (from end of full series) |
| `swing_low` | float | Price of the detected swing low pivot (intrabar low) |
| `swing_low_bars_ago` | int | Bars ago the swing low occurred |
| `bars_since_anchor` | int | Bars elapsed since `move_end` (more recent of the two pivots) |
| `retracement_levels` | dict | All 7 Fibonacci retracement levels (keys: `fib_0` … `fib_100`) |
| `extension_levels` | dict | Two extension levels (keys: `fib_1272`, `fib_1618`) |
| `current_price` | float | Most recent closing price |
| `nearest_retracement` | str | Key of the closest retracement level to current price |
| `nearest_retracement_price` | float | Price of that closest level |
| `nearest_retracement_pct_dist` | float | % distance from current price to nearest level |
| `at_fib_levels` | str[] | List of all retracement level keys where price is within 1.5% |
| `at_golden_ratio` | bool | `true` if price is within 1.5% of `fib_618` specifically |
| `has_confluence_at_golden_ratio` | bool | `true` if `fib_618` is within 1% of SMA20, SMA50, or SMA200 — highest-conviction setup flag |
| `confluence_levels` | str[] | All Fib+MA proximity pairs (e.g. `["fib_618_near_sma50"]`) |
| `entry_signal` | str | `"bullish_entry"` / `"bearish_entry"` / `"none"` |
| `entry_conditions` | dict | Per-condition boolean breakdown (4 conditions, see Stage 5) |
| `stop_loss_level` | float \| null | Stop-loss price (next adverse Fib level); `null` when no entry |
| `target_1_swing_end` | float | First target — return to `move_end` (the swing pivot that started the current move) |
| `target_2_ext_1272` | float | Second target — 127.2% extension beyond `move_end` |
| `target_3_ext_1618` | float | Third target — 161.8% extension beyond `move_end` |

#### Error cases

| Error key | Cause |
|---|---|
| `"insufficient_pivot_data"` | No swing high or no swing low found in the last 90 bars |
| `"no_valid_anchor_pair"` | Swing high and swing low found, but the closest pair is more than `max_anchor_gap=60` bars apart |
| `"degenerate_swing"` | `swing_high == swing_low` (zero-size move — degenerate data) |

In all error cases, `entry_signal` is `"none"` and no trade levels are returned.

#### Example output (uptrend pullback)

```json
{
  "anchor_direction": "uptrend",
  "swing_high": 203.0,
  "swing_high_bars_ago": 29,
  "swing_low": 98.5,
  "swing_low_bars_ago": 69,
  "bars_since_anchor": 29,
  "retracement_levels": {
    "fib_0":   203.0,
    "fib_236": 178.22,
    "fib_382": 163.57,
    "fib_500": 150.75,
    "fib_618": 137.93,
    "fib_786": 118.54,
    "fib_100": 98.5
  },
  "extension_levels": {
    "fib_1272": 231.47,
    "fib_1618": 265.32
  },
  "current_price": 138.2,
  "nearest_retracement": "fib_618",
  "nearest_retracement_price": 137.93,
  "nearest_retracement_pct_dist": 0.19,
  "at_fib_levels": ["fib_618"],
  "at_golden_ratio": true,
  "has_confluence_at_golden_ratio": true,
  "confluence_levels": ["fib_618_near_sma50"],
  "entry_signal": "bullish_entry",
  "entry_conditions": {
    "uptrend_anchor": true,
    "price_at_level": true,
    "rsi_below_threshold": true,
    "volume_confirmed": true
  },
  "stop_loss_level": 118.54,
  "target_1_swing_end": 203.0,
  "target_2_ext_1272": 231.47,
  "target_3_ext_1618": 265.32
}
```

---

### `price_structure`

Key price levels and Fibonacci retracements anchored to the 52-week range.

| Field | Type | Description |
|---|---|---|
| `52w_high` | float | 52-week high |
| `52w_low` | float | 52-week low |
| `current_price` | float | Most recent closing price |
| `pct_from_52w_high` | float | % below the 52-week high (negative = below) |
| `pct_from_52w_low` | float | % above the 52-week low |
| `key_resistance` | float[] | Up to 3 clustered pivot resistance levels (last 90 days); levels that have flipped roles (see `role_reversal`) are deduplicated out |
| `key_support` | float[] | Up to 3 clustered pivot support levels (last 90 days); levels that have flipped roles are deduplicated out |
| `fibonacci_levels` | dict | Static retracement levels anchored to 52-week range (see below) |
| `nearest_fib_level` | str | Key name of the closest Fibonacci level to current price |
| `nearest_fib_price` | float | Price of the closest Fibonacci level |
| `nearest_fib_pct_distance` | float | % distance from current price to nearest fib level |
| `role_reversal` | dict | Polarity-flip levels detected by `detect_role_reversal_levels` (see below) |

#### `role_reversal`

Captures the **polarity-flip principle**: a resistance level that has been decisively broken and then retested from above becomes new support (and vice versa for broken support levels). This is one of the highest-conviction structural signals in classical technical analysis.

```json
"role_reversal": {
  "former_resistance_now_support": [
    {
      "price": 182.40,
      "broken_bars_ago": 12,
      "retest_detected": true,
      "retest_held": true,
      "confirmed": true
    }
  ],
  "former_support_now_resistance": [
    {
      "price": 175.10,
      "broken_bars_ago": 8,
      "retest_detected": true,
      "retest_held": true,
      "confirmed": true
    }
  ]
}
```

**Per-level fields:**

| Field | Type | Description |
|---|---|---|
| `price` | float | Price of the flipped pivot level |
| `broken_bars_ago` | int | Trading bars since the breakout was confirmed |
| `retest_detected` | bool | `true` if price returned to within proximity of the level after the breakout |
| `retest_held` | bool | `true` if the retest closed away from the level (confirming the flip held) |
| `confirmed` | bool | `true` only when `retest_detected=true` AND `retest_held=true` — both conditions must be met |

**Deduplication:** Any level appearing in `role_reversal` (within 0.5% tolerance) is automatically removed from `key_resistance` and `key_support` to avoid double-counting the same price zone with conflicting labels.

#### Fibonacci Levels (static, 52-week anchored)

> These are different from the swing-anchored levels in the `fibonacci` section.
> They give a structural view of where the stock sits relative to its full yearly range,
> not a trade-specific entry signal.

Computed as retracements from the 52-week high down to the 52-week low:

| Key | Retracement | Significance |
|---|---|---|
| `fib_0` | 0% (52w high) | Major resistance |
| `fib_236` | 23.6% | Shallow pullback support |
| `fib_382` | 38.2% | Common pullback support |
| `fib_500` | 50.0% | Psychological midpoint |
| `fib_618` | 61.8% | Golden ratio — strongest support/resistance |
| `fib_786` | 78.6% | Deep retracement |
| `fib_100` | 100% (52w low) | Major support |

---

### `summary`

Composite buy/sell score synthesized from all indicator sections.

| Field | Type | Description |
|---|---|---|
| `bullish_signals` | int | Weighted count of bullish signals fired |
| `bearish_signals` | int | Weighted count of bearish signals fired |
| `neutral_signals` | int | Weighted count of neutral (no direction) signals |
| `total_signals` | int | Total weighted signal count |
| `technical_score` | float | `bullish / total` — 0.0 (fully bearish) to 1.0 (fully bullish) |
| `overall_signal` | str | Final verdict (see **Overall Signal Thresholds**) |
| `timing_assessment` | str | Entry timing verdict |
| `trend_quality` | str | ADX regime (`strong_trending` / `weak_trending` / `ranging`) |
| `signal_detail` | dict | Per-indicator direction for transparency |

#### Overall Signal Thresholds

| Score | `overall_signal` | `timing_assessment` |
|---|---|---|
| ≥ 0.80 | `strong_buy` | `favorable_entry` |
| ≥ 0.60 | `buy` | `favorable_entry` |
| 0.41–0.59 | `neutral` | `wait_for_clarity` |
| ≤ 0.40 | `avoid` | `unfavorable_entry` |
| ≤ 0.20 | `sell` | `unfavorable_entry` |

#### Scoring Methodology

Twelve named signals are evaluated; some carry extra weight:

| Signal | Weight | Bullish Condition | Bearish Condition |
|---|---|---|---|
| `sma_trend` | 1× | ADX-gated: trend in (`strong_uptrend`, `uptrend`, `pullback_in_uptrend`) | Any of: `strong_downtrend`, `downtrend`, `death_cross_forming`, `topping`, `developing_downtrend`, `pullback_weakening` |
| `adx_di` | 1× | +DI > −DI | +DI < −DI |
| `parabolic_sar` | 1× | Price > SAR | Price < SAR |
| `rsi` | 1× | RSI < 30 AND not in downtrend | RSI > 70 AND not in uptrend |
| `macd_crossover` | **1–2×** | Bullish crossover in last 10 bars | Bearish crossover in last 10 bars |
| `rsi_divergence` | **2×** | Regular bullish divergence | Regular bearish divergence |
| `macd_divergence` | **2×** | Regular bullish divergence | Regular bearish divergence |
| `mfi` | 1× | MFI < 20 AND not in downtrend | MFI > 80 AND not in uptrend |
| `obv_trend` | 1× | OBV above 20-day OBV mean | OBV below 20-day OBV mean |
| `bollinger` | 1× | Price below lower band | Price above upper band |
| `fibonacci_entry` | **1–2×** | `entry_signal == "bullish_entry"` | `entry_signal == "bearish_entry"` |
| `role_reversal` | **2×** | Any `confirmed=true` level in `former_resistance_now_support` | Any `confirmed=true` level in `former_support_now_resistance` |

**Weight escalation for `fibonacci_entry`:**
- **2×** when `has_confluence_at_golden_ratio == true` — 61.8% level aligns with a key MA. Two independent frameworks (Fibonacci + moving average) pointing to the same price zone is a highest-conviction setup.
- **1×** for any other Fibonacci entry (price at level + RSI + volume confirmed, but no MA confluence).

**Key design decisions:**
- **ADX gate on uptrend signals** — `sma_trend` bullish signals are suppressed when ADX < 20 (ranging market). False uptrend signals in choppy conditions are a common source of losses.
- **No ADX gate on bearish reversal signals** — `death_cross_forming`, `topping`, etc. are always counted regardless of ADX, because a breakdown is a breakdown.
- **Trend-aligned RSI and MFI** — oversold RSI in a confirmed downtrend is not a buy signal; it is ignored. This prevents premature "value" entries in falling stocks.
- **Fresh MACD crossover bonus** — crossovers within the last 5 bars receive 2× weight. A crossover from 10 bars ago is stale; a fresh one is actionable.
- **Divergence double weight** — RSI and MACD divergence are among the most reliable reversal signals in classical TA and are weighted accordingly.
- **Fibonacci golden-ratio + confluence double weight** — a price sitting at the 61.8% retracement while a key moving average also passes through that zone creates a multi-framework confluence that institutional traders actively watch. The 2× weight reflects this conviction.
- **Role-reversal double weight** — A confirmed polarity flip (breakout + held retest) is one of the highest-conviction structural signals. A price that broke through resistance and then successfully retested it as support is a textbook institutional accumulation zone; a break below support that held on retest as resistance is an equally strong distribution signal.

---

## Helper Functions

### `safe_float(val)`
Returns a rounded `float` or `None`. Handles `NaN`, `Inf`, and any exception.
All indicator values in the output pass through this function.

### `safe_series_tail(series, n=5)`
Returns the last `n` non-NaN values of a pandas Series as a Python list of `safe_float` values.
Used for the `*_last5` slope context fields.

### `detect_trend(close, sma20, sma50, sma200)`
Velocity-aware trend classifier. Uses both the current values of the three SMAs
and their 5-bar net change (slope) to determine market regime. Returns one of
the 12 signal strings in the taxonomy above.

### `detect_divergence(close, indicator, window=5, lookback=60)`
Scans the last `lookback` bars for local price peaks and troughs (using a
`window`-bar neighborhood check). Compares the last two peaks and last two
troughs against the corresponding indicator values to classify divergence type.

### `detect_recent_crossover(line1, line2, lookback=10)`
Walks backward through the last `lookback` bars to find the most recent bar
where `line1` crossed `line2`. Returns `{type, bars_ago}`.

### `detect_support_resistance(close, window=20)`
Scans the most recent 90 days for pivot highs and lows using rolling max/min.
Clusters nearby levels within a 1% tolerance band and returns the top 3
resistance and support clusters. Also computes all static 52-week Fibonacci
retracement levels.

### `detect_role_reversal_levels(close, high, low, window=10, lookback=252, breakout_closes=2, retest_window=30, proximity_pct=0.12)`

Detects **polarity-flip levels** — price zones where a former resistance has become support (or former support has become resistance) — using a four-step algorithm:

**Step 1 — Pivot Detection**
Scans the most recent `lookback` bars for local highs (pivot resistance candidates) and local lows (pivot support candidates). A bar qualifies as a pivot high if its `high` is the maximum in a symmetric `window`-bar neighborhood; similarly for pivot lows using `low`. This uses the same neighborhood logic as `detect_divergence`.

**Step 2 — Clustering**
Nearby pivots are grouped into clusters using an ATR-adaptive tolerance: pivots within `0.5 × ATR(14)` of each other are merged into a single level (the mean of the cluster). This prevents the same price zone from producing multiple redundant entries.

**Step 3 — Breakout + Retest Detection**
For each clustered pivot level, the algorithm checks whether a confirmed **breakout** has occurred and, if so, whether price has **retested** the level:

*Breakout confirmation* — requires `breakout_closes` **consecutive** closes above the level + half-ATR buffer (for resistance → support flip) or below the level − half-ATR buffer (for support → resistance flip). A single close past the level is not enough; the streak requirement filters out false breakouts from wicks and brief spikes.

*Retest detection* — after the breakout is confirmed, the algorithm searches the next `retest_window` bars for price to return within `proximity_pct %` of the level. This window is bounded (default 30 bars) — retests that occur too long after the breakout are not considered valid polarity flips.

*Held check* — a retest "holds" if price closes back away from the level using the same `breakout_closes` streak logic used for the original breakout. This symmetric definition prevents a single indecisive close from marking a failed retest.

**Step 4 — Proximity Filter**
Up to 3 levels per category are returned. If multiple levels cluster near the current price (within `proximity_pct %`), only the closest one is kept to avoid cluttering output with overlapping zones.

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `close` | — | Closing price Series |
| `high` | — | High price Series |
| `low` | — | Low price Series |
| `window` | `10` | Neighborhood half-width for pivot detection |
| `lookback` | `252` | Maximum bars to scan (~1 trading year) |
| `breakout_closes` | `2` | Consecutive closes required to confirm a breakout or held retest |
| `retest_window` | `30` | Maximum bars after breakout to look for a retest |
| `proximity_pct` | `0.12` | % distance defining "close enough" for retest detection and output deduplication |

**Output:**
```json
{
  "former_resistance_now_support": [ { "price": ..., "broken_bars_ago": ..., "retest_detected": ..., "retest_held": ..., "confirmed": ... } ],
  "former_support_now_resistance": [ { "price": ..., "broken_bars_ago": ..., "retest_detected": ..., "retest_held": ..., "confirmed": ... } ]
}
```
Both lists contain at most 3 levels each, sorted by proximity to current price. `confirmed=true` requires both `retest_detected=true` AND `retest_held=true`.

### `detect_fibonacci_signals(close, high, low, volume, rsi, sma20, sma50, sma200, ...)`

Swing-anchored Fibonacci analysis with entry signal generation. See the full
[`fibonacci` section reference](#fibonacci) above for the complete algorithm
description, parameter table, and output field definitions.

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `close` | — | Closing price Series |
| `high` | — | High price Series |
| `low` | — | Low price Series |
| `volume` | — | Volume Series |
| `rsi` | — | RSI(14) Series (pre-computed) |
| `sma20` | — | 20-day SMA Series |
| `sma50` | — | 50-day SMA Series |
| `sma200` | — | 200-day SMA Series |
| `lookback` | `90` | Bars to scan for swing pivots |
| `window` | `5` | Neighborhood half-width for pivot detection |
| `max_anchor_gap` | `60` | Max bars between swing high and swing low anchors |
| `confluence_tol` | `0.01` | Tolerance (1%) for MA proximity to a Fib level |
| `entry_tol` | `0.015` | Tolerance (1.5%) for "price at level" detection |
| `rsi_bull_threshold` | `45` | RSI must be **below** this for a bullish entry |
| `rsi_bear_threshold` | `55` | RSI must be **above** this for a bearish entry |
| `volume_threshold` | `0.85` | Current volume must be ≥ 85% of 20-day average |

---

## Error Handling

If the ticker is invalid or no data is returned by yfinance:

```json
{ "error": "No data for XYZ" }
```

The `fibonacci` section may independently return an error dict (see error cases above)
without affecting the rest of the output. The summary scoring gracefully handles a missing
or errored `fibonacci` section by treating `entry_signal` as `"none"`.

---

## Notes and Limitations

- **Data source** — yfinance data is adjusted for splits and dividends. Prices reflect
  adjusted close, which may differ from real-time quotes.
- **Minimum data requirements** — SMA200 requires at least 200 bars. For periods
  shorter than 1 year, `sma_200` will be `null` and any condition depending on it
  will resolve to `"mixed"`.
- **Parabolic SAR** — only computed when the `ta` library is installed. Falls back
  to `"unavailable"` otherwise.
- **Stochastic Oscillator** — only computed when the `ta` library is installed.
  Returns `null` fields otherwise.
- **Divergence sensitivity** — the `window=5` parameter for peak/trough detection
  means only local extrema separated by at least 5 bars qualify. Noisy or
  low-volatility stocks may produce fewer detected pivots and thus fewer divergence signals.
- **Fibonacci pivot sensitivity** — the same `window=5` neighborhood check applies.
  Very choppy or mean-reverting stocks may produce too many micro-pivots, causing the
  anchor pair to reflect noise rather than a genuine swing. A larger `window` (e.g. 8–10)
  can be passed to `detect_fibonacci_signals` directly for smoother pivot detection.
- **Swing-anchored vs static Fibonacci** — `fibonacci.retracement_levels` are re-computed
  on every call as the detected swing pivots change. `price_structure.fibonacci_levels`
  always reflects the 52-week range and is stable day-to-day. Both are included because
  they serve different analytical purposes: the swing-anchored levels are trade-specific
  entry tools; the 52-week levels give structural context.
- **This tool provides signals, not recommendations** — all output should be
  interpreted alongside fundamental analysis, sector context, and risk management rules.
