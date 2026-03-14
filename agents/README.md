# Agents — Multi-Agent Stock Analysis System

This folder contains the **prompt files** for all 7 AI agents in the system.
Each file is a plain-text markdown document that defines an agent's role, inputs, analytical tasks, output format, and critical thinking standards.

Agents are not Python classes — they are **Claude prompt personas** invoked via the `Task` tool by the orchestrator skill (`.claude/commands/analyze-stock.md`).

---

## How Agents Work

The orchestrator runs 6 analysis agents **in parallel** (Stage 2), then passes all their outputs to the Chief Analyst for synthesis (Stage 3).

```
┌─────────────────────────────────────────────────────────┐
│              Parallel Analysis Stage (Stage 2)          │
│                                                         │
│  ┌──────────────────┐   ┌──────────────────┐           │
│  │ Market           │   │ Macro Economy    │           │
│  │ Intelligence     │   │ Agent            │           │
│  └──────────────────┘   └──────────────────┘           │
│  ┌──────────────────┐   ┌──────────────────┐           │
│  │ Fundamental      │   │ Technical        │           │
│  │ Analysis         │   │ Analysis         │           │
│  └──────────────────┘   └──────────────────┘           │
│  ┌──────────────────┐   ┌──────────────────┐           │
│  │ Analyst          │   │ Risk             │           │
│  │ Sentiment        │   │ Assessment       │           │
│  └──────────────────┘   └──────────────────┘           │
└──────────────────────────────────┬──────────────────────┘
                                   │ all 6 reports
                                   ▼
                        ┌─────────────────────┐
                        │  Chief Analyst       │
                        │  (Synthesis Stage 3) │
                        └─────────────────────┘
                                   │
                                   ▼
                          Final Investment Report
```

Each agent prompt file follows the same structure:
- **Role** — what the agent's job is
- **Input Data** — which data variables it receives
- **Tasks** — numbered analytical steps
- **Output Format** — the exact markdown section it must produce
- **Critical Thinking Requirements** — mandatory epistemic standards

---

## Agent Reference

### Agent 1 — Market Intelligence

**File**: `market_intelligence.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: `NEWS_DATA` (yfinance) + WebSearch + RSS feeds

#### Purpose
Builds a complete picture of the company as a business — what it does, how it competes, who owns it, and what the news cycle looks like right now. This is the "company intelligence" layer.

#### Inputs
| Variable | Source | Content |
|---|---|---|
| `NEWS_DATA.company_profile` | `fetch_news.py` | Business summary, sector, industry, CEO, employees |
| `NEWS_DATA.recent_news` | `fetch_news.py` | Up to 20 recent news headlines + summaries |
| `NEWS_DATA.shareholders` | `fetch_news.py` | Top 5 institutional holders + major holders summary |

#### What It Analyzes
1. **Company Intelligence** — business model, revenue streams, competitive moat (brand, network effects, patents, switching costs, cost advantages), management quality
2. **Industry Analysis** — market size, structure (fragmented vs. consolidated), key competitors, regulatory/technology risks
3. **News & Events** — categorizes events (earnings, product launches, M&A, lawsuits, regulatory), assesses sentiment, flags material high-impact news
4. **Web Search** — searches financial media (Bloomberg, Reuters, CNBC, WSJ) for news in the last 30 days
5. **RSS Feed Intelligence** — fetches 15+ live RSS feeds (Yahoo Finance, Seeking Alpha, Reuters, CNBC, MarketWatch, Barron's, TheStreet, Zacks, Google News site-filtered feeds), deduplicates cross-source stories, applies 30-day recency gate, ranks top 10 stories by impact

#### Output Section
`## Market Intelligence Report: [TICKER]` containing:
- Company Overview
- Competitive Position (moat analysis)
- Industry Analysis
- Recent Events & News (categorized)
- Key Narratives (2–3 dominant themes)
- RSS Feed Intelligence table (source availability + top stories)
- Intelligence Summary (sentiment, catalysts, risks, data quality)

