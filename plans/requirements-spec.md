# Requirements Specification: AI Multi-Agent Stock Analysis System

**Version**: 1.0
**Date**: 2026-03-13
**Purpose**: Personal investing tool — value investing (6–24 month horizon)

---

## 1. System Overview

An AI-powered, multi-agent stock research platform that:
1. Scans the US equity market (S&P 500 + Russell 1000) for investment candidates
2. Performs deep, institutional-quality research on individual stocks
3. Produces professional investment memo reports (Markdown + HTML)
4. Tracks all analyses and recommendations in a SQLite database

**Style**: Long-term value investing (fundamentals-first, Buffett-style)
**Target user**: Single user, local deployment

---

## 2. Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent Orchestration | LangGraph |
| LLM | Claude (Anthropic API) — `claude-sonnet-4-6` for analysis, `claude-haiku-4-5` for lightweight tasks |
| Primary Data | `yfinance` (price history, fundamentals, basic news) |
| Gap Data | Claude-powered web scraping (news, sentiment, analyst commentary) |
| Data Processing | `pandas`, `numpy` |
| Report Generation | Jinja2 templates → Markdown + HTML |
| Persistence | SQLite (`analyses.db`) |
| Config | `python-dotenv` (.env file) |
| CLI | `argparse` or `click` |

---

## 3. Data Sources & Access Strategy

### Primary (yfinance — free, no key required)
- Price history (OHLCV)
- Basic financials (income statement, balance sheet, cash flow)
- Key metrics (P/E, P/B, EPS, market cap, etc.)
- Basic news headlines
- Analyst price targets (limited)
- Dividend history

### Gap Filling (Claude-powered web scraping)
Claude will scrape publicly available pages to retrieve:
- Recent news and earnings commentary (Yahoo Finance, MarketWatch)
- Analyst ratings and commentary
- Management/CEO background (LinkedIn summaries, Wikipedia)
- Macro economic indicators (FRED, BLS public data)
- Industry/competitor context

### Data Gaps to Accept (MVP)
- Real-time quotes (use end-of-day data)
- Options flow data
- Institutional holdings (13F) — accept limited coverage
- Social sentiment (Reddit, Twitter) — optional Phase 3

---

## 4. Functional Requirements

### FR-001 — Single Stock Deep Dive
```
Input:  Ticker symbol (e.g., AAPL)
Output: Markdown report + HTML saved to /reports/{TICKER}_{DATE}/
        SQLite record of analysis and recommendation
```
Trigger: `python analyze.py --ticker AAPL`

### FR-002 — Market Scanner
```
Input:  None (uses pre-defined universe: S&P 500 + Russell 1000)
Output: Ranked watchlist of top N candidates (default 20)
        Each candidate has: ticker, reason, quick metrics summary
```
Trigger: `python scan.py [--top 20] [--filter value|growth|momentum]`

### FR-003 — Scan + Deep Dive Pipeline
```
Input:  None
Output: Scanner finds top candidates, auto-runs deep dive on top 5
        Full report set for each
```
Trigger: `python run.py --mode full`

### FR-004 — Agent Outputs
Each agent must produce a **structured JSON result** that feeds into the next stage.
All agent outputs are accumulated in a shared LangGraph state object.

### FR-005 — Investment Memo Report
Report must include all 11 sections from the plan:
1. Executive Summary
2. Market Context
3. Company Overview
4. Industry Analysis
5. Fundamental Analysis
6. Technical Analysis
7. Sentiment Analysis
8. Risk Analysis
9. Investment Thesis
10. Portfolio Fit
11. Final Recommendation (Strong Buy / Buy / Hold / Avoid)

Report must also include:
- Expected return estimate (12-month price target)
- Downside risk estimate
- Key risks (top 3)
- Investment horizon
- Confidence score (1–10)

### FR-006 — SQLite Analysis Tracking
Store per analysis:
- Ticker, company name, analysis date
- Final recommendation (Strong Buy / Buy / Hold / Avoid)
- Claude's 12-month price target
- Confidence score
- Key thesis (1-paragraph summary)
- Report file path
- Status for future tracking (open/closed)

