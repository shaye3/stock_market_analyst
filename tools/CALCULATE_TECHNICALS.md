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

The function returns a single `dict` with six top-level sections:

```
{
  "ticker":      "AAPL",
  "period":      "1y",
  "data_points": 252,
  "trend":       { ... },
  "momentum":    { ... },
  "volatility":  { ... },
  "volume":      { ... },
  "price_structure": { ... },
  "summary":     { ... }
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

### `price_structure`

Key price levels and Fibonacci retracements anchored to the 52-week range.

| Field | Type | Description |
|---|---|---|
| `52w_high` | float | 52-week high |
| `52w_low` | float | 52-week low |
| `current_price` | float | Most recent closing price |
| `pct_from_52w_high` | float | % below the 52-week high (negative = below) |
| `pct_from_52w_low` | float | % above the 52-week low |
| `key_resistance` | float[] | Up to 3 clustered pivot resistance levels (last 90 days) |
| `key_support` | float[] | Up to 3 clustered pivot support levels (last 90 days) |
| `fibonacci_levels` | dict | Retracement levels anchored to 52-week range (see below) |
| `nearest_fib_level` | str | Key name of the closest Fibonacci level to current price |
| `nearest_fib_price` | float | Price of the closest Fibonacci level |
| `nearest_fib_pct_distance` | float | % distance from current price to nearest fib level |

#### Fibonacci Levels

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

Ten named signals are evaluated; some carry extra weight:

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

**Key design decisions:**
- **ADX gate on uptrend signals** — `sma_trend` bullish signals are suppressed when ADX < 20 (ranging market). False uptrend signals in choppy conditions are a common source of losses.
- **No ADX gate on bearish reversal signals** — `death_cross_forming`, `topping`, etc. are always counted regardless of ADX, because a breakdown is a breakdown.
- **Trend-aligned RSI and MFI** — oversold RSI in a confirmed downtrend is not a buy signal; it is ignored. This prevents premature "value" entries in falling stocks.
- **Fresh MACD crossover bonus** — crossovers within the last 5 bars receive 2× weight. A crossover from 10 bars ago is stale; a fresh one is actionable.
- **Divergence double weight** — RSI and MACD divergence are among the most reliable reversal signals in classical TA and are weighted accordingly.

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
resistance and support clusters. Also computes all Fibonacci retracement levels.

---

## Error Handling

If the ticker is invalid or no data is returned by yfinance:

```json
{ "error": "No data for XYZ" }
```

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
- **This tool provides signals, not recommendations** — all output should be
  interpreted alongside fundamental analysis, sector context, and risk management rules.
