# Tools — Data Fetching Layer

This folder contains the **4 Python data tools** that form Stage 1 of the analysis pipeline.
They are pure data-fetching scripts: they take a ticker symbol as input, query `yfinance`, and emit a clean JSON object to stdout.

The orchestrator (`.claude/commands/analyze-stock.md`) runs all 4 tools **in parallel** using `Bash` calls, then feeds their JSON output into the analysis agents.

---

## Architecture Overview

```
Orchestrator (analyze-stock.md)
        │
        ├── Bash: python tools/fetch_financials.py AAPL     ─┐
        ├── Bash: python tools/calculate_technicals.py AAPL  ├── Parallel
        ├── Bash: python tools/fetch_news.py AAPL            ├── execution
        └── Bash: python tools/fetch_price_data.py AAPL     ─┘
                          │
                          ▼
           JSON output captured → fed into agents
```

All tools:
- Use `yfinance` as the sole data source
- Print JSON to stdout (agents read from stdout)
- Have graceful error handling — partial data is returned, not a crash
- Can be run standalone from the command line for debugging

---

## Tool Reference

### 1. `fetch_financials.py`

#### Purpose
Fetches all **fundamental financial data** for a stock — the most comprehensive of the four tools. Its output is the primary input for the Fundamental Analysis Agent and supplements the Analyst Sentiment and Macro agents.

#### Usage
```bash
python tools/fetch_financials.py AAPL
python tools/fetch_financials.py MSFT
```

#### What It Does
Calls `yfinance.Ticker(ticker)` and extracts data from two sources:
- `stock.info` — a large dict of current snapshot metrics (valuation, margins, growth, balance sheet)
- `stock.financials`, `stock.balance_sheet`, `stock.cashflow` — annual historical statements (4 years)
- `stock.quarterly_financials`, `stock.quarterly_balance_sheet`, `stock.quarterly_cashflow` — recent quarterly data (3 quarters)

#### Output Schema
```json
{
  "ticker": "AAPL",

  "key_stats": {
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "country": "United States",
    "employees": 150000,
    "market_cap": 3000000000000,
    "enterprise_value": 3100000000000,
    "currency": "USD",
    "exchange": "NMS",
    "website": "https://www.apple.com",
    "business_summary": "Apple Inc. designs, manufactures..."  // truncated at 500 chars
  },

  "valuation": {
    "trailing_pe": 28.5,
    "forward_pe": 25.1,
    "peg_ratio": 2.1,
    "price_to_sales": 7.8,
    "price_to_book": 45.2,
    "ev_to_ebitda": 22.4,
    "ev_to_revenue": 8.1
  },

  "profitability": {
    "gross_margin": 0.4530,
    "operating_margin": 0.2950,
    "net_margin": 0.2530,
    "roe": 1.4720,
    "roa": 0.2240,
    "ebitda": 130000000000,
    "trailing_eps": 6.13,
    "forward_eps": 7.02
  },

  "growth": {
    "revenue_growth_yoy": 0.0420,
    "earnings_growth_yoy": 0.0710,
    "earnings_quarterly_growth": 0.1020,
    "revenue_ttm": 385000000000
  },

  "balance_sheet": {
    "total_cash": 65000000000,
    "total_debt": 108000000000,
    "net_debt": 43000000000,       // total_debt - total_cash
    "debt_to_equity": 151.3,
    "current_ratio": 1.04,
    "quick_ratio": 0.98,
    "book_value_per_share": 4.21
  },

  "cash_flow": {
    "operating_cash_flow": 113000000000,
    "free_cash_flow": 95000000000,
    "capex": 18000000000           // operating_cash_flow - free_cash_flow
  },

  "dividend_shares": {
    "dividend_yield": 0.0053,
    "dividend_rate": 0.96,
    "payout_ratio": 0.1560,
    "shares_outstanding": 15250000000,
    "float_shares": 15220000000,
    "shares_short": 95000000,
    "short_ratio": 1.2,
    "short_percent_of_float": 0.0063
  },

  "analyst_consensus": {
    "target_mean_price": 220.50,
    "target_high_price": 250.00,
    "target_low_price": 165.00,
    "recommendation_key": "buy",
    "number_of_analyst_opinions": 38
  },

  "historical_income_statement": {
    "2024-09-28": { "Total Revenue": 391000000000, "Net Income": 94000000000, ... },
    "2023-09-30": { "Total Revenue": 383000000000, ... },
    "2022-09-24": { ... },
    "2021-09-25": { ... }
  },

  "historical_balance_sheet": { ... },   // same structure, 4 annual periods
  "historical_cash_flow": { ... },       // same structure, 4 annual periods

  "quarterly_income_statement": {
    "2024-12-31": { ... },
    "2024-09-28": { ... },
    "2024-06-29": { ... }
  },

  "quarterly_balance_sheet": { ... },   // 3 recent quarters
  "quarterly_cash_flow": { ... }        // 3 recent quarters
}
```