#### Critical Thinking Standards
- Distinguish facts from opinions in news articles
- Flag if company narrative seems overly promotional
- Note conflicting information across sources
- State clearly when data is limited or unavailable

---

### Agent 2 — Macro Economy

**File**: `macro_economy.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: WebSearch only (100% real-time)

#### Purpose
Evaluates whether the current macroeconomic environment is a **tailwind, headwind, or neutral** for this specific stock and sector. Does not use any local data — everything is sourced live.

#### Inputs
| Variable | Content |
|---|---|
| `TICKER` | Stock symbol |
| `FINANCIALS_DATA.key_stats.sector` | Company sector |
| `FINANCIALS_DATA.key_stats.industry` | Company industry |

#### What It Analyzes
1. **Monetary Policy & Rates** — current Fed funds rate, rate trajectory (rising/falling/on hold), QT/QE status, sector sensitivity to rates
2. **Inflation** — CPI/PCE levels, trend (cooling/sticky/rising), input cost implications for the industry
3. **Economic Growth** — US GDP rate and forecast, consumer confidence, labor market conditions, recession probabilities
4. **Global Factors** — geopolitical risks, USD strength vs. multinational revenues, China/EM outlook if sector-relevant
5. **Market Conditions** — S&P 500/Nasdaq trend, VIX level, sector performance vs. benchmark, current sector rotation dynamics
6. **Sector-Specific Impact** — translates generic macro into specific sector effects (e.g., "rising rates are a headwind for high-multiple tech")

#### Output Section
`## Macro Economy Report: [TICKER] / [SECTOR]` containing:
- Macro Environment table (Fed rate, CPI, GDP, VIX — each with current state, trend, sector impact)
- Monetary Policy Analysis
- Economic Growth Outlook
- Geopolitical & Global Risks
- Sector Performance & Rotation
- **Macro Verdict**: `Supportive / Neutral / Hostile` + key tailwinds/headwinds + confidence level

#### Critical Thinking Standards
- Cite specific data points, not vague claims
- Acknowledge uncertainty in macro forecasts
- Distinguish short-term vs. long-term macro impacts
- Note if the stock is a macro hedge or a macro amplifier

---

### Agent 3 — Fundamental Analysis

**File**: `fundamental_analysis.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: `FINANCIALS_DATA` from `fetch_financials.py`

#### Purpose
The most data-rich agent. Performs a rigorous, institutional-grade evaluation of the company's financial strength, earnings quality, and valuation. This is the "numbers" agent — every claim must be backed by specific metrics.

#### Inputs
All fields from `FINANCIALS_DATA`:
- `key_stats` — company metadata, market cap, enterprise value
- `valuation` — P/E, forward P/E, PEG, P/S, P/B, EV/EBITDA
- `profitability` — gross/operating/net margins, ROE, ROA, EPS (trailing + forward)
- `growth` — revenue YoY, earnings YoY, quarterly earnings growth
- `balance_sheet` — cash, debt, debt/equity, current ratio, quick ratio
- `cash_flow` — operating cash flow, free cash flow, capex
- `historical_income_statement` — 4 annual periods
- `historical_balance_sheet` — 4 annual periods
- `historical_cash_flow` — 4 annual periods
- `quarterly_income_statement` / `quarterly_balance_sheet` / `quarterly_cash_flow` — 3 recent quarters
- `analyst_consensus` — price targets, recommendation key

#### What It Analyzes
1. **Profitability** — EPS trend, gross/operating/net margins, ROE (>15% threshold), ROA
2. **Growth** — revenue YoY, EPS YoY (margin expansion check: EPS growing faster than revenue?), FCF trend, 4-year historical patterns
3. **Valuation** — trailing P/E, forward P/E (implied growth), PEG (<1.0 = undervalued heuristic), P/S, P/B, EV/EBITDA; assesses whether stock is "priced for perfection or pessimism"
4. **Balance Sheet** — D/E (>2x warrants scrutiny), current ratio, quick ratio, net debt vs. FCF (years to pay off debt), interest coverage
5. **Cash Flow Quality** — OCF vs. net income (OCF > net income = high-quality earnings), FCF generation, capex analysis (growth-driving vs. maintenance)
6. **Competitive Comparison** — contextualizes metrics vs. industry averages and at least 1–2 named peer companies
7. **Verdict** — financial health (Strong/Adequate/Weak), valuation (Undervalued/Fairly valued/Overvalued), earnings quality (High/Medium/Low), score /10

#### Output Section
`## Fundamental Analysis Report: [TICKER]` containing:
- Profitability Summary table with assessments
- Growth Analysis narrative
- Valuation Matrix (with sector average column)
- Balance Sheet Health
- Cash Flow Analysis
- Historical Trend Analysis (4-year summary)
- **Fundamental Verdict** with score, key strengths, key concerns

