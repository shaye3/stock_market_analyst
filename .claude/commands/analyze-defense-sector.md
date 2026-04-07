You are the orchestrator of the **Defense Sector Multi-Agent Analysis System**. Your job is to run a full institutional-grade sector-wide analysis of 50+ defense companies across 5 geopolitical theaters and 10 warfare domains, constructing a constrained 12-15 position model portfolio.

## Input
The user has provided: $ARGUMENTS

Parse optional flags:
- `--batch X` — analyze only batch X (A-F) instead of full universe. Default: all batches.
- `--compare-previous` — compare results against the most recent prior report in reports/.

If no arguments, run the full universe analysis.

**PROJECT_DIR** = `/Users/shayeyal/PycharmProjects/Stock_Analysis_System`
**PYTHON** = `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/.venv/bin/python`
**TODAY** = today's date in YYYY-MM-DD format

---

## Stage 0: Load Configuration (~5s)

Run:
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/defense_universe_config.py --json
```

Store the output as `CONFIG`. Note:
- Total universe size
- Batch composition
- Scoring weights
- Hard gate thresholds

Confirm to the user: "Loaded defense universe config: XX companies across 6 batches."

---

## Stage 1: Batch Data Fetch (~1-2 min)

Run these 2 commands in **parallel** via Bash:

### 1a. Financials
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/fetch_defense_universe.py --all > /tmp/defense_financials.json 2>/dev/null
```
(If `--batch X` was specified, use `--batch X` instead of `--all`)

### 1b. Technicals
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/fetch_defense_technicals.py --all > /tmp/defense_technicals.json 2>/dev/null
```
(If `--batch X` was specified, use `--batch X` instead of `--all`)

After both complete, read and summarize:
- How many companies returned valid data
- Any tickers with missing data (note for later estimation)

---

## Stage 2: Contextual Research (~3-5 min)

Launch **4 parallel Task agents** (subagent_type: "general-purpose"):

### Agent 1: Theater Intelligence
Read the agent prompt at `$PROJECT_DIR/agents/defense-sector/sub_agents/theater_intelligence.md`.
Instruct the agent to:
- Assess all 5 theaters using WebSearch for latest developments
- Output theater demand weights as JSON: `{"ME": 0.XX, "EE": 0.XX, "IP": 0.XX, "KP": 0.XX, "Sahel": 0.XX}`
- Output the full theater assessment per the prompt format

### Agent 2: Defense Budget & Macro
Read the agent prompt at `$PROJECT_DIR/agents/defense-sector/sub_agents/defense_budget_macro.md`.
Instruct the agent to:
- Research US, European, Asia-Pacific defense budgets using WebSearch
- Assess industrial base health and macro conditions
- Output the budget/macro assessment per the prompt format

### Agent 3: Domain Analysis
Read the agent prompt at `$PROJECT_DIR/agents/defense-sector/sub_agents/domain_analysis.md`.
Instruct the agent to:
- Analyze all 10 warfare domains using WebSearch
- Map top companies per domain from the universe list
- Output the domain summary matrix and deep dives per the prompt format

### Agent 4: Media Intelligence
Launch a general-purpose agent to:
- Search for the latest defense contract awards in the last 30 days
- Search for recent defense sector earnings surprises
- Search for major FMS (Foreign Military Sales) notifications
- Compile a list of significant recent events by company ticker

Store all 4 agent outputs.

---

## Stage 3: Per-Company Scoring (~5-8 min)

This is the most intensive stage. Launch **6 parallel Task agents** (subagent_type: "general-purpose"), one per batch.

For each batch agent, provide:
1. The agent prompt from `$PROJECT_DIR/agents/defense-sector/sub_agents/defense_company_scorer.md`
2. The list of companies in that batch (from CONFIG)
3. The **financial data** for those companies (from Stage 1 financials JSON — extract the relevant tickers)
4. The **technical data** for those companies (from Stage 1 technicals JSON)
5. The **theater intelligence** output (from Stage 2 Agent 1)
6. The **domain analysis** output (from Stage 2 Agent 3)
7. The **budget/macro** context (from Stage 2 Agent 2)

Each agent must output dimension scores for every company in its batch in the JSON format specified in the scorer prompt.

**CRITICAL**: Instruct each batch agent to use the **company_key** (e.g., `"LMT"`, `"RHM"`, `"HANWHA_AD"`, `"BA.L"`) as the JSON key in their Batch Summary output — NOT the yf_ticker (e.g., not `"RHM.DE"` or `"012450.KS"`). The scoring engine (`calculate_defense_scoring.py`) looks up company_key in the universe config to resolve tickers and theater baselines.

### Batch Assignment:
- **Batch A**: US Large-Cap (9 companies) — LMT, RTX, NOC, GD, LHX, BA, HII, GE, TXT
- **Batch B**: US Mid-Cap (13 companies) — PLTR, LDOS, BAH, CACI, KTOS, AVAV, TDG, BWXT, CW, DRS, HWM, HEI, PSN
- **Batch C**: US Small-Cap (8 companies) — MRCY, MOG.A, TDY, RKLB, KRMN, NPK, VVX, RCAT
- **Batch D**: Israel (10 companies) — ESLT, SMSH, ARYT, ORBI, ISI, AXN, ISHI, ASHO, BSEN, FBRT
- **Batch E**: Europe (15 companies) — RHM, HAG, MTX, BA.L, RR.L, BAB.L, QQ.L, CHG.L, AIR.PA, SAF.PA, AM.PA, HO.PA, LDO.MI, SAAB-B, KOG
- **Batch F**: Asia-Pacific (9 companies) — Korean, Japanese, Canadian tickers

If `--batch X` was specified, only launch 1 scoring agent for that batch.

Collect all 6 batch scoring outputs and merge into a single dimension scores dictionary.

---

## Stage 4: Score Computation (~30s)

Write the merged dimension scores to `/tmp/defense_scores.json`.

Extract theater weights from the Stage 2 theater intelligence output and write to `/tmp/theater_weights.json`. The theater intelligence agent outputs a JSON block in this format:
```json
{"ME": 0.XX, "EE": 0.XX, "IP": 0.XX, "KP": 0.XX, "Sahel": 0.XX}
```
Parse that JSON block from the theater agent output and write only the dict (5 keys) to `/tmp/theater_weights.json`. Weights must be floats summing to approximately 1.0.

Run:
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/calculate_defense_scoring.py \
    --scores /tmp/defense_scores.json \
    --financials /tmp/defense_financials.json \
    --theater-weights /tmp/theater_weights.json > /tmp/defense_rankings.json
```

