You are the orchestrator of the **Theater Baseline Update System**. Your job is to research each defense company's real-world theater exposure using live web data and update the `theater_baseline` scores in `defense_universe_config.py` with evidence-backed values.

## Input
The user has provided: $ARGUMENTS

Parse optional flags:
- `--batch X` — update only batch X (A-F). Default: all batches.
- `--dry-run` — print proposed changes without writing to the file.

**PROJECT_DIR** = `/Users/shayeyal/PycharmProjects/Stock_Analysis_System`
**PYTHON** = `/Users/shayeyal/PycharmProjects/Stock_Analysis_System/.venv/bin/python`
**CONFIG_FILE** = `$PROJECT_DIR/agents/defense-sector/tools/defense_universe_config.py`
**TODAY** = today's date in YYYY-MM-DD format

---

## Background: What Is theater_baseline?

In `defense_universe_config.py`, every company in the UNIVERSE dict has a `theater_baseline` entry:

```python
"LMT": {
    ...
    "theater_baseline": {"ME": 0.8, "EE": 0.7, "IP": 0.7, "KP": 0.4, "Sahel": 0.1},
},
```

These scores (0.0–1.0) represent how much **demand** each geopolitical theater generates for that company's products and services. They are used in the TWES (Theater-Weighted Exposure Score) multiplier during portfolio scoring.

The **5 theaters** are:
- **ME** = Middle East (precision munitions, missile defense, FMS to Israel/Gulf states, Iron Dome replenishment)
- **EE** = Eastern Europe (Ukraine/Russia war, NATO rearmament, artillery, air defense, armor, drones)
- **IP** = Indo-Pacific (Taiwan deterrence, AUKUS, naval platforms, long-range strike, submarines)
- **KP** = Korean Peninsula (DPRK provocations, ROK modernization, THAAD, K-defense exports)
- **Sahel** = Sahel/Africa (CT operations, SOF equipment, light ISR, training/simulation)

**Scoring rubric** (apply consistently across all companies):
| Score | Meaning |
|-------|---------|
| 0.0–0.1 | No exposure — no relevant products or contracts in this theater |
| 0.1–0.3 | Peripheral — adjacent products (sustainment, training) with minor theater footprint |
| 0.3–0.5 | Moderate — some theater-relevant contracts but not a primary supplier |
| 0.5–0.7 | Strong — key programs directly tied to theater demand drivers |
| 0.7–0.9 | High — major contracts, FMS wins, or primary supplier for theater's top capability needs |
| 0.9–1.0 | Critical — the defining supplier for this theater; demand collapse here = major revenue risk |

---

## Stage 0: Load Configuration

Run:
```bash
cd $PROJECT_DIR && $PYTHON agents/defense-sector/tools/defense_universe_config.py --json
```

Store the output as `CONFIG`. Extract:
- Full UNIVERSE dict (all companies with current theater_baseline values)
- Batch composition (A-F)

Confirm to user: "Loaded XX companies across 6 batches. Starting theater baseline research..."

---

## Stage 1: Parallel Batch Research

Launch **parallel Task agents** (subagent_type: "general-purpose"), one per batch being processed.

If `--batch X` specified, launch only 1 agent for that batch.
If no batch specified, launch all 6 agents simultaneously.

### Instructions for EACH batch research agent

Provide the agent with:
1. The list of companies in its batch (ticker, name, country, current theater_baseline)
2. The scoring rubric above
3. The research protocol below

**Research Protocol (per company):**

For each company in the batch, run WebSearch queries to gather current intelligence:

1. **Contract & FMS search**: `"[Company name]" defense contract [2025 OR 2026] [theater region keywords]`
   - ME keywords: Israel, Saudi Arabia, UAE, Qatar, Jordan, FMS Middle East, Iron Dome, Patriot, Houthi
   - EE keywords: Ukraine, NATO, Poland, Germany rearmament, artillery, HIMARS, air defense Eastern Europe
   - IP keywords: Taiwan, AUKUS, Japan rearmament, Philippines, South China Sea, submarine, INDOPACOM
   - KP keywords: South Korea, ROK, DPRK, Hanwha, Korean defense, THAAD, K-defense
   - Sahel keywords: West Africa, Somalia, SOCOM, counterterrorism, light attack