#### Key Implementation Details
- `safe_float()` and `safe_int()` helper functions handle `None`, `NaN`, and `inf` values without crashing — return `null` in JSON instead
- `df_to_dict()` converts yfinance DataFrames (rows = metrics, cols = dates) to nested dicts, capped at `max_cols` most-recent periods
- `capex` is derived as `operating_cash_flow - free_cash_flow` (yfinance doesn't expose it directly in `info`)
- `business_summary` is truncated at 500 characters to keep context window usage reasonable
- All historical data uses `max_cols=4` for annual, `max_cols=3` for quarterly

#### Agents That Use This Tool
| Agent | Fields Used |
|---|---|
| Fundamental Analysis | All fields — full financial deep dive |
| Analyst Sentiment | `analyst_consensus` — price targets, recommendation key |
| Macro Economy | `key_stats.sector`, `key_stats.industry` |
| Risk Assessment | All fields via Fundamental Agent's output |

---

### 2. `calculate_technicals.py`

#### Purpose
Calculates a comprehensive set of **technical analysis indicators** from price history. This is the most sophisticated tool — approximately 650 lines of Python implementing 10+ indicator families with a custom weighted scoring system.

Designed to give the Technical Analysis Agent pre-computed, structured data rather than raw OHLCV, so the agent can focus on interpretation rather than calculation.

#### Usage
```bash
python tools/calculate_technicals.py AAPL
python tools/calculate_technicals.py MSFT --period 2y
python tools/calculate_technicals.py NVDA --period 6mo
```

#### What It Does
Fetches `stock.history(period=period)` from yfinance and runs the full indicator suite. Has a **dual-path implementation**: if the `ta` library is installed, it uses `ta`'s optimized implementations; if not, it falls back to manual NumPy/pandas implementations of every indicator. This ensures the tool works even in minimal environments.

#### Indicator Categories

**Trend**
- Simple Moving Averages: SMA20, SMA50, SMA200
- Exponential Moving Averages: EMA12, EMA26, EMA50
- Price vs. each SMA as a percentage (how far above/below)
- Golden Cross detection (SMA50 crossing above SMA200) — exact date and bars ago
- Death Cross detection (SMA50 crossing below SMA200) — exact date and bars ago
- Average Directional Index (ADX-14): trend strength (`strong_trending` / `weak_trending` / `ranging`) + +DI/-DI directional signal
- Parabolic SAR: trailing stop signal (`bullish` / `bearish`)
- **Custom `detect_trend()` function**: velocity-aware 12-state taxonomy (see below)
- Last 5 values of SMA20/50/200 (slope context)

**Momentum**
- RSI(14) with `overbought` / `oversold` / `neutral` signal
- Last 5 RSI values (trend context)
- MACD: line, signal line, histogram; crossover state (`bullish` / `bearish`)
- MACD recent crossover event: direction + bars_ago (last 10 bars)
- Fresh crossover flag: `true` if crossover within last 5 bars
- Last 5 MACD histogram values
- Stochastic Oscillator: %K, %D, signal
- Money Flow Index (MFI-14): volume-weighted RSI
- **RSI divergence detection**: regular bullish/bearish, hidden bullish/bearish
- **MACD divergence detection**: regular bullish/bearish, hidden bullish/bearish

**Volatility**
- Bollinger Bands(20): upper, mid, lower, width
- Price vs. Bollinger: `above_upper` / `below_lower` / `within_bands`
- ATR(14): in price and as % of current price
- 30-day historical volatility (annualized)

**Volume**
- Current volume vs. 20-day and 50-day averages
- Volume ratio (current / 20d average)
- Volume trend: `increasing` / `decreasing` (20d avg vs. 50d avg)
- On-Balance Volume (OBV): current value + trend (`bullish` / `bearish`)
- Last 5 volume values

**Price Structure**
- Key resistance levels (clustered from 90-day pivot highs, top 3)
- Key support levels (clustered from 90-day pivot lows, bottom 3)
- 52-week high and low
- Current price, % from 52w high, % from 52w low
- Fibonacci retracement levels (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%)
- Nearest Fibonacci level and % distance from it

**Summary Signal (Weighted Scoring)**
All indicators are consolidated into a single weighted score:
- Each indicator votes `bullish`, `bearish`, or `neutral`
- Divergence signals (RSI, MACD) get **2x weight** — high-conviction reversal signals
- Fresh MACD crossovers (≤5 bars) get **2x weight**
- Trend signals are **ADX-gated** — trend votes are only counted when ADX confirms a trending regime (avoids false signals in choppy markets)
- Score formula: `bullish_signals / total_signals`
- Overall signal: `strong_buy` (≥0.8), `buy` (≥0.6), `neutral` (0.4–0.6), `avoid` (≤0.4), `sell` (≤0.2)
- Timing assessment: `favorable_entry`, `wait_for_clarity`, `unfavorable_entry`

#### The `detect_trend()` Function — 12-State Taxonomy
The most important custom function in the tool. It goes beyond simple "above/below SMA" checks by incorporating **MA slope (velocity)** to detect market structure more accurately.

| State | Condition |
|---|---|
| `strong_uptrend` | price > SMA20 > SMA50 > SMA200, all slopes rising |
| `strong_uptrend_losing_momentum` | same stack but SMA20 already falling |
| `uptrend` | price > SMA50 > SMA200 |
| `pullback_in_uptrend` | price < SMA50, MAs still rising, SMA50 > SMA200 |
| `pullback_weakening` | price < SMA50, MAs declining, SMA50 > SMA200 |
| `death_cross_forming` | SMA20 within 0.5% of SMA50 from above, both falling |
| `topping` | SMA20 crossed below SMA50, both declining, SMA50 > SMA200 |
| `developing_downtrend` | price broke below SMA200, SMA50 still above it |
| `downtrend` | price < SMA50 < SMA200 |
| `strong_downtrend` | price < SMA20 < SMA50 < SMA200 |
| `consolidation` | price within 3% of SMA20, SMAs flat/tight |
| `mixed` | catch-all for ambiguous conditions |

#### The `detect_divergence()` Function
Detects four divergence types between price and a momentum indicator (RSI or MACD):
- **Regular Bullish**: price makes lower low + indicator makes higher low → reversal up
- **Regular Bearish**: price makes higher high + indicator makes lower high → reversal down
- **Hidden Bullish**: price makes higher low + indicator makes lower low → uptrend continuation
- **Hidden Bearish**: price makes lower high + indicator makes higher high → downtrend continuation

Uses a 60-bar lookback and 5-bar window for peak/trough detection.

#### Output Schema
```json
{
  "ticker": "AAPL",
  "period": "1y",
  "data_points": 252,

  "trend": {
    "sma_20": 225.40,
    "sma_50": 220.15,
    "sma_200": 210.80,
    "ema_12": 226.10,
    "ema_26": 222.50,
    "ema_50": 218.90,
    "price_vs_sma20": 1.25,       // % above/below
    "price_vs_sma50": 3.60,
    "price_vs_sma200": 7.90,
    "golden_cross_date": "2024-11-15",
    "golden_cross_bars_ago": 42,
    "death_cross_date": null,
    "death_cross_bars_ago": null,
    "trend_signal": "strong_uptrend",
    "adx_14": 28.5,
    "adx_pos_di": 24.1,
    "adx_neg_di": 16.3,
    "trend_strength": "strong_trending",
    "adx_di_signal": "bullish",
    "parabolic_sar": 218.50,
    "parabolic_sar_signal": "bullish",
    "sma20_last5": [224.1, 224.6, 225.0, 225.2, 225.4],
    "sma50_last5": [219.8, 220.0, 220.1, 220.1, 220.2],
    "sma200_last5": [210.5, 210.6, 210.7, 210.7, 210.8]
  },

  "momentum": {
    "rsi_14": 58.4,
    "rsi_signal": "neutral",
    "rsi_last5": [54.1, 55.8, 57.2, 58.0, 58.4],
    "rsi_divergence": "none",
    "rsi_divergence_detail": { "regular_bullish": false, "regular_bearish": false, ... },
    "macd_line": 2.85,
    "macd_signal": 2.10,
    "macd_histogram": 0.75,
    "macd_crossover_state": "bullish",
    "macd_crossover_event": { "type": "bullish", "bars_ago": 3 },
    "macd_fresh_crossover": true,
    "macd_hist_last5": [0.20, 0.35, 0.52, 0.65, 0.75],
    "macd_divergence": "none",
    "stoch_k": 62.1,
    "stoch_d": 58.4,
    "stoch_signal": "neutral",
    "mfi_14": 61.2,
    "mfi_signal": "neutral"
  },

  "volatility": {
    "bollinger_upper": 242.10,
    "bollinger_mid": 225.40,
    "bollinger_lower": 208.70,
    "bollinger_width": 14.82,
    "price_vs_bb": "within_bands",
    "atr_14": 3.85,
    "atr_pct_of_price": 1.69,
    "hist_volatility_30d": 22.4
  },

  "volume": {
    "current_volume": 58000000,
    "avg_volume_20d": 62000000,
    "avg_volume_50d": 65000000,
    "volume_ratio_vs_avg": 0.94,
    "volume_trend": "decreasing",
    "obv_current": 1850000000,
    "obv_trend": "bullish",
    "volume_last5": [55000000, 61000000, 58000000, 63000000, 58000000]
  },

  "price_structure": {
    "key_resistance": [232.50, 237.20, 244.10],
    "key_support": [218.40, 213.60, 208.90],
    "52w_high": 244.10,
    "52w_low": 164.08,
    "current_price": 228.22,
    "pct_from_52w_high": -6.51,
    "pct_from_52w_low": 38.97,
    "fibonacci_levels": {
      "fib_0": 244.10,
      "fib_236": 225.85,
      "fib_382": 218.49,
      "fib_500": 204.09,
      "fib_618": 196.70,
      "fib_786": 185.13,
      "fib_100": 164.08
    },
    "nearest_fib_level": "fib_236",
    "nearest_fib_price": 225.85,
    "nearest_fib_pct_distance": 1.05
  },

  "summary": {
    "bullish_signals": 8,
    "bearish_signals": 2,
    "neutral_signals": 3,
    "total_signals": 13,
    "technical_score": 0.62,
    "overall_signal": "buy",
    "timing_assessment": "favorable_entry",
    "trend_quality": "strong_trending",
    "signal_detail": {
      "sma_trend": "bullish",
      "adx_di": "bullish",
      "parabolic_sar": "bullish",
      "rsi": "neutral",
      "macd_crossover": "bullish",
      "rsi_divergence": "neutral",
      "macd_divergence": "neutral",
      "mfi": "neutral",
      "obv_trend": "bullish",
      "bollinger": "neutral"
    }
  }
}
```

#### Key Implementation Details
- **Dual-path design**: `TA_AVAILABLE` flag switches between `ta`-library and manual implementations. Every indicator has both paths, ensuring identical output schema regardless of environment.
- **ADX gating**: Uptrend signals are only counted when ADX confirms trending conditions (`> 20`). Bearish reversal signals (death cross, topping) are always counted — a death cross is a death cross regardless of ADX.
- **Weighted summary scoring**: Divergences and fresh MACD crossovers receive 2x weight because they are statistically stronger reversal signals.
- **`detect_support_resistance()`**: Uses a rolling window pivot approach on 90-day data, clusters nearby levels with 1% tolerance, and adds Fibonacci retracement from the 52-week range.

#### Agents That Use This Tool
| Agent | Fields Used |
|---|---|
| Technical Analysis | All sections — primary input |
| Risk Assessment | Via Technical Agent's output (technical risks) |

---

### 3. `fetch_news.py`

#### Purpose
Fetches **recent news headlines, company profile metadata, institutional shareholders, and earnings history** for a stock. Provides the Market Intelligence Agent with its primary local data foundation, before it augments with WebSearch and RSS feeds.

#### Usage
```bash
python tools/fetch_news.py AAPL
python tools/fetch_news.py MSFT --limit 30
```

#### What It Does
Calls `yfinance.Ticker(ticker)` and extracts:
- `stock.info` — company profile fields
- `stock.news` — recent news items (up to `limit`, default 20)
- `stock.institutional_holders` — top 5 institutional holders
- `stock.major_holders` — summary of insider/institutional ownership percentages
- `stock.calendar` — upcoming earnings date
- `stock.earnings_history` — last 8 quarters of EPS estimates vs. actuals

**News parsing note**: yfinance's news format changed and now nests data under a `content` key with `pubDate`, `title`, `summary`, `provider`, and `canonicalUrl`/`clickThroughUrl`. The tool handles both the old flat format and the new nested format.

#### Output Schema
```json
{
  "ticker": "AAPL",

  "company_profile": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "country": "United States",
    "website": "https://www.apple.com",
    "summary": "Apple Inc. designs, manufactures..."  // up to 800 chars
    "ceo": "Timothy D. Cook",                        // from companyOfficers[0]
    "employees": 150000
  },

  "shareholders": {
    "top_institutional": [
      { "Holder": "Vanguard Group Inc", "Shares": 1260000000, "% Out": 0.0824, ... },
      { "Holder": "Blackrock Inc.", "Shares": 1080000000, ... },
      // up to 5 entries
    ],
    "major_holders_summary": [
      { "Value": "0.02%", "Breakdown": "% of Shares Held by All Insider" },
      { "Value": "61.90%", "Breakdown": "% of Shares Held by Institutions" },
      // ...
    ]
  },

  "recent_news": [
    {
      "title": "Apple Reports Record Q1 2025 Revenue",
      "summary": "Apple Inc. today reported record revenue of $124.3 billion...",  // 300 chars max
      "publisher": "Business Wire",
      "published": "2025-01-30T22:00:00Z",
      "url": "https://..."
    },
    // up to `limit` items (default 20)
  ],

  "earnings_calendar": {
    "Earnings Date": "2025-04-30 00:00:00-04:00",
    "Earnings Average": "1.62",
    "Earnings Low": "1.52",
    "Earnings High": "1.78"
  },

  "earnings_history": [
    {
      "date": "2025-01-30",
      "eps_estimate": 2.35,
      "eps_actual": 2.40,
      "surprise_pct": 2.13    // positive = beat, negative = miss
    },
    // up to 8 most recent quarters
  ],

  "data_timestamp": "2026-03-14 09:30"
}
```

#### Key Implementation Details
- News summary is truncated at 300 characters to keep token usage manageable
- Company profile summary is truncated at 800 characters (longer than `fetch_financials.py`'s 500-char version, as the Market Intelligence Agent needs more context)
- CEO is extracted from `companyOfficers[0].name` — if the list is empty, returns `null`
- All data extraction is wrapped in `try/except` blocks; if a section fails, it returns an empty dict/list rather than crashing
- `data_timestamp` is included so agents know exactly when the data was fetched

#### Agents That Use This Tool
| Agent | Fields Used |
|---|---|
| Market Intelligence | `company_profile`, `recent_news`, `shareholders` — primary input |
| Risk Assessment | Via Market Intelligence output (company risks, news-driven risks) |

---

### 4. `fetch_price_data.py`

#### Purpose
Fetches **historical OHLCV (Open, High, Low, Close, Volume) price data** for a stock. Provides the raw price series and summary statistics. This is the simplest and most lightweight of the four tools.

#### Usage
```bash
python tools/fetch_price_data.py AAPL
python tools/fetch_price_data.py MSFT --period 2y
python tools/fetch_price_data.py NVDA --period 6mo
```

#### What It Does
Calls `stock.history(period=period)` and computes summary statistics, then structures the data in two formats:
- **Summary stats**: current price, 52w high/low, 1-year return %, 30-day average volume
- **Recent 90-day window**: full OHLCV arrays as lists (for the Technical Analysis Agent to plot/analyze recent price action)
- **Full close series**: date → price dict for the entire requested period
- **Full volume series**: date → volume dict for the entire requested period

The 90-day window was chosen as a balance between recency (recent chart patterns) and context (enough data to identify short-term trends and support/resistance).

#### Output Schema
```json
{
  "ticker": "AAPL",
  "period": "1y",

  "current_price": 228.22,
  "price_52w_high": 244.10,
  "price_52w_low": 164.08,
  "price_change_1y_pct": 16.45,
  "avg_volume_30d": 62000000,

  "data_points": 252,
  "date_range": {
    "start": "2025-03-14",
    "end": "2026-03-13"
  },

  "recent_90d": {
    "dates": ["2025-12-12", "2025-12-13", ..., "2026-03-13"],  // 90 entries
    "close": [225.10, 226.50, ..., 228.22],                    // 90 entries
    "volume": [58000000, 61000000, ..., 58000000],              // 90 entries
    "high": [227.30, 228.10, ..., 229.50],                     // 90 entries
    "low": [223.80, 225.20, ..., 227.00]                       // 90 entries
  },

  "full_close_series": {
    "2025-03-14": 195.60,
    "2025-03-17": 196.40,
    // ... all trading days in period
    "2026-03-13": 228.22
  },

  "full_volume_series": {
    "2025-03-14": 75000000,
    // ...
    "2026-03-13": 58000000
  }
}
```

#### Key Implementation Details
- Index is converted from `DatetimeIndex` to string (`YYYY-MM-DD`) before serialization — avoids JSON serialization errors
- `price_change_1y_pct` compares the last close to the first close in the period (not necessarily a full calendar year if the period is shorter)
- `avg_volume_30d` uses the last 30 trading days, not 30 calendar days
- All price values are rounded to 2 decimal places; volume is cast to `int`
- Returns `{"error": "..."}` if yfinance returns no data for the ticker

#### Agents That Use This Tool
| Agent | Fields Used |
|---|---|
| Technical Analysis | `recent_90d` — 90-day OHLCV for chart analysis |
| Risk Assessment | Via Technical Agent output (price levels, volatility) |

---

## Running Tools Manually

All tools can be run standalone for debugging or data inspection:

```bash
# Activate virtual environment
source .venv/bin/activate

# Fetch fundamentals
python tools/fetch_financials.py AAPL | python -m json.tool | head -100

# Calculate technicals (2-year period)
python tools/calculate_technicals.py NVDA --period 2y | python -m json.tool

# Fetch news (30 items)
python tools/fetch_news.py MSFT --limit 30 | python -m json.tool

# Fetch price data (6-month period)
python tools/fetch_price_data.py TSLA --period 6mo | python -m json.tool

# Save output to file for inspection
python tools/fetch_financials.py AAPL > /tmp/aapl_financials.json
```

---

## Data Flow to Agents

```
fetch_financials.py
    └── FINANCIALS_DATA
            ├── key_stats         → Fundamental Agent, Macro Agent
            ├── valuation         → Fundamental Agent
            ├── profitability     → Fundamental Agent
            ├── growth            → Fundamental Agent
            ├── balance_sheet     → Fundamental Agent
            ├── cash_flow         → Fundamental Agent
            ├── dividend_shares   → Fundamental Agent
            ├── analyst_consensus → Fundamental Agent, Analyst Sentiment Agent
            ├── historical_*      → Fundamental Agent (trend analysis)
            └── quarterly_*       → Fundamental Agent (recent quarter momentum)

fetch_news.py
    └── NEWS_DATA
            ├── company_profile   → Market Intelligence Agent
            ├── shareholders      → Market Intelligence Agent
            ├── recent_news       → Market Intelligence Agent
            ├── earnings_calendar → Market Intelligence Agent
            └── earnings_history  → Market Intelligence Agent

calculate_technicals.py
    └── TECHNICALS_DATA
            ├── trend             → Technical Analysis Agent
            ├── momentum          → Technical Analysis Agent
            ├── volatility        → Technical Analysis Agent
            ├── volume            → Technical Analysis Agent
            ├── price_structure   → Technical Analysis Agent
            └── summary           → Technical Analysis Agent (overall signal)

fetch_price_data.py
    └── PRICE_DATA
            ├── current_price     → Technical Analysis Agent
            ├── price_52w_high/low→ Technical Analysis Agent
            ├── price_change_1y   → Technical Analysis Agent
            └── recent_90d        → Technical Analysis Agent (chart context)
```

---

## Dependencies

All tools require:
```
yfinance>=0.2.0
pandas>=1.5.0
numpy>=1.23.0
```

`calculate_technicals.py` additionally uses:
```
ta>=0.10.0     # Technical analysis library (optional — has manual fallback)
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

Or using the project virtual environment:
```bash
.venv/bin/pip install -r requirements.txt
```

---

## Error Handling

All tools follow the same error handling strategy:

1. **Partial data is better than no data**: If one section fails (e.g., `stock.institutional_holders` throws), that section returns `{}` or `[]` and the rest of the output is still returned.
2. **No hard crashes**: All external calls are wrapped in `try/except`. Errors are captured and the tool continues.
3. **Explicit `null` values**: `safe_float()` and `safe_int()` return `None` (JSON `null`) for missing/NaN/infinite values rather than crashing or returning 0.
4. **Error key**: If the entire tool fails (e.g., ticker not found), it returns `{"error": "..."}` which the orchestrator notes and continues with available data.

The orchestrator (`.claude/commands/analyze-stock.md`) is instructed: *"If any tool fails, note the error and proceed with available data."*
