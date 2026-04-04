# `fetch_financials.py` — Financial Data Reference

Fetches fundamental financial data for a stock ticker via **yfinance** (Yahoo Finance).
Source: `tools/fetch_financials.py`

## Usage

```bash
python tools/fetch_financials.py AAPL
```

Returns a single JSON object with 14 top-level sections described below.

---

## Data Freshness Overview

| Section | Source | Freshness |
|---|---|---|
| `key_stats` | `stock.info` | Market cap / enterprise value: **real-time (today)**. Static fields (employees, sector, summary): updated periodically by Yahoo Finance |
| `valuation` | `stock.info` | **Real-time** — price-based ratios (P/E, P/S, P/B) recalculate continuously using the live stock price against the latest TTM financials |
| `profitability` | `stock.info` | **TTM** (trailing twelve months) — reflects the most recently reported quarter |
| `growth` | `stock.info` | **TTM / most recent quarter** — updated when a new earnings report is filed |
| `balance_sheet` | `stock.info` | **Most recent quarterly filing** |
| `cash_flow` | `stock.info` | **TTM** — most recently reported quarter |
| `dividend_shares` | `stock.info` | Dividend rate/yield: near real-time. Short interest: updated ~2x/month by exchanges |
| `analyst_consensus` | `stock.info` | **Continuously updated** as analysts revise price targets and ratings |
| `historical_income_statement` | `stock.financials` | **Annual** — up to 4 fiscal years. Most recent period = last fiscal year-end |
| `historical_balance_sheet` | `stock.balance_sheet` | **Annual** — up to 4 fiscal years |
| `historical_cash_flow` | `stock.cashflow` | **Annual** — up to 4 fiscal years |
| `quarterly_income_statement` | `stock.quarterly_financials` | **Last 3 quarters** — most recent data available |
| `quarterly_balance_sheet` | `stock.quarterly_balance_sheet` | **Last 3 quarters** |
| `quarterly_cash_flow` | `stock.quarterly_cashflow` | **Last 3 quarters** |

> **Key insight:** The `stock.info` sections (valuation through analyst_consensus) use **TTM data** derived from the most recently reported quarter — not the fiscal year-end. For example, if a company's fiscal year ends in September but reported a December quarter, the TTM figures already include that December quarter. This makes them more current than the `historical_*` annual sections.

---

## Section Reference

### `key_stats`

General company profile and size metrics.

| Field | Description |
|---|---|
| `company_name` | Full legal company name |
| `sector` | GICS sector (e.g., Technology) |
| `industry` | GICS industry sub-group |
| `country` | Country of incorporation |
| `employees` | Number of full-time employees |
| `market_cap` | Market capitalisation in local currency (integer, real-time) |
| `enterprise_value` | Market cap + debt − cash (real-time) |
| `currency` | Reporting currency code (e.g., USD) |
| `exchange` | Primary listing exchange (e.g., NMS) |
| `website` | Company website URL |
| `business_summary` | Business description (truncated to 500 characters) |

**Freshness:** `market_cap` and `enterprise_value` update in real-time with the stock price. All other fields are static/periodically updated by Yahoo Finance.

---

### `valuation`

Price-based valuation multiples. All ratios use **today's live price** in the numerator.

| Field | Description |
|---|---|
| `trailing_pe` | Price / trailing 12-month EPS |
| `forward_pe` | Price / next-12-month consensus EPS estimate |
| `peg_ratio` | P/E divided by expected earnings growth rate |
| `price_to_sales` | Price / trailing 12-month revenue per share |
| `price_to_book` | Price / book value per share |
| `ev_to_ebitda` | Enterprise value / trailing 12-month EBITDA |
| `ev_to_revenue` | Enterprise value / trailing 12-month revenue |

**Freshness:** **Real-time** — recalculated continuously during market hours as the stock price changes. The earnings/revenue denominators update when new quarterly results are reported.

---

### `profitability`

Margin and return metrics on a **trailing twelve-month (TTM)** basis.

| Field | Description |
|---|---|
| `gross_margin` | Gross profit / revenue (TTM) |
| `operating_margin` | Operating income / revenue (TTM) |
| `net_margin` | Net income / revenue (TTM) |
| `roe` | Return on equity (TTM) |
| `roa` | Return on assets (TTM) |
| `ebitda` | Earnings before interest, taxes, depreciation & amortisation (TTM, absolute value) |
| `trailing_eps` | Diluted EPS (TTM) |
| `forward_eps` | Next-12-month consensus EPS estimate |

**Freshness:** TTM figures update when a new quarterly earnings report is filed. `forward_eps` updates as analyst estimates are revised.

---

### `growth`

Year-over-year and quarterly growth rates.

| Field | Description |
|---|---|
| `revenue_growth_yoy` | TTM revenue growth vs. prior TTM period (decimal, e.g. 0.157 = 15.7%) |
| `earnings_growth_yoy` | TTM net income growth vs. prior TTM period |
| `earnings_quarterly_growth` | Most recent quarter EPS growth vs. same quarter prior year |
| `revenue_ttm` | Total TTM revenue (absolute, in reporting currency) |

**Freshness:** Updated when the most recent quarterly earnings are reported.

---

### `balance_sheet`

Point-in-time balance sheet snapshot from the **most recently filed quarter**.