### FR-007 — Rate Limit & Error Handling
- Graceful handling of yfinance rate limits (exponential backoff)
- Graceful handling of Claude API rate limits
- If a data source fails, agent proceeds with available data and notes the gap

---

## 5. Agent Specifications

### Phase 1 MVP — Deep Research Layer (Layer 3)

All agents run sequentially via LangGraph state graph.

---

#### Agent 1: Company Intelligence Agent
**Role**: Build a complete company profile
**Data sources**: yfinance + Claude web scraping
**Output JSON**:
```json
{
  "company_name": "",
  "sector": "",
  "industry": "",
  "business_description": "",
  "revenue_streams": [],
  "key_products": [],
  "competitive_advantages": [],
  "key_risks_business": [],
  "management_quality_score": 1-10,
  "management_notes": "",
  "market_cap_category": "large|mid|small",
  "years_in_operation": 0
}
```

---

#### Agent 2: Fundamental Analysis Agent
**Role**: Evaluate financial strength and value
**Data sources**: yfinance financial statements
**Investment style**: Value-first (P/E, P/B, EV/EBITDA, FCF yield)
**Output JSON**:
```json
{
  "profitability": { "eps": 0, "gross_margin": 0, "net_margin": 0, "roe": 0, "roic": 0 },
  "growth": { "revenue_yoy": 0, "earnings_yoy": 0, "fcf_yoy": 0 },
  "valuation": { "pe": 0, "pb": 0, "ps": 0, "ev_ebitda": 0, "peg": 0, "fcf_yield": 0 },
  "balance_sheet": { "debt_to_equity": 0, "current_ratio": 0, "interest_coverage": 0 },
  "vs_sector_pe": "cheap|fair|expensive",
  "vs_historical_pe": "cheap|fair|expensive",
  "fundamental_score": 1-10,
  "fundamental_summary": ""
}
```

---

#### Agent 3: Technical Analysis Agent
**Role**: Evaluate price behavior and entry timing
**Data sources**: yfinance price history
**Output JSON**:
```json
{
  "trend": { "above_sma20": true, "above_sma50": true, "above_sma200": true, "trend_direction": "up|down|sideways" },
  "momentum": { "rsi_14": 0, "macd_signal": "bullish|bearish|neutral" },
  "volatility": { "atr_14": 0, "bollinger_position": "upper|middle|lower" },
  "support_level": 0,
  "resistance_level": 0,
  "entry_timing": "strong_entry|neutral|risky|wait",
  "technical_score": 1-10,
  "technical_summary": ""
}
```

---

#### Agent 4: Sentiment Intelligence Agent
**Role**: Analyze market sentiment from news and analyst activity
**Data sources**: yfinance news + Claude web scraping
**Output JSON**:
```json
{
  "news_sentiment": "bullish|neutral|bearish",
  "analyst_consensus": "strong_buy|buy|hold|sell|strong_sell",
  "analyst_price_target": 0,
  "analyst_upside_pct": 0,
  "recent_news_headlines": [],
  "sentiment_score": 1-10,
  "narrative_shift": "positive|none|negative",
  "sentiment_summary": ""
}
```

---

#### Agent 5: Macro Intelligence Agent
**Role**: Evaluate macro environment for this stock's sector
**Data sources**: Claude web scraping (FRED, recent macro news)
**Output JSON**:
```json
{
  "interest_rate_environment": "supportive|neutral|negative",
  "inflation_trend": "declining|stable|rising",
  "economic_cycle": "expansion|peak|contraction|recovery",
  "sector_macro_impact": "tailwind|neutral|headwind",
  "macro_score": 1-10,
  "macro_summary": ""
}
```

---

#### Agent 6: Investment Committee Agent (Synthesis)
**Role**: Synthesize all agent outputs into final investment memo
**Data sources**: All 5 agent JSON outputs (in LangGraph state)
**Output**: Full Markdown investment memo + structured recommendation JSON

**Recommendation schema**:
```json
{
  "recommendation": "Strong Buy|Buy|Hold|Avoid",
  "confidence": 1-10,
  "price_target_12m": 0,
  "upside_pct": 0,
  "downside_risk_pct": 0,
  "investment_horizon": "6-12 months|12-24 months",
  "thesis": "",
  "bull_case": "",
  "bear_case": "",
  "top_3_risks": [],
  "composite_score": 1-10
}
```