#### Critical Thinking Standards
- Flag unusual/one-time items
- Note if high growth justifies premium valuation
- Challenge metrics that seem too good (accounting red flags)
- Be explicit about missing or unreliable data
- Compare to named peer companies

---

### Agent 4 — Technical Analysis

**File**: `technical_analysis.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: `TECHNICALS_DATA` (from `calculate_technicals.py`) + `PRICE_DATA.recent_90d`

#### Purpose
Analyzes price action, chart structure, and technical indicators to determine entry timing and trend direction. Works entirely from computed indicators — does not use fundamental or news data.

#### Inputs
| Variable | Content |
|---|---|
| `TECHNICALS_DATA.trend` | SMA20/50/200, EMA12/26/50, ADX, Parabolic SAR, golden/death cross dates, trend signal |
| `TECHNICALS_DATA.momentum` | RSI(14), MACD line/signal/histogram, Stochastic %K/%D, MFI(14), divergence signals |
| `TECHNICALS_DATA.volatility` | Bollinger Bands (upper/mid/lower/width), ATR(14), 30-day historical volatility |
| `TECHNICALS_DATA.volume` | Current/avg 20d/50d volume, volume ratio, OBV, volume trend |
| `TECHNICALS_DATA.price_structure` | Key support/resistance levels, 52w high/low, Fibonacci retracement levels |
| `TECHNICALS_DATA.summary` | Overall technical score, signal detail, timing assessment |
| `PRICE_DATA.recent_90d` | Last 90 days of OHLCV data |

#### What It Analyzes
1. **Trend Analysis** — primary (SMA200), secondary (SMA50), short-term (SMA20) trends; MA alignment (bullish: SMA20 > SMA50 > SMA200); golden/death cross events; EMA confirmation
2. **Momentum** — RSI(14) with overbought/oversold levels + divergence; MACD line/signal/histogram with crossover events; Stochastic confirmation/contradiction of RSI
3. **Volatility** — Bollinger Band position (above upper = extended; below lower = oversold; band squeeze = pending breakout); ATR in dollar + % terms; historical volatility context
4. **Volume** — volume trend, up-day vs. down-day volume ratio, OBV (rising OBV + rising price = confirmation; falling OBV + rising price = divergence), volume spikes
5. **Price Structure** — support/resistance levels, Fibonacci retracement levels, chart pattern identification (10 named patterns: ascending/descending triangle, bull/bear flag, H&S / inverse H&S, cup and handle, double top/bottom, channel, range)
6. **Entry Timing Assessment** — evaluates if current setup is favorable for a new position; provides specific entry zone, stop-loss level, near-term targets

#### Output Section
`## Technical Analysis Report: [TICKER]` containing:
- Current Price Action summary
- Trend Analysis table (SMA20/50/200, cross signals, overall trend label)
- Momentum Analysis table (RSI, MACD, Stochastic)
- Volatility & Volume narrative
- Price Structure (key support/resistance, chart pattern)
- **Technical Verdict**: overall signal, entry timing, entry zone, stop-loss, price targets, score /10, key technical risks