| Field | Description |
|---|---|
| `total_cash` | Cash + short-term investments |
| `total_debt` | Total interest-bearing debt (short + long term) |
| `net_debt` | `total_debt` − `total_cash` (derived) |
| `debt_to_equity` | Total debt / shareholders' equity (%) |
| `current_ratio` | Current assets / current liabilities |
| `quick_ratio` | (Current assets − inventory) / current liabilities |
| `book_value_per_share` | Shareholders' equity / shares outstanding |

**Freshness:** Reflects the **most recently filed quarterly report**. Updated ~4× per year at each earnings release.

---

### `cash_flow`

TTM cash flow summary.

| Field | Description |
|---|---|
| `operating_cash_flow` | Net cash from operating activities (TTM) |
| `free_cash_flow` | Operating cash flow − capital expenditure (TTM) |
| `capex` | Capital expenditure, derived as `operating_cash_flow − free_cash_flow` |

**Freshness:** TTM — includes the most recently reported quarter.

---

### `dividend_shares`

Dividend policy and share structure data.

| Field | Description |
|---|---|
| `dividend_yield` | Annual dividend / current price (decimal) |
| `dividend_rate` | Annual dividend per share (absolute) |
| `payout_ratio` | Dividends paid / net income |
| `shares_outstanding` | Total shares issued |
| `float_shares` | Publicly tradeable shares (excludes insider/institutional lockups) |
| `shares_short` | Number of shares sold short |
| `short_ratio` | Days to cover (shares short / average daily volume) |
| `short_percent_of_float` | Short interest as % of float |

**Freshness:** `dividend_yield` is real-time (price-based). Short interest (`shares_short`, `short_ratio`, `short_percent_of_float`) is reported by exchanges twice per month and lags by ~2 weeks.

---

### `analyst_consensus`

Aggregated sell-side analyst price targets and ratings.

| Field | Description |
|---|---|
| `target_mean_price` | Consensus (mean) 12-month price target |
| `target_high_price` | Highest analyst price target |
| `target_low_price` | Lowest analyst price target |
| `recommendation_key` | Normalised rating string: `strong_buy`, `buy`, `hold`, `underperform`, `sell` |
| `number_of_analyst_opinions` | Number of analysts contributing to the consensus |

**Freshness:** Near real-time — updates whenever an analyst publishes or revises a rating or price target.

---

### `historical_income_statement`

Annual income statements for up to the **last 4 fiscal years**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are fiscal year-end dates).

Includes: Total Revenue, Gross Profit, Operating Income, Net Income, EBITDA, EPS, and more.

**Freshness:** Annual — most recent period is the **last completed fiscal year-end**. For companies with September fiscal year-ends this would be Sep 2025. This is **one quarter behind** the quarterly sections below.

---

### `historical_balance_sheet`

Annual balance sheets for up to the **last 4 fiscal years**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are fiscal year-end dates).

Includes: Total Assets, Total Liabilities, Shareholders' Equity, Cash & Equivalents, Total Debt, Working Capital, and more.

**Freshness:** Annual — same cadence as `historical_income_statement`.

---

### `historical_cash_flow`

Annual cash flow statements for up to the **last 4 fiscal years**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are fiscal year-end dates).

Includes: Operating Cash Flow, Free Cash Flow, Capital Expenditure, Dividends Paid, Share Buybacks, and more.

**Freshness:** Annual — same cadence as `historical_income_statement`.

---

### `quarterly_income_statement`

Income statements for the **3 most recently reported quarters**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are quarter-end dates).

Contains the same metrics as `historical_income_statement` but on a quarterly basis.

**Freshness:** Most up-to-date financial statement data available. Updated within days of each earnings release (~4× per year). This is the **most recent fundamental data** in the entire output.

---

### `quarterly_balance_sheet`

Balance sheets for the **3 most recently reported quarters**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are quarter-end dates).

**Freshness:** Same as `quarterly_income_statement` — most recent quarterly filing.

---

### `quarterly_cash_flow`

Cash flow statements for the **3 most recently reported quarters**.

Structure: `{ "YYYY-MM-DD": { "metric": value, ... }, ... }` (keys are quarter-end dates).

**Freshness:** Same as `quarterly_income_statement` — most recent quarterly filing.

---

## Freshness Summary Diagram

```
Real-time (live price)
  └── valuation.*  (P/E, P/S, P/B, EV multiples)
  └── key_stats.market_cap / enterprise_value

Most recent quarter (TTM or point-in-time)
  └── profitability.*
  └── growth.*
  └── balance_sheet.*
  └── cash_flow.*
  └── dividend_shares.dividend_yield
  └── analyst_consensus.*
  └── quarterly_income_statement  ← 3 most recent quarters
  └── quarterly_balance_sheet     ← 3 most recent quarters
  └── quarterly_cash_flow         ← 3 most recent quarters

Annual (fiscal year-end, ~1 quarter behind quarterly sections)
  └── historical_income_statement  ← last 4 fiscal years
  └── historical_balance_sheet     ← last 4 fiscal years
  └── historical_cash_flow         ← last 4 fiscal years

Bi-monthly (short interest)
  └── dividend_shares.shares_short / short_ratio / short_percent_of_float
```

---

## Data Source

All data is sourced from **Yahoo Finance** via the [yfinance](https://github.com/ranaroussi/yfinance) library (v1.2.0+). Yahoo Finance data is provided as-is and may occasionally differ from primary exchange feeds or SEC filings by small rounding amounts.