---

### Phase 2 — Opportunity Discovery Layer (add after MVP)

#### Agent 7: Quant Screening Agent
Filters S&P 500 + Russell 1000 using yfinance bulk data.
No LLM calls — pure quant filters.

**Value filter**: P/E < 20, P/B < 3, EV/EBITDA < 12
**Quality filter**: ROE > 12%, positive FCF, D/E < 1.5
**Growth filter**: Revenue YoY > 5%, EPS growth positive
**Momentum filter**: Price above SMA 50

Output: Ranked list of top 50 candidates with scores.

#### Agent 8: Market Scanner Agent
Identifies unusual activity from daily data:
- Volume spike > 2x 20-day average
- Price move > 3% in a day
- Earnings reaction (large gap up/down)

Output: Watchlist with reason codes.

---

### Phase 3 — Portfolio Construction + Risk (future)
- Opportunity Ranking Agent
- Portfolio Optimization Agent
- Risk Assessment Agent
- Stress Testing Agent

---

## 6. LangGraph Architecture

### MVP State Graph (Deep Research Pipeline)
```
START
  ↓
[Data Fetcher Node]     — fetch all yfinance data for ticker
  ↓
[Company Intel Agent]   — build company profile
  ↓
[Fundamental Agent]     — financial analysis
  ↓
[Technical Agent]       — price/chart analysis
  ↓
[Sentiment Agent]       — news + analyst sentiment
  ↓
[Macro Agent]           — macro environment check
  ↓
[Committee Agent]       — synthesize → recommendation
  ↓
[Report Writer Node]    — render Markdown + HTML report
  ↓
[DB Writer Node]        — save to SQLite
  ↓
END
```

### Shared LangGraph State Object
```python
class AnalysisState(TypedDict):
    ticker: str
    company_data: dict          # raw yfinance data
    company_profile: dict       # Agent 1 output
    fundamental_analysis: dict  # Agent 2 output
    technical_analysis: dict    # Agent 3 output
    sentiment_analysis: dict    # Agent 4 output
    macro_analysis: dict        # Agent 5 output
    recommendation: dict        # Committee output
    report_markdown: str        # Final rendered report
    errors: list[str]           # Any errors encountered
```

---

## 7. Project Structure

```
Stock_Analysis_System/
├── .env                        # ANTHROPIC_API_KEY, etc.
├── requirements.txt
├── analyze.py                  # CLI: single ticker deep dive
├── scan.py                     # CLI: market scanner
├── run.py                      # CLI: full pipeline
│
├── agents/
│   ├── __init__.py
│   ├── company_intel.py        # Agent 1
│   ├── fundamental.py          # Agent 2
│   ├── technical.py            # Agent 3
│   ├── sentiment.py            # Agent 4
│   ├── macro.py                # Agent 5
│   └── committee.py            # Agent 6 (synthesis)
│
├── data/
│   ├── fetcher.py              # yfinance data fetcher
│   ├── scraper.py              # Claude-powered web scraper
│   └── universe.py             # S&P 500 + Russell 1000 tickers
│
├── graph/
│   ├── pipeline.py             # LangGraph state graph definition
│   └── state.py                # AnalysisState TypedDict
│
├── reports/
│   └── {TICKER}_{DATE}/
│       ├── report.md
│       └── report.html
│
├── templates/
│   ├── report.md.j2            # Jinja2 Markdown template
│   └── report.html.j2          # Jinja2 HTML template
│
├── db/
│   ├── database.py             # SQLite connection + schema
│   └── analyses.db             # (auto-created)
│
└── plans/
    ├── multi-agents-stock-analysis-system.md
    └── requirements-spec.md    # This file
```

---

## 8. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | Single stock deep dive completes in < 3 minutes |
| NFR-002 | Scanner pre-filter (quant only) completes in < 2 minutes for 1500 stocks |
| NFR-003 | System runs entirely locally (no cloud deployment needed) |
| NFR-004 | API rate limits handled with exponential backoff (yfinance + Claude) |
| NFR-005 | If any agent fails, pipeline continues with available data (no hard crashes) |
| NFR-006 | Each agent notes data gaps clearly in its output |
| NFR-007 | Reports saved with timestamp to avoid overwrites |
| NFR-008 | Claude model costs target: < $0.50 per full stock analysis |
| NFR-009 | System uses `claude-haiku-4-5` for lightweight parsing tasks, `claude-sonnet-4-6` for reasoning |