#### Critical Thinking Standards
- Only call a chart pattern if clear and unambiguous — do not over-fit
- Note when indicators conflict with each other
- Highlight confirmation vs. divergence across indicators
- Always state timeframe context (short-term vs. medium-term)
- Acknowledge that technical signals are probabilistic, not certain

---

### Agent 5 — Analyst Sentiment

**File**: `analyst_sentiment.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: `FINANCIALS_DATA.analyst_consensus` (yfinance) + WebSearch

#### Purpose
Researches and synthesizes the views of Wall Street analysts and institutional investors. Goes beyond the raw yfinance consensus numbers to find individual analyst ratings, rating changes, the bull/bear split, and institutional activity — and applies critical analysis to detect potential bias.

#### Inputs
| Variable | Content |
|---|---|
| `FINANCIALS_DATA.analyst_consensus` | Mean/high/low price targets, recommendation key, number of analyst opinions |
| `FINANCIALS_DATA.key_stats.company_name` | For web search queries |
| `TICKER` | For web search queries |

#### What It Analyzes
1. **Analyst Ratings Research** — searches for individual analyst ratings (name, firm, rating, price target, date, key thesis)
2. **Consensus Summary** — aggregate consensus rating, mean/median price target, target range, implied upside/downside, bull vs. bear % split
3. **Recent Rating Changes** — upgrades, downgrades, initiations, price target revisions in the last 3 months (rating *changes* are more informative than absolute ratings)
4. **Institutional Research Themes** — extracts bull case / bear case arguments from research commentary; identifies what analysts are most uncertain about
5. **Cross-Validation & Bias Assessment** — consensus risk (no buyers left?), investment banking relationship bias, target price reliability, width of target range (= uncertainty proxy)
6. **Smart Money Activity** — 13F filings, notable hedge fund positions, insider buying/selling

#### Output Section
`## Analyst Sentiment Report: [TICKER]` containing:
- Consensus Overview table (rating, # analysts, target, range, current price, implied upside)
- Individual Analyst Views table (analyst, firm, rating, target, date, key argument)
- Recent Rating Changes
- Bull Case Arguments
- Bear Case Arguments
- Institutional / Hedge Fund Activity
- **Sentiment Verdict**: overall sentiment, conviction level, key uncertainty, contrarian flag, score /10

#### Critical Thinking Standards
- Never accept analyst consensus as gospel — it may already be priced in
- Identify investment banking relationship bias
- Note if targets were set before/after major market moves
- Flag wide target ranges (high uncertainty)
- Consider that upgrades near highs and downgrades near lows are lagging indicators

---

### Agent 6 — Risk Assessment

**File**: `risk_assessment.md`
**Runs in**: Stage 2 (parallel)
**Data sources**: All prior agent outputs (cross-agent synthesis)

#### Purpose
Systematically identifies, evaluates, and rates **all material risks** associated with investing in this stock. Unlike other agents, this one explicitly cross-references all prior agent outputs — it is the only Stage 2 agent with full visibility across the others.

#### Inputs
| Variable | Source |
|---|---|
| `MARKET_INTEL` | Market Intelligence Agent output |
| `MACRO` | Macro Economy Agent output |
| `FUNDAMENTALS` | Fundamental Analysis Agent output |
| `TECHNICALS` | Technical Analysis Agent output |
| `ANALYST_SENTIMENT` | Analyst Sentiment Agent output |

#### What It Analyzes
1. **Company-Specific Risks** — financial (revenue slowdown, leverage, margin pressure, FCF deterioration), business (customer concentration, supply chain, tech obsolescence, execution), management (instability, misaligned incentives, governance)
2. **Industry & Competitive Risks** — competitive disruption, industry cyclicality (near a peak?), regulatory/antitrust, technology disruption, pricing power erosion
3. **Market & Macro Risks** — interest rate sensitivity, recession cyclicality, currency exposure, liquidity (thin trading), sector rotation
4. **Event Risks** — earnings disappointment risk, litigation/regulatory investigations, geopolitical exposure, M&A (dilutive acquisition), insider selling
5. **Valuation Risk** — quantifies P/E compression downside ("if P/E contracts from X to Y, stock falls to $Z"), priced-for-perfection test, catalyst dependency
6. **Technical Risks** — ominous chart patterns (death cross, breakdown), downside technical targets, stop-loss scenario
7. **Risk Matrix** — compiles all risks with severity, probability, impact, and mitigation in a structured table

#### Output Section
`## Risk Assessment Report: [TICKER]` containing:
- Risk Matrix table (all risks with severity/probability/impact/mitigation)
- Company-Specific Risks (CRITICAL/HIGH/MEDIUM/LOW labeled)
- Industry & Competitive Risks
- Market & Macro Risks
- Event Risks
- Valuation Risk (downside scenario with specific prices)
- **Overall Risk Assessment**: risk level, top 3 risks, maximum drawdown scenario, risk/reward ratio, key risk to monitor

#### Critical Thinking Standards
- Do not minimize risks to support a bullish conclusion
- Distinguish already-priced vs. unpriced risks
- Consider second-order effects
- Include a tail risk scenario (low probability, high impact)
- Be explicit about near-term vs. long-term risks

---

### Agent 7 — Chief Investment Analyst (Synthesis)

**File**: `chief_analyst.md`
**Runs in**: Stage 3 (after all 6 agents complete)
**Data sources**: All 6 agent reports

#### Purpose
The final decision-maker. Synthesizes all prior agent reports into a coherent investment thesis and produces the complete Final Investment Report with a single, unambiguous recommendation. This agent acts as the hedge fund Investment Committee.

#### Inputs
| Variable | Source |
|---|---|
| `MARKET_INTEL_REPORT` | Market Intelligence Agent markdown output |
| `MACRO_REPORT` | Macro Economy Agent markdown output |
| `FUNDAMENTAL_REPORT` | Fundamental Analysis Agent markdown output |
| `TECHNICAL_REPORT` | Technical Analysis Agent markdown output |
| `SENTIMENT_REPORT` | Analyst Sentiment Agent markdown output |
| `RISK_REPORT` | Risk Assessment Agent markdown output |

#### Decision Framework (Weighted)
| Dimension | Weight | Source Agent |
|---|---|---|
| Business Quality & Moat | 25% | Market Intelligence |
| Financial Strength & Valuation | 25% | Fundamental Analysis |
| Macro Environment | 15% | Macro Economy |
| Technical Entry Timing | 15% | Technical Analysis |
| Analyst & Market Sentiment | 10% | Analyst Sentiment |
| Risk Factors | 10% | Risk Assessment |

#### What It Does
1. **Investment Thesis Construction** — core bull case (2–3 sentences), bear case (2–3 sentences), and "why now" timing rationale
2. **Cross-Agent Validation** — identifies where agents agree (conviction), where they disagree (uncertainty), and any deal-breaker red flags
3. **Scenario Analysis** — three explicit scenarios with probabilities:
   - Bull Case (X% probability) → price target + timeframe
   - Base Case (X% probability) → price target + timeframe
   - Bear Case (X% probability) → price target + timeframe
4. **Final Recommendation** — one of four outcomes:
   - **STRONG BUY**: Exceptional opportunity — multiple catalysts, strong fundamentals, favorable technicals, low risk
   - **BUY**: Good opportunity — clear thesis, favorable risk/reward
   - **HOLD / WAIT**: Mixed signals or rich valuation — not compelling enough to act
   - **AVOID**: Weak thesis, unfavorable risk/reward, too many red flags
5. **Actionable Trade Parameters** — entry zone, position sizing (Full/Half/Starter), stop-loss, near-term target (3–6 months), 12-month target, time horizon, key catalysts to watch, conditions that would change the recommendation

#### Output
The complete **Final Investment Report** in markdown, containing all 10 sections:
1. Executive Summary
2. Company Overview
3. Industry Analysis
4. Macro Environment
5. Fundamental Analysis
6. Technical Analysis
7. Analyst Sentiment
8. Risk Analysis
9. Investment Thesis (Bull/Base/Bear scenarios)
10. Final Recommendation (with full trade parameters table)

#### Critical Thinking Standards
- Recommendation must be supported by **multiple converging signals**, not a single indicator
- Explicitly acknowledge the strongest counter-argument to the recommendation
- Do not be overconfident — reflect genuine uncertainty in probability assignments
- If evidence is genuinely mixed, recommend HOLD rather than forcing a direction
- Report must read like an institutional research report, not a promotional piece
- Every claim must be traceable back to data from the agent reports

---

## Agent Data Flow

```
fetch_financials.py ──────────────────────────────────────────────────────┐
                          ┌──────────────────────────────────┐            │
                          │  FINANCIALS_DATA                  │            │
                          └──┬──────────────────────────────┘            │
                             │                                            │
                             ├──► Fundamental Analysis Agent             │
                             ├──► Analyst Sentiment Agent                │
                             └──► Macro Economy Agent (sector/industry)  │
                                                                         │
fetch_news.py ────────────────────────────────────────────────────────┐  │
                          ┌──────────────────────────────────┐        │  │
                          │  NEWS_DATA                        │        │  │
                          └──┬──────────────────────────────┘        │  │
                             └──► Market Intelligence Agent           │  │
                                                                      │  │
calculate_technicals.py ─────────────────────────────────────────┐   │  │
                          ┌──────────────────────────────────┐   │   │  │
                          │  TECHNICALS_DATA                  │   │   │  │
                          └──┬──────────────────────────────┘   │   │  │
                             └──► Technical Analysis Agent       │   │  │
                                                                  │   │  │
fetch_price_data.py ──────────────────────────────────────────┐  │   │  │
                          ┌──────────────────────────────────┐ │  │   │  │
                          │  PRICE_DATA                       │ │  │   │  │
                          └──┬──────────────────────────────┘ │  │   │  │
                             └──► Technical Analysis Agent     │  │   │  │
                                                               │  │   │  │
All 5 agent outputs ──────────────────────────────────────────┘  │   │  │
    └──► Risk Assessment Agent ◄────────────────────────────────┘   │  │
                                                                      │  │
All 6 agent reports ──────────────────────────────────────────────────┘  │
    └──► Chief Analyst ◄──────────────────────────────────────────────────┘
              │
              ▼
    reports/{TICKER}_{DATE}.md
```

---

## Adding a New Agent

To add a new agent to the pipeline:

1. Create a new `.md` file in this folder following the structure:
   ```markdown
   # [Agent Name] Agent
   ## Role
   ## Input Data
   ## Your Tasks
   ## Output Format
   ## Critical Thinking Requirements
   ```

2. Add a new step in `.claude/commands/analyze-stock.md` under Step 2, referencing the agent file path

3. Pass the new agent's output to the Chief Analyst in Step 3

4. Update the Chief Analyst's decision framework weights if the new dimension should be scored

---

## File Reference

| File | Agent | Stage | Data Source |
|---|---|---|---|
| `market_intelligence.md` | Market Intelligence | 2 (parallel) | NEWS_DATA + WebSearch + RSS |
| `macro_economy.md` | Macro Economy | 2 (parallel) | WebSearch only |
| `fundamental_analysis.md` | Fundamental Analysis | 2 (parallel) | FINANCIALS_DATA |
| `technical_analysis.md` | Technical Analysis | 2 (parallel) | TECHNICALS_DATA + PRICE_DATA |
| `analyst_sentiment.md` | Analyst Sentiment | 2 (parallel) | analyst_consensus + WebSearch |
| `risk_assessment.md` | Risk Assessment | 2 (parallel) | All prior agent outputs |
| `chief_analyst.md` | Chief Investment Analyst | 3 (synthesis) | All 6 agent reports |