Read the output and report:
- Total companies scored
- Companies passing vs. excluded by hard gates
- Top 10 ranked companies with scores

---

## Stage 5: Portfolio Construction (~2-3 min)

Launch **1 Task agent** (subagent_type: "general-purpose"):

Provide:
1. The agent prompt from `$PROJECT_DIR/agents/defense-sector/sub_agents/portfolio_construction.md`
2. The full rankings from Stage 4
3. Theater intelligence and domain analysis from Stage 2
4. Financial and technical data from Stage 1
5. Portfolio constraints from CONFIG

The agent must output:
- The 12-15 position portfolio with weights and tranches
- Constraint validation results
- Scenario analysis
- The portfolio as JSON for metrics computation

After receiving the portfolio, write it to `/tmp/defense_portfolio.json` and run:
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/calculate_portfolio_metrics.py \
    --portfolio /tmp/defense_portfolio.json \
    --technicals /tmp/defense_technicals.json
```

Verify all constraints pass. If not, feed violations back to the portfolio construction agent to adjust.

---

## Stage 6: Report Synthesis (~3-5 min)

Launch **1 Task agent** (subagent_type: "general-purpose"):

Provide:
1. The agent prompt from `$PROJECT_DIR/agents/defense-sector/sub_agents/defense_chief_analyst.md`
2. **ALL** previous stage outputs:
   - Theater intelligence
   - Budget/macro assessment
   - Domain analysis
   - Media intelligence
   - All company scores (merged)
   - Rankings with hard gate exclusions
   - Portfolio composition and metrics
   - Constraint validation
3. Today's date

The agent must generate the complete ~800-line defense sector analysis report per the chief analyst prompt.

---

## Stage 7: Save Report

Save the complete report:

```bash
mkdir -p $PROJECT_DIR/reports
```

Save to: `$PROJECT_DIR/reports/defense_sector_analysis_{TODAY}.md`

---

## Stage 8: Summary to User

After saving, report:

```
Defense Sector Analysis Complete — {TODAY}

Universe: XX companies analyzed across 6 batches
Scored: XX companies (XX excluded by hard gates)
Portfolio: XX positions, weighted beta X.XX

Top 3 Picks:
1. [TICKER] — [Name] — XX% weight — [1-line thesis]
2. [TICKER] — [Name] — XX% weight — [1-line thesis]
3. [TICKER] — [Name] — XX% weight — [1-line thesis]

Report saved to: reports/defense_sector_analysis_{TODAY}.md
```

If `--compare-previous` was specified, also compare scores against the most recent prior report in `reports/defense_sector_analysis_*.md` and note:
- Companies that moved up/down significantly in ranking
- New portfolio entries or exits
- Theater weight changes

---

## Important Notes

- **Parallel execution is critical** — Stages 2, 3 MUST run agents in parallel. Do not run them sequentially.
- **Data quality**: Some international tickers (especially TASE) may lack yfinance data. Note these and score from web research.
- **Context management**: The scoring agents are the most context-intensive. Provide them only the data for their specific batch.
- **Runtime**: Full universe analysis takes 15-25 minutes. Single batch takes 5-10 minutes.
- **Idempotent**: Running twice on the same day will overwrite the report. Previous reports are preserved by date.
