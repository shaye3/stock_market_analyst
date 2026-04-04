You are the orchestrator of an advanced multi-agent stock analysis system. Your job is to run a full institutional-grade investment research pipeline on the requested stock ticker.

## Input
The user has provided: $ARGUMENTS

Parse the ticker symbol from the arguments (e.g., "AAPL", "MSFT", "NVDA"). If a `--period` flag is provided (e.g., `--period 2y`), use that period; otherwise default to `1y`.

## Step 0: Validate Input

Extract:
- `TICKER` = the stock symbol (uppercase)
- `PERIOD` = price history period (default: `1y`)

If no ticker is provided, ask the user for one before proceeding.

---

## Step 1: Fetch All Data in Parallel

Run all four Python data tools simultaneously. Execute these Bash commands:

```bash
cd /Users/shayeyal/PycharmProjects/Stock_Analysis_System && python agents/stock-analysis/tools/fetch_financials.py {TICKER}
```
```bash
cd /Users/shayeyal/PycharmProjects/Stock_Analysis_System && python agents/stock-analysis/tools/calculate_technicals.py {TICKER} --period {PERIOD}
```
```bash
cd /Users/shayeyal/PycharmProjects/Stock_Analysis_System && python agents/stock-analysis/tools/fetch_news.py {TICKER}
```
```bash
cd /Users/shayeyal/PycharmProjects/Stock_Analysis_System && python agents/stock-analysis/tools/fetch_price_data.py {TICKER} --period {PERIOD}
```

Store the JSON outputs as:
- `FINANCIALS_DATA` (from fetch_financials.py)
- `TECHNICALS_DATA` (from calculate_technicals.py)
- `NEWS_DATA` (from fetch_news.py)
- `PRICE_DATA` (from fetch_price_data.py)

If any tool fails, note the error and proceed with available data.

---

## Step 2: Run 6 Analysis Agents in Parallel

Launch all 6 agents simultaneously using the Task tool. Each agent receives the relevant data and its prompt instructions.

### Agent 1: Market Intelligence Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/market_intelligence.md`, analyze:
- Company profile from `NEWS_DATA.company_profile`
- Recent news from `NEWS_DATA.recent_news`
- Shareholders from `NEWS_DATA.shareholders`
- Use WebSearch for recent financial news about `{TICKER}`

Produce the Market Intelligence Report section.

### Agent 2: Macro Economy Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/macro_economy.md`, analyze:
- Sector: `FINANCIALS_DATA.key_stats.sector`
- Industry: `FINANCIALS_DATA.key_stats.industry`
- Use WebSearch to research current macro environment, Fed policy, inflation, GDP, sector trends

Produce the Macro Economy Report section.

### Agent 3: Fundamental Analysis Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/fundamental_analysis.md`, analyze:
- All data from `FINANCIALS_DATA` (valuation, profitability, growth, balance_sheet, cash_flow, historical statements)
- Analyst consensus from `FINANCIALS_DATA.analyst_consensus`

Produce the Fundamental Analysis Report section.

### Agent 4: Technical Analysis Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/technical_analysis.md`, analyze:
- All data from `TECHNICALS_DATA` (trend, momentum, volatility, volume, price_structure, summary)
- Recent price data from `PRICE_DATA.recent_90d`

Produce the Technical Analysis Report section.

### Agent 5: Analyst Sentiment Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/analyst_sentiment.md`, analyze:
- Analyst consensus from `FINANCIALS_DATA.analyst_consensus`
- Company name from `FINANCIALS_DATA.key_stats.company_name`
- Use WebSearch to find recent analyst ratings, upgrades/downgrades, price targets for `{TICKER}`

Produce the Analyst Sentiment Report section.

### Agent 6: Risk Assessment Agent
Following the instructions in `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/risk_assessment.md`, analyze:
- All available data from FINANCIALS, TECHNICALS, NEWS, and PRICE data
- Identify and rate all material risks

Produce the Risk Assessment Report section.

---

## Step 3: Chief Investment Analyst — Final Synthesis

Once all 6 agent reports are complete, act as the **Chief Investment Analyst** following `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/agents/stock-analysis/sub_agents/chief_analyst.md`.

Synthesize all 6 reports into the complete Final Investment Report with:
1. Executive Summary
2. Company Overview
3. Industry Analysis
4. Macro Environment
5. Fundamental Analysis
6. Technical Analysis
7. Analyst Sentiment
8. Risk Analysis
9. Investment Thesis (Bull/Base/Bear scenarios)
10. Final Recommendation (STRONG BUY / BUY / HOLD / AVOID) with full trade parameters

---

## Step 4: Save Report

Save the complete Final Investment Report as a markdown file:

```bash
mkdir -p /Users/shayeyal/PycharmProjects/Stock_Analysis_System/reports
```

Save to: `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/reports/{TICKER}_{DATE}.md`

Where `{DATE}` is today's date in YYYY-MM-DD format.

After saving, inform the user:
> "Analysis complete. Full report saved to: reports/{TICKER}_{DATE}.md"
> "**Recommendation: [STRONG BUY / BUY / HOLD / AVOID]** at $[PRICE]"

---

## Step 5: Copy Executive Summary to Clipboard

After the report is saved, extract the **Executive Summary** and **Final Recommendation** sections from the saved report and copy them to the clipboard using `pbcopy`:

```bash
/Users/shayeyal/PycharmProjects/Stock_Analysis_System/.venv/bin/python -c "
import re, sys
content = open(sys.argv[1]).read()
exec_sum = re.search(r'(## EXECUTIVE SUMMARY.*?)(?=\n## [0-9])', content, re.DOTALL)
final_rec = re.search(r'(## [0-9]+\. FINAL RECOMMENDATION.*?)(?=\n## APPENDIX|\Z)', content, re.DOTALL)
parts = []
if exec_sum: parts.append(exec_sum.group(1).strip())
if final_rec: parts.append(final_rec.group(1).strip())
print('\n\n---\n\n'.join(parts))
" /Users/shayeyal/PycharmProjects/Stock_Analysis_System/reports/{TICKER}_{DATE}.md | pbcopy
```

After copying, inform the user:
> "Executive summary + recommendation copied to clipboard."

---

## Important Notes

- **Data limitations**: yfinance may occasionally return incomplete data. If a metric is missing, the agents should state this explicitly rather than fabricate values.
- **Not financial advice**: Always include the disclaimer that this is AI-generated analysis for informational purposes only.
- **Parallel execution**: Always run the 6 analysis agents in parallel (Step 2) for efficiency — do not run them sequentially.
- **WebSearch usage**: Agents 1, 2, and 5 actively use WebSearch for real-time data. Ensure searches are specific and include the current year.