2. **Earnings/investor search**: `"[Ticker]" earnings theater exposure international 2025 2026`

3. **News search**: `"[Company name]" [theater country] contract award 2025`

**Scoring logic:**
- Recent contract wins in theater = +0.1 to +0.2 vs baseline
- No contracts found but core products are theater-relevant = maintain or slight adjustment
- Competitor wins major theater contract = possible -0.1
- Company explicitly exited theater market = significant reduction
- Israeli companies: ME baseline always ≥ 0.5 unless pure civilian pivot

**Output format (strict JSON):**

```json
{
  "batch": "A",
  "updated_date": "YYYY-MM-DD",
  "companies": {
    "LMT": {
      "theater_baseline": {"ME": 0.85, "EE": 0.75, "IP": 0.70, "KP": 0.40, "Sahel": 0.10},
      "citation": "LMT won $3.2B Patriot PAC-3 FMS for Poland Dec 2025; F-35 deliveries to Israel ongoing",
      "delta": {"ME": "+0.05", "EE": "+0.05", "IP": "0", "KP": "0", "Sahel": "0"},
      "confidence": "high"
    },
    "RTX": {
      "theater_baseline": {"ME": 0.90, "EE": 0.80, "IP": 0.60, "KP": 0.50, "Sahel": 0.15},
      "citation": "RTX Patriot interceptor production surge for Ukraine/Poland; Stinger MANPADS export ongoing",
      "delta": {"ME": "0", "EE": "0", "IP": "0", "KP": "0", "Sahel": "0"},
      "confidence": "high"
    }
  }
}
```

Rules for the research agent:
- Every score MUST be grounded in a search result or a well-established product fact
- If web search returns no useful results for a company, keep current score and mark confidence "low"
- Do NOT invent contracts or citations
- Citation must be ≤ 15 words: event + date is sufficient
- Confidence levels: "high" (recent direct evidence), "medium" (product fit inference), "low" (no new data found)

### Batch Assignments

- **Batch A** (9 companies): LMT, RTX, NOC, GD, LHX, BA, HII, GE, TXT — US Large-Cap
- **Batch B** (13 companies): PLTR, LDOS, BAH, CACI, KTOS, AVAV, TDG, BWXT, CW, DRS, HWM, HEI, PSN — US Mid-Cap
- **Batch C** (8 companies): MRCY, MOG.A, TDY, RKLB, KRMN, NPK, VVX, RCAT — US Small-Cap
- **Batch D** (10 companies): ESLT, SMSH, ARYT, ORBI, ISI, AXN, ISHI, ASHO, BSEN, FBRT — Israel
- **Batch E** (15 companies): RHM, HAG, MTX, BA.L, RR.L, BAB.L, QQ.L, CHG.L, AIR.PA, SAF.PA, AM.PA, HO.PA, LDO.MI, SAAB-B, KOG — Europe
- **Batch F** (9 companies): HANWHA_AD, HANWHA_OC, HYUNDAI_ROT, LIG_NEX1, KOREAN_AIR, MHI, KHI, IHI, CAE — Asia-Pacific

Collect all batch agent outputs. Merge into a single dict keyed by company ticker/key.

---

## Stage 2: Apply Updates to defense_universe_config.py

**If `--dry-run` flag**: print the proposed changes as a table and stop. Do not modify any files.

**Otherwise**, update `$CONFIG_FILE` for each company:

### Update procedure

Read the full content of `$CONFIG_FILE`.

For each company in the merged research output:

1. Find the company's `theater_baseline` line in the file. It matches the pattern:
   ```
   "theater_baseline": {"ME": X.X, "EE": X.X, "IP": X.X, "KP": X.X, "Sahel": X.X},
   ```
   preceded by the company key (e.g., `"LMT": {`).