---

## 9. User Stories & Acceptance Criteria

### US-001 — Deep Dive on a Stock
**As a** value investor
**I want to** run `python analyze.py --ticker MSFT`
**So that** I receive a complete investment memo on Microsoft

**Acceptance criteria:**
- [ ] Report generated in `/reports/MSFT_{date}/report.md`
- [ ] Report contains all 11 sections
- [ ] Final recommendation is one of: Strong Buy / Buy / Hold / Avoid
- [ ] Price target and confidence score are included
- [ ] SQLite record created

### US-002 — Market Scan for Value Opportunities
**As a** value investor
**I want to** run `python scan.py --filter value --top 20`
**So that** I see the 20 most undervalued stocks in the S&P 500 + Russell 1000

**Acceptance criteria:**
- [ ] Output shows ranked list with ticker, sector, key metrics, reason
- [ ] Filters applied: P/E < 20, P/B < 3, ROE > 12%, positive FCF
- [ ] Runs without LLM calls (pure yfinance quant filter)
- [ ] Completes in < 2 minutes

### US-003 — View Past Analyses
**As a** value investor
**I want to** query past recommendations
**So that** I can track how my analysis aged

**Acceptance criteria:**
- [ ] SQLite DB queryable with standard tools
- [ ] Contains: date, ticker, recommendation, price target, confidence, thesis

---

## 10. Open Questions (to decide during implementation)

| # | Question | Recommendation |
|---|---|---|
| OQ-1 | Which Claude model for which agents? | Use `haiku-4-5` for data extraction/parsing, `sonnet-4-6` for analysis reasoning, `sonnet-4-6` for committee synthesis |
| OQ-2 | How to handle stocks with very limited yfinance data (small caps)? | Note data quality in report; lower confidence score automatically |
| OQ-3 | Should web scraping use Playwright (JS-rendered pages) or requests+BeautifulSoup? | Start with requests+BS4; upgrade to Playwright if needed |
| OQ-4 | Caching: re-use data for same ticker within same day? | Yes — cache yfinance data to avoid repeat calls during development |
| OQ-5 | Should the scanner add Finnhub free tier later for better news coverage? | Yes — add in Phase 2 as a simple enhancement |

---

## 11. Build Phases

### Phase 1 — MVP Deep Research (Build First)
- [ ] Project skeleton + .env + requirements.txt
- [ ] `data/fetcher.py` — yfinance wrapper
- [ ] `graph/state.py` — AnalysisState TypedDict
- [ ] `graph/pipeline.py` — LangGraph graph skeleton
- [ ] Agent 2: Fundamental Analysis (most critical, best data)
- [ ] Agent 3: Technical Analysis (pure yfinance, no scraping)
- [ ] Agent 6: Committee Agent (simplified — just Agents 2+3 for now)
- [ ] Report template (Markdown)
- [ ] SQLite DB setup
- [ ] CLI: `analyze.py`

### Phase 2 — Full Research Pipeline
- [ ] Agent 1: Company Intelligence (add web scraping)
- [ ] Agent 4: Sentiment Intelligence (scraping)
- [ ] Agent 5: Macro Intelligence (scraping)
- [ ] Upgrade Committee Agent to use all 5 agents
- [ ] HTML report template
- [ ] Better error handling and data gap notes

### Phase 3 — Scanner + Discovery
- [ ] `data/universe.py` — S&P 500 + Russell 1000 tickers
- [ ] Agent 7: Quant Screening Agent
- [ ] Agent 8: Market Scanner Agent
- [ ] `scan.py` CLI

### Phase 4 — Portfolio + Risk (future)
- [ ] Ranking Agent
- [ ] Portfolio Optimization
- [ ] Risk Agents

---

*Generated by: /sc:brainstorm session on 2026-03-13*
*Next step: Use `/sc:design` to create architecture and implementation plan*