2. Replace it with the new values AND append an inline comment:
   ```python
   "theater_baseline": {"ME": 0.85, "EE": 0.75, "IP": 0.70, "KP": 0.40, "Sahel": 0.10},  # Updated YYYY-MM-DD: LMT won $3.2B Patriot PAC-3 FMS Poland
   ```

3. If the line already has an existing `# Updated` comment, replace it entirely.

Use the Edit tool to apply each change. Process companies one at a time.

**Only update a company's scores if at least one theater delta ≠ 0 OR if confidence is "high".**
Do not change scores when confidence is "low" and no meaningful new information was found.

---

## Stage 3: Verify File Integrity

After all updates are applied, verify the file is valid Python:

```bash
cd $PROJECT_DIR && $PYTHON -c "
from agents.defense_sector.tools.defense_universe_config import UNIVERSE, THEATERS
print(f'OK: {len(UNIVERSE)} companies loaded, {len(THEATERS)} theaters')
"
```

If this fails with an ImportError or SyntaxError:
1. Report the exact error to the user
2. Do NOT attempt further updates
3. Ask the user to review the file manually

If it succeeds, continue to Stage 4.

---

## Stage 4: Generate Delta Report

Save a report to: `$PROJECT_DIR/reports/theater_baseline_update_{TODAY}.md`

Report structure:

```markdown
# Theater Baseline Update — {TODAY}

## Summary
- Companies researched: XX
- Companies updated: XX (score changed in ≥1 theater)
- Companies unchanged: XX (no new evidence found)
- Batches processed: A, B, C, D, E, F (or subset)

## Significant Changes (|delta| ≥ 0.15)

| Company | Theater | Old | New | Delta | Evidence |
|---------|---------|-----|-----|-------|----------|
| LMT | EE | 0.70 | 0.85 | +0.15 | NATO artillery contract Dec 2025 |
| ...     | ...     | ... | ... | ...   | ...      |

## Theater-Level Observations

### Middle East (ME)
[1-3 sentences on overall ME trend across universe]

### Eastern Europe (EE)
[1-3 sentences on EE — Ukraine war status, NATO procurement]

### Indo-Pacific (IP)
[1-3 sentences on IP — AUKUS, Taiwan, Japan rearmament]

### Korean Peninsula (KP)
[1-3 sentences on KP — ROK modernization, K-defense exports]

### Sahel/Africa (Sahel)
[1-3 sentences on Sahel — CT posture, proxy competition]

## Low-Confidence Companies
Companies where no current web data was found — scores kept unchanged:
- [TICKER]: [Company name] — recommend manual review

## Next Update Recommended
[DATE + 30 days from today]
```

---

## Stage 5: Summary to User

```
Theater Baseline Update Complete — {TODAY}

Universe processed: XX companies across batches [X, X, ...]
Updated: XX companies (score changed in ≥1 theater)
Unchanged: XX companies (no new evidence / low confidence)
Significant moves (|delta| ≥ 0.15): XX

Top movers:
  UP:   [TICKER] [Theater] +X.XX — [reason]
  DOWN: [TICKER] [Theater] -X.XX — [reason]

Config file updated: agents/defense-sector/tools/defense_universe_config.py ✓
Report saved: reports/theater_baseline_update_{TODAY}.md
```

---

## Important Notes

- **Do NOT modify** any other section of `defense_universe_config.py` (DIMENSION_WEIGHTS, HARD_GATES, THEATERS, PORTFOLIO_CONSTRAINTS, etc.)
- **Do NOT add or remove companies** from UNIVERSE
- **Score bounds**: All values must stay in [0.0, 1.0] — clamp if research suggests out-of-range
- **Israeli companies (Batch D)**: ME baseline should almost never fall below 0.5 given domestic demand
- **Parallel agents are required** for full-universe runs — do not run batch research sequentially
- **Context per agent**: Each batch agent receives only its batch's data, not the full universe
- **Runtime**: Single batch ~5 min, full universe ~15 min
- **Idempotent**: Running again on same day overwrites that day's report and updates file again with fresh research
