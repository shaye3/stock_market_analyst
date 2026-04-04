# Defense Sector Deep Analysis — Sector Orchestrator Skill

## Objective

Conduct a **data-driven investment analysis** to identify the **top publicly traded defense companies** most likely to generate **alpha vs. the ITA (iShares U.S. Aerospace & Defense ETF)** across three investment horizons following the 2026 U.S.–Israel–Iran conflict.

**Output: Three model portfolios** — Near-term (0–6 months), Medium-term (6–18 months), Long-term (18–36 months).

Every claim must tie to **contracts, backlog, production capacity, procurement signals, or verifiable financial data**. No narrative-only conclusions.

---

## Part 1: Conflict Phase Model

The analysis must explicitly model **which companies win in which phase**. In addition to the direct U.S.–Israel–Iran bilateral conflict, model **proxy escalation vectors** as independent demand streams — they may persist after primary-conflict resolution and should not be collapsed into a single phase signal.

### Phase 1: Active Combat & Immediate Aftermath (0–6 months)
- Munition consumption surge → emergency procurement
- Winners: Existing production lines, sole-source suppliers, ISR/targeting platforms
- Key signal: Supplemental budget requests, emergency FMS notifications

**Proxy escalation vectors (model separately from bilateral conflict):**
| Proxy Actor | Theater | Primary Demand Signal | Key Beneficiary Domain |
|-------------|---------|----------------------|------------------------|
| Houthi (continued) | Red Sea / Gulf of Aden | Naval escort ops, ship-defense interceptor burn, mine counter-measure | Naval & Maritime, Air Defense |
| Hezbollah (northern front) | Lebanon/Israel border | Iron Dome/David's Sling Tamir consumption, UAV attrition, artillery | Interceptors, Munitions |
| Iraqi militia | Iraq/Syria (force protection) | Counter-rocket/mortar (C-RAM), MRAP sustainment, short-range AD | Short-Range Air Defense, Armor |

### Phase 2: Replenishment Cycle (6–18 months)
- Backlog conversion → revenue acceleration
- Winners: High-backlog companies with production scalability, Tier-2 bottleneck holders
- Key signal: Multi-year contract awards, production rate increases, LRIP-to-FRP transitions
- **Proxy persistence factor**: Model whether Houthi/Hezbollah operations continue at elevated tempo — affects duration of Phase 1 demand overlap into Phase 2. If proxies remain active, treat Phase 1 demand signals as additive to Phase 2 replenishment.

### Phase 3: Structural Arms Race & Modernization (18–36 months)
- Budget expansion → new program starts, allied procurement waves
- Winners: Next-gen platform developers, directed energy, autonomous systems, cyber
- Key signal: NATO spending commitments, Gulf FMS approvals, FYDP budget growth
- **Structural proxy premium**: Persistent Iranian proxy network → structural increase in demand for layered defense systems. This is not episodic replenishment but a reclassification of threat environment by defense planners — expect budget baseline shifts, not one-time supplementals.

---

## Part 2: Full-Spectrum Warfare Domains

Analyze each domain independently. For each, identify the **top 3 companies** and map the **demand drivers**:

### 1. Air Defense & Missile Systems
- Interceptors: PAC-3, Tamir, SM-6, Arrow, David's Sling, THAAD
- Precision-guided munitions: JDAM, SDB, JASSM, LRASM
- Directed energy: laser systems, high-power microwave
- **Cost asymmetry**: Quantify cost-per-interceptor vs. cost-per-threat (e.g., Tamir ~$50K vs. Houthi drone ~$2K)

### 2. Cyber & Electronic Warfare
- Offensive cyber capabilities
- Defensive network security (military-grade)
- Electronic countermeasures and jamming
- Signals intelligence (SIGINT)

### 3. Space & Satellite ISR
- Reconnaissance and surveillance satellites
- Space situational awareness
- Protected communications (SATCOM)
- GPS resilience / anti-jamming

### 4. Naval & Maritime Domain
- Red Sea / Strait of Hormuz chokepoint defense
- Anti-ship missiles and counter-measures
- Mine warfare and undersea systems
- Naval air defense (Aegis, ship-based interceptors)
- **Proxy vector note**: Houthi Red Sea campaign has a structural demand tail independent of Iran ceasefire. Model separately.

### 5. Autonomous Systems & Counter-UAS
- Tactical drones (loitering munitions, ISR)
- Counter-UAS systems (kinetic and non-kinetic)
- Swarm defense capabilities
- Drone-as-a-service / attritable platforms

### 6. AI, Software & C4ISR
- Battlefield management / decision support
- AI-enabled targeting and sensor fusion
- Data analytics / intelligence platforms
- Command, control, communications

### 7. Supply Chain, Energetics & Logistics
- Solid rocket motor production (critical bottleneck)
- Energetics and propellants
- Guidance systems and seekers
- Military logistics and sustainment

---

## Part 3: Global Company Universe

**Note**: This universe is a starting baseline. The analysis agent may add companies where strong procurement signal evidence or unique domain positioning warrants inclusion. Any additions must be documented with an explicit justification sentence citing the relevant contract, program, or supply chain position.

### US Large-Cap
| Ticker | Company | Primary Domain(s) |
|--------|---------|-------------------|
| LMT | Lockheed Martin | Missiles, Air Defense, Space |
| RTX | RTX Corporation | Missiles, Sensors, Cyber |
| NOC | Northrop Grumman | Space, Bombers, C4ISR |
| GD | General Dynamics | Naval, IT, Munitions |
| LHX | L3Harris Technologies | Space, EW, Communications |
| BA | Boeing (Defense segment) | Aircraft, Munitions, Naval |
| HII | Huntington Ingalls Industries | Naval Shipbuilding, Nuclear Submarines & Carriers |

### US Mid/Small-Cap
| Ticker | Company | Primary Domain(s) |
|--------|---------|-------------------|
| PLTR | Palantir Technologies | AI/Software, C4ISR |
| LDOS | Leidos | IT, Cyber, Intelligence |
| BAH | Booz Allen Hamilton | Cyber, AI, Consulting |
| CACI | CACI International | Cyber, SIGINT, EW |
| KTOS | Kratos Defense | Drones, Directed Energy, Attritable Targets |
| AVAV | AeroVironment | Tactical Drones, Loitering Munitions |
| TDG | TransDigm Group | Proprietary Aerospace Components, Sole-Source Supply Chain |
| MRCY | Mercury Systems | Embedded Defense Electronics, Secure Signal Processing |
| MOG.A | Moog Inc. | Precision Actuation, Missile Guidance, Flight Controls |
| TDY | Teledyne Technologies | Sensors, FLIR, Undersea Detection, ISR |

### Israel
| Ticker | Company | Primary Domain(s) |
|--------|---------|-------------------|
| ESLT | Elbit Systems | Drones, EW, C4ISR, Air Defense |

*Note: Rafael Advanced Defense Systems and Israel Aerospace Industries (IAI) are government-owned and not publicly traded. Elbit captures Israeli defense innovation exposure. Monitor for IAI IPO signals.*

### Europe
| Ticker | Company | Primary Domain(s) |
|--------|---------|-------------------|
| RHM.DE | Rheinmetall | Munitions, Vehicles, Air Defense |
| BA.L | BAE Systems | Naval, EW, Munitions, Cyber |
| SAAB-B.ST | Saab AB | Radar, EW, Submarines, C4ISR |
| LDO.MI | Leonardo | Helicopters, Electronics, Cyber |
| HO.PA | Thales | Radar, Space, Cyber, Communications |
| CHG.L | Chemring Group | Energetics, Propellants, Countermeasures (pure-play) |

### Asia-Pacific
| Ticker | Company | Primary Domain(s) |
|--------|---------|-------------------|
| 012450.KS | Hanwha Aerospace | Artillery, Munitions, Space |

**Currency risk note**: European names (EUR/GBP/SEK) and Korean names (KRW) carry FX exposure vs. USD. Estimated FX impact must be reported per non-USD position. Flag if aggregate non-USD exposure in any portfolio exceeds 30% — recommend hedging assessment.

---

## Part 4: Per-Company Scoring Framework

For **each company** in the universe, score on the following dimensions (1–5 scale):

### Dimension 1: Replenishment Exposure
- % of revenue directly tied to depleted munition categories
- Emergency procurement eligibility (sole-source, existing IDIQs)

### Dimension 2: Domain Breadth & Relevance
- Weighted by phase: Phase 1 domains (air defense, munitions) weighted 3x in near-term portfolio; Phase 3 domains (cyber, AI, space) weighted 3x in long-term portfolio

### Dimension 3: Moat / Sole-Source Position
- Sole-source contracts or irreplaceable technology
- Controls critical bottleneck (rocket motors, seekers, guidance)
- ITAR/export control barriers to entry

### Dimension 4: Production Scalability
- Current utilization rate vs. capacity
- Evidence of expansion (CapEx, new facilities, M&A)
- Historical "surge" capability
- **Constraint flag**: Companies citing labor, materials, or tooling constraints in recent earnings calls are capped at score 3 until constraint resolution is evidenced in subsequent filings

### Dimension 5: Backlog Quality
- Total backlog / revenue ratio
- Funded vs. unfunded split
- Backlog growth trajectory (YoY)

### Dimension 6: Time-to-Revenue
- Contract → revenue recognition lag
- Milestone-based vs. cost-plus structure
- Near-term earnings visibility
- **CR risk adjustment**: During an active continuing resolution period, downgrade Time-to-Revenue by 1 point for any program-start-dependent company

### Dimension 7: Valuation Discipline (CRITICAL — see Part 5)

### Dimension 8: Allied Export Potential
- FMS pipeline exposure
- NATO/Gulf/Asia-Pacific procurement eligibility
- Joint venture or offset agreement participation

### Dimension 9: Fundamental Financial Quality
High defense-thesis composite scores are insufficient if the company is financially deteriorating. This dimension acts as a quality filter.

**Profitability:**
- Gross margin, operating margin, net margin — note trend direction (expanding / stable / contracting)
- ROE threshold: >15% = strong capital efficiency
- ROA: compare to defense sector peers

**FCF Quality:**
- FCF/Net Income ratio: >1.0 = high-quality earnings (cash-backed); <0.7 = investigate accruals
- FCF yield vs. sector: flag if <2%

**Balance Sheet Health:**
- Debt/Equity: flag if >2.0x (RTX and LHX carry elevated D/E from M&A — must be explicitly acknowledged)
- Net debt / EBITDA: flag if >4.0x
- Interest coverage: flag if <3.0x
- Current ratio: >1.0 = adequate short-term liquidity

**Capital Allocation:**
- CapEx trend: growth-driving (new capacity) vs. maintenance-heavy
- Buyback/dividend discipline relative to FCF generation

**Accounting Quality Flags:**
- Large goodwill balances relative to equity (impairment risk post-M&A)
- Revenue recognition via percentage-of-completion (normal in defense, but watch for restatement risk)
- Pension obligations: LMT, NOC, RTX carry significant defined-benefit liabilities — quantify annual service cost vs. FCF

**Score Guide:**
| Score | Criteria |
|-------|----------|
| 5 | FCF conversion >100%, D/E <0.5, margins expanding, no accounting flags |
| 4 | FCF healthy, moderate leverage (<1.5x D/E), stable margins |
| 3 | Adequate, some leverage concern or margin pressure, minor flags |
| 2 | Elevated leverage (D/E >2x) or FCF constrained or declining margins |
| 1 | Financially stressed — debt servicing at risk, negative FCF trend, or material restatement risk |

---

### Output Format (MANDATORY per company):

| Company | Ticker | Replenishment (1-5) | Domain (1-5) | Moat (1-5) | Scalability (1-5) | Backlog (1-5) | Time-to-Rev (1-5) | Valuation (1-5) | Export (1-5) | Fundamentals (1-5) | Composite (Near) | Composite (Mid) | Composite (Long) |
|---------|--------|---------------------|--------------|------------|--------------------|---------------|--------------------|-----------------|--------------|--------------------|-----------------|-----------------|------------------|

**Composite Score** = Weighted average. Weights vary by portfolio horizon:

| Dimension | Near-Term Weight | Medium-Term Weight | Long-Term Weight |
|-----------|-----------------|-------------------|-----------------|
| Replenishment | 25% | 5% | 0% |
| Scalability | 18% | 10% | 14% |
| Time-to-Revenue | 17% | 8% | 0% |
| Moat | 15% | 18% | 20% |
| Valuation | 15% | 18% | 11% |
| Fundamentals | 10% | 12% | 12% |
| Backlog | 0% | 22% | 8% |
| Export | 0% | 18% | 18% |
| Domain | 0% | 12% | 25% (phase-weighted) |
| **Total** | **100%** | **100%** | **100%** |

**Tie-breaking rule**: When two companies have equal composite scores (within 0.1 points), rank by:
1. Valuation score — prefer the cheaper name
2. Fundamentals score — prefer the financially stronger name
3. Moat score — prefer the more defensible business

**Hard gate override**: Any company triggering a valuation hard gate (Part 5) is excluded from portfolio consideration regardless of composite score.

---

## Part 5: Valuation Gates

### Hard Gates (automatic exclusion from recommendation)
- **P/E > 40x** with no confirmed backlog acceleration (>20% YoY growth)
- **EV/EBITDA > 25x** AND free cash flow yield < 2%
- Stock price > 30% above 52-week average with no new contract catalyst

### Soft Gates (flag with warning, do not exclude)
- P/E > 30x (above sector median ~22x for large-cap defense)
- EV/Revenue > 4x for services companies, > 3x for hardware
- Insider selling > $10M in trailing 90 days

### Relative Valuation Ranking
- Rank all universe companies by: EV/EBITDA, P/FCF, PEG ratio
- Identify: **cheapest names with highest composite scores** = best risk/reward
- Flag: **expensive names with high scores** = "great company, bad price" risk

### Valuation Score (1–5):
- 5 = Trading below 5-year average multiples with improving fundamentals
- 4 = At or near fair value with clear catalysts
- 3 = Moderately expensive but justified by growth
- 2 = Expensive, thesis must be very strong to justify
- 1 = Overvalued — hard gate or near hard gate territory

---

## Part 6: Three Model Portfolios (Final Output)

### Portfolio A: Near-Term Tactical (0–6 months)
- **Theme**: Immediate beneficiaries of combat consumption and emergency procurement
- **Selection**: Top 8 companies by near-term composite score
- **Beta target**: Portfolio β > 1.2 vs. ITA (maximize tactical upside capture)
- **Allocation**:
  - Core positions (60%): Top 4 large-cap, equal weight
  - Growth positions (25%): 2-3 mid-cap with highest replenishment exposure
  - Speculative (15%): 1-2 small-cap with asymmetric upside
- **Entry trigger**: Confirmed supplemental budget or emergency FMS notification
- **Exit trigger**: Replenishment contracts fully priced in (P/E expansion > 40% from entry)
- **Rebalancing trigger**: Any position deviates >25% from target allocation; OR supplemental budget fully appropriated; OR new hard gate hit

### Portfolio B: Medium-Term Replenishment (6–18 months)
- **Theme**: Backlog conversion, production ramp, allied procurement wave
- **Selection**: Top 8 companies by medium-term composite score
- **Beta target**: Portfolio β 0.9–1.2 vs. ITA (balanced upside/stability)
- **Allocation**: Same structure as Portfolio A
- **Entry trigger**: Multi-year contract awards, production rate increases
- **Exit trigger**: Backlog growth rate decelerates below 10% YoY; margin compression from scaling costs confirmed in earnings
- **Rebalancing trigger**: Any position deviates >25% from target allocation; OR backlog growth rate decelerates below 10% YoY

### Portfolio C: Long-Term Structural (18–36 months)
- **Theme**: Next-gen warfare platforms, structural budget expansion, paradigm shifts
- **Selection**: Top 8 companies by long-term composite score
- **Beta target**: Portfolio β 0.8–1.1 vs. ITA (quality-growth with stability)
- **Allocation**: Same structure as Portfolio A
- **Entry trigger**: New program milestones (EMD awards, LRIP contracts), NATO spending pledges, FYDP growth confirmation
- **Exit trigger**: Program cancellation risk, political de-escalation signal, FYDP budget revision signaling cuts
- **Rebalancing trigger**: Any position deviates >25% from target allocation; OR FYDP revision signals program-level cuts

### Portfolio Constraints (apply to all):
- Max single position: 15%
- Min geographic diversification: at least 2 non-US names
- No more than 3 companies from the same warfare domain
- **Max single-domain concentration: 40%** (e.g., missiles/munitions domain cannot exceed 40% of portfolio weight)
- Valuation hard gates must be respected
- **Currency risk**: Non-USD positions must include estimated FX impact. Flag portfolios with >30% non-USD exposure for hedging assessment.
- **Beta check**: After construction, compute portfolio beta vs. ITA. If outside target range for the horizon, rebalance between core/growth/speculative tiers until target is achieved.

---

## Part 7: Data Sources (Signal Only)

### Institutional Analysts
- Jonathan Siegmann, Louie DiPalma, Alek Jovovic

### Think Tanks & Policy Research
- Chatham House, Atlantic Council, CSIS, RAND Corporation

### Data Platforms
- SIPRI (arms transfers), IISS (military balance), Jane's Defence

### Procurement Signal Sources
- SAM.gov (US contract awards)
- Defense Security Cooperation Agency (DSCA FMS notifications)
- NATO Support and Procurement Agency (NSPA)
- Congressional Budget Justification Books (FYDP data)
- HASC / SASC markup calendars and hearing transcripts

### Company Filings
- 10-K/10-Q (backlog data, segment revenue, goodwill/pension disclosures)
- Earnings call transcripts (production rate commentary, constraint language)
- Proxy statements (insider transactions)

### Market Signals
- **Options flow**: Elevated call volume or unusual open interest in defense names often leads contract announcements by 5–15 trading days
- **Institutional 13F filings**: Defense sector weight changes by top funds (quarterly, 45-day lag)
- **Short interest trends**: Rising short interest in specific names = market skepticism worth investigating before entering position

---

## Part 8: Advanced Research Heuristics (Edge Layer)

### 1. "Energetics Bottleneck"
- Map the **solid rocket motor supply chain** end-to-end
- Identify hidden Tier-2 winners: motor casings, propellant chemistry suppliers, nozzle manufacturers
- Flag any company with sole-source position on critical energetics components
- **Company connection**: CHG.L (Chemring) is the only pure-play publicly traded energetics company in the universe — evaluate sole-source positions on propellant and countermeasure fill lines. MOG.A (Moog) controls precision actuation that feeds into guided weapon terminal phases.

### 2. "Unfunded → Emergency Flip"
- Track programs currently on unfunded requirements lists
- Model which are most likely to move into **supplemental budgets** post-conflict
- Historical precedent: Post-Ukraine supplementals (2022–2024) — Stinger/Javelin replenishment went from unfunded to emergency within 60 days
- Apply this framework to current Iranian-theater requirements: C-RAM, SHORAD, naval interceptors

### 3. Export Signal Tracking
- Monitor Foreign Military Sales (FMS) pipeline by country
- Track Gulf state procurement approvals (Saudi Vision 2030 defense pillar)
- NATO member spending commitments vs. actual procurement
- Watch for: SAMI (Saudi) and EDGE Group (UAE) joint ventures with Western primes

### 4. "Drone-Slayer Index"
- Rank counter-UAS solutions by: cost-per-interception, magazine depth, scalability vs. swarm threat
- Compare: Kinetic (missile-based) vs. Non-kinetic (directed energy, EW, cyber)
- Identify the "winning architecture" for layered drone defense
- **Company connection**: KTOS (Kratos) and AVAV (AeroVironment) are primary candidates for attritable/kinetic. Evaluate MRCY (Mercury Systems) for embedded processing in counter-UAS sensor fusion platforms. KTOS directed energy programs are an asymmetric cost-per-kill bet.

### 5. "Cyber Escalation Premium"
- Model the probability and impact of cyber escalation on defense IT/cyber companies
- Track: US Cyber Command budget, CMMC compliance mandates, zero-trust adoption mandates
- Identify companies with **recurring revenue** from cyber defense (not one-time project work)
- Distinguish: PLTR/LDOS/BAH/CACI have different revenue recurrence profiles — map this explicitly

### 6. "Space Vulnerability Index"
- Assess which space assets are most at risk (LEO vs. GEO, military vs. dual-use)
- Identify companies positioned for space resilience (proliferated LEO constellations, rapid reconstitution)
- Track: Space Force budget growth, SDA Tranche awards (Tranche 2 and 3 contracts are near-term catalysts)
- **Company connection**: NOC and LHX are primary SDA constellation competitors. Map Tranche award timelines.

### 7. "Naval Chokepoint Premium"
- Red Sea / Strait of Hormuz conflict → sustained naval defense demand regardless of Iran ceasefire
- Map companies exposed to: shipbuilding, naval munitions, undersea systems, Aegis upgrades
- Track: Navy shipbuilding plan, Aegis system production rates, torpedo/mine procurement
- **Company connection**: HII is the **sole** builder of US nuclear-powered carriers and one of only two submarine builders (with GD/Electric Boat). Model Houthi campaign duration as a direct demand signal for sustained vessel maintenance and new construction. TDY (Teledyne) for undersea sonar and detection systems. RTX for SM-6/SM-3 naval interceptors.

### 8. "Congressional Calendar Model" (NEW)
**Purpose**: A contract thesis without an appropriations timing model is incomplete. Budget signal and contract award are not the same event.

**Key calendar dates to track annually:**
| Event | Typical Timing | Investment Implication |
|-------|---------------|----------------------|
| President's Budget Request (PBR) | February | Sets FYDP demand signal; watch for program additions/cuts |
| HASC/SASC markup | May–July | Authorization levels; earmarks; floor amendments |
| NDAA floor vote | September–December | Confirms authorization; enables FMS approvals |
| Appropriations deadline | September 30 (FY start Oct 1) | If missed → CR activates |
| Continuing Resolution (CR) | Oct–Jan (if applicable) | Freezes new program starts; limits production rate increases |
| Supplemental introduction | T+30–90 days post-conflict trigger | Watch for admin request language |
| Supplemental signed into law | T+90–180 days (historical range) | Contract awards begin flowing T+180–270 |

**Supplemental budget timing model (based on Ukraine 2022 precedent):**
- T+0: Conflict trigger event
- T+30: Administration drafts supplemental request
- T+90: Supplemental introduced to Congress
- T+120–180: Signed into law
- T+180–270: Contract awards flowing

**Investment implication**: Near-term portfolio entry should be executed before T+90 (when supplemental language is public but market has not yet fully priced contract specifics). CR risk flag: Downgrade Time-to-Revenue score by 1 point for program-start-dependent companies during active CR periods.

### 9. "Production Constraint Tracker" (NEW)
**Purpose**: Dimension 4 (Scalability) requires understanding the actual binding constraints, not just rated capacity.

**Constraint types to track per company:**
| Constraint Type | Examples | Primary Affected Companies |
|----------------|----------|--------------------------|
| Skilled labor | Welders (shipyards), guidance assemblers | HII, RTX, GD |
| Materials | Titanium, radiation-hardened FPGAs, specialty propellant chemistry | LMT, NOC, CHG.L |
| Tooling lead times | Missile production tooling: 12–18 month lead from sub-suppliers | RTX, LMT |
| Sub-tier bottlenecks | Rocket motor casings, seeker components, energetic fill lines | KTOS, CHG.L, MOG.A |

**Flag rule**: Any company citing a specific production constraint in earnings call language should have Scalability score capped at 3 until constraint resolution is evidenced in a subsequent quarterly filing.

---

## Part 9: Regional Realignment Analysis

### Gulf Cooperation Council (Saudi Arabia, UAE, Kuwait)
- Analyze shift toward **defense sovereignty / local manufacturing**
- Who wins: Western primes (as JV partners) vs. local champions (SAMI, EDGE)?
- Map specific JV/offset agreements and their revenue potential
- Track Saudi Vision 2030 defense localization targets and actual procurement split

### European Rearmament
- Track national defense budget increases (Germany's Zeitenwende, Poland's 4% GDP target)
- Identify European primes benefiting from domestic preference policies
- Map cross-border European procurement (Eurofighter, FCAS, MGCS programs)
- Watch for EU defense industrial base legislation creating preferential procurement for European primes

### Asia-Pacific (Secondary)
- South Korea as emerging defense exporter (Hanwha, Korea Aerospace Industries)
- Japan's defense budget doubling and revised export policy (lifting of arms export restrictions)
- Australia's AUKUS-driven procurement (SSN-AUKUS submarine program → HII/GD involvement)

---

## Part 10: Fundamental Analysis Integration

For each company in the universe, conduct a **focused fundamental analysis** alongside the defense-thesis scoring. The purpose is to ensure high-scoring defense plays are not undermined by financial deterioration or accounting risk.

### Required Output Per Company

**Profitability Snapshot:**
- EPS (TTM and forward), growth direction
- Gross margin, operating margin, net margin — expanding / stable / contracting
- ROE (flag if <10%; defense sector median ~15–20%)
- ROA vs. sector peers

**Valuation Cross-Check (feeds Dimension 7):**
- P/E trailing and forward; compare to defense sector median (~22x large-cap)
- PEG ratio: <1.0 = potential undervaluation relative to growth
- EV/EBITDA; compare to company's own 5-year average
- P/FCF; FCF yield threshold: flag if <2%

**Balance Sheet Assessment:**
- Debt/Equity — note M&A-driven leverage (RTX, LHX carry elevated D/E from Raytheon and Harris mergers respectively)
- Net debt / EBITDA — flag if >4.0x
- Current ratio — flag if <1.0
- Interest coverage — flag if <3.0x
- Pension liability: LMT, NOC, RTX carry large defined-benefit obligations; report annual pension service cost as % of FCF

**Cash Flow Quality:**
- OCF / Net Income ratio (>1.0 = quality earnings; <0.7 = investigate accruals)
- Free cash flow = OCF − CapEx; trend direction
- CapEx classification: growth-driving vs. maintenance-heavy

**Accounting Quality Flags:**
- Goodwill as % of total equity (impairment risk, especially post-M&A): flag if >50%
- Revenue recognition via percentage-of-completion (standard in defense, but flag any restatement history)
- Segment margin disclosure gaps: flag if key segments are blended in reporting

### Per-Company Fundamental Verdict (mandatory output)
```
- Financial Health:     [Strong / Adequate / Weak]
- Earnings Quality:     [High / Medium / Low]
- Balance Sheet Risk:   [Low / Moderate / High]
- FCF Yield:            X%
- Key Flags:            [List any hard concerns]
```

---

## Part 11: Final Output Requirements (Strict)

### Per Company:
1. **Investment thesis** (2–3 lines, specific — no generalities)
2. **Primary growth driver** (cite a specific contract, program, or procurement signal with approximate value/timeline)
3. **Key risk** (the single most likely reason this thesis fails)
4. **Catalysts** (next 6–12 months, with approximate dates where possible)
5. **Fundamental snapshot** (Financial Health, Earnings Quality, Balance Sheet Risk, FCF Yield)
6. **Proxy exposure** (how does Houthi/Hezbollah/militia persistence affect this thesis — positively or negatively?)
7. **Confidence score** (1–10 with brief justification)

### Per Portfolio:
1. **Ranked list** of 8 companies with all three composite scores (near/mid/long)
2. **Allocation breakdown** (Core / Growth / Speculative with explicit % weights)
3. **Portfolio beta** vs. ITA — computed, not estimated; confirm it meets horizon target
4. **Non-USD exposure** — total %, list of affected names, FX impact estimate
5. **Entry/exit criteria** specific to that time horizon
6. **Rebalancing trigger** conditions (explicit, not generic)
7. **Scenario analysis**:
   - **Base case**: Conflict contained, orderly replenishment, congressional appropriations on schedule
   - **Escalation case**: Wider regional war, proxy persistence, emergency supplemental, production constraint acceleration
   - **De-escalation case**: Ceasefire, defense spending plateau, supplemental delayed or reduced
   - **CR/sequestration case**: Congressional gridlock delays appropriations — unique risk to US defense spending programs; model impact on Time-to-Revenue for each holding

### Summary Output:
- **One-page executive brief** with the single highest-conviction idea per portfolio
- **Risk matrix**: What kills each portfolio? (de-escalation, budget sequestration, supply chain failure, congressional CR, financial deterioration at portfolio companies)
- **Pairs/hedges**: For each portfolio, one suggested hedge (short candidate or defensive offset)
- **Domain concentration check**: Confirm no domain exceeds 40% across each portfolio

---

## Part 12: Media Intelligence Collection Protocol

**Purpose**: Part 7 lists *what* sources exist. This part explains *how* to systematically collect, classify, and act on signals from those sources. A thesis built on stale or misread intelligence is worse than no thesis at all.

---

### 12.1 Source Taxonomy

Rank sources by signal quality before investing time in them.

**Tier 1 — Primary Sources (highest signal, lowest noise)**

These are official, verifiable, and carry immediate investment relevance:

| Source | What to Look For | Access Method |
|--------|-----------------|---------------|
| DoD Contract Announcements (defense.gov/News/Contracts) | Daily 5pm ET releases — dollar value, company, program name | RSS feed + keyword filter |
| SAM.gov Award Search | Sole-source justifications, IDIQ task orders, emergency OTAs | Set saved searches by company CAGE code and program keywords |
| DSCA FMS Notifications | Country, system, dollar value — triggers export thesis | Email list at dsca.mil/press-room |
| Company 8-K Filings (SEC EDGAR) | Material contract awards, guidance changes, leadership changes | EDGAR full-text search or RSS by CIK number |
| Congressional Record / Congress.gov | NDAA amendment text, appropriations line items, hearing testimony | Full-text keyword search |
| Pentagon Press Briefings (defense.gov/News/Transcripts) | Secretary/CJCS statements on procurement priorities, surge production orders | RSS + keyword scan |

**Tier 2 — Trade Publications (defense-specific, high domain expertise)**

Read for context, program-level detail, and procurement intent signals (RFPs, down-selects):

| Publication | Specialty | Best Signal Type |
|-------------|-----------|-----------------|
| Breaking Defense (breakingdefense.com) | US acquisition policy, Pentagon politics | Budget and program decisions |
| Defense News (defensenews.com) | Industry-wide contract and program news | Contract awards, production news |
| Aviation Week & Space Technology | Aerospace/defense technical | Program milestones, production rates |
| The War Zone (thedrive.com/the-war-zone) | Operational/tactical, weapons employment | Conflict escalation signals, new system deployments |
| C4ISRNET (c4isrnet.com) | Cyber, C2, ISR, EW | Cyber/EW program and contract signals |
| Naval News (navalnews.com) | Naval systems, shipbuilding | Naval procurement and deployment signals |
| Jane's Defence (janes.com) | Technical intelligence, order-of-battle | Sole-source identification, Tier-2 supply chain |

**Tier 2 — Think Tanks (policy and budget analysis)**

Use for budget trajectory modeling and geopolitical context — not for near-term contract signals:

| Organization | Best Use |
|-------------|---------|
| CSIS Defense360 | Congressional defense budget analysis, NDAA tracking |
| RAND Corporation | Technology forecasting, program risk assessment |
| CNAS (Center for a New American Security) | Emerging technology defense applications |
| Atlantic Council | Allied procurement, NATO spending trajectory |

**Tier 2 — Financial Media**

Use for valuation context and institutional sentiment — not as primary contract intelligence:

- Bloomberg (defense industry tag), Reuters Defense, WSJ defense beat
- Seeking Alpha defense articles: useful for contrarian signals; always verify underlying data

**Tier 3 — Social / Sentiment (use as corroborating signal only, never primary)**

| Channel | Value | Caution |
|---------|-------|---------|
| X/Twitter: @BreakingDefense, @defensenewsmedia, @AaronMehta, @TaraCopp | Breaking news 2–4 hours before formal release | Unverified until official source confirms |
| LinkedIn: defense executive commentary | Occasionally signals production expansions, hiring surges | Self-promotional; verify independently |
| r/CredibleDefense (Reddit) | Operational context, proxy theater tracking | No investment signal; use for conflict phase modeling only |

---

### 12.2 Collection Cadence

Structure your monitoring to match signal velocity. Not all sources require daily attention.

**Real-Time (set alerts — no manual checking required)**

| Alert Type | Setup Method | Trigger Condition |
|------------|-------------|-------------------|
| Company 8-K filings | EDGAR email alerts by CIK per universe company | Material contract or guidance change |
| SAM.gov contract awards | Saved search by company CAGE code | Any award >$50M to a universe company |
| DSCA FMS notifications | dsca.mil email subscription | Any notification referencing universe system |
| Google News alerts | One alert per universe ticker + company name | Breaking news mention |
| Pentagon contract page | RSS reader (e.g., Feedly) on defense.gov/News/Contracts | Daily 5pm release scan |

**Daily (~15 minutes)**

- Scan Pentagon daily contract announcements for universe company names
- Scan Breaking Defense and Defense News headlines
- Check X/Twitter defense journalists for breaking program news

**Weekly (~60 minutes)**

- Review HASC/SASC hearing transcripts for program mentions (Congress.gov "Hearings" section)
- Read Aviation Week and C4ISRNET for production rate and milestone news
- Review options flow in defense names for unusual activity (via brokerage platform or TradingView)
- Update earnings calendar: note any universe company reporting within next 30 days

**Monthly (~2–3 hours)**

- DSCA FMS notification review: compile new entries, map to export scores
- Screen Institutional 13F changes for defense sector weight shifts (SEC EDGAR, with 45-day lag awareness)
- Jane's order tracker: new orders placed for universe company systems by allied nations
- Review SIPRI quarterly arms transfer data if available

**Quarterly (~4–6 hours)**

- Full 10-Q analysis for each universe company (mandatory fields: backlog, funded/unfunded split, segment revenue, production constraint language in MD&A and earnings call transcript)
- Earnings call transcript review: extract specific constraint language (labor, materials, tooling) — apply Dimension 4 cap rule where triggered
- Proxy filing review: insider transactions in trailing 90 days — apply soft gate if >$10M selling

**Annually (~1 full day)**

- 10-K deep review: backlog composition, segment margins, pension obligations, goodwill/impairment disclosures
- FYDP analysis (February PBR release): line-by-line changes to defense program funding vs. prior year
- NDAA final text analysis (December–January): authorization changes that create or eliminate programs
- SIPRI Arms Transfers Database: annual update to allied procurement and FMS pipeline data

---

### 12.3 Signal Classification Framework

Every piece of media intelligence must be classified before acting on it. Unclassified signals create noise.

| Signal Class | Definition | Example |
|-------------|-----------|---------|
| **Contract Signal** | Specific dollar-value award to a universe company | "Raytheon awarded $1.2B IDIQ for PAC-3 interceptors" |
| **Procurement Intent Signal** | RFI/RFP issued — indicates upcoming award, not yet booked | "DoD issues RFP for next-gen SHORAD" |
| **Budget Signal** | Appropriations change, supplemental introduction, FYDP revision | "Senate Appropriations adds $800M for Patriot replenishment" |
| **Production Signal** | Official rate increase/decrease, new facility, CapEx announcement | "RTX breaks ground on Tucson missile production expansion" |
| **Export Signal** | FMS notification, allied nation procurement announcement | "DSCA notifies Congress of $3.5B Patriot sale to Poland" |
| **Conflict Escalation Signal** | New proxy theater activation, operational tempo increase | "Houthi launches 15 drones at Red Sea shipping convoy" |
| **Constraint Signal** | Production bottleneck disclosed by company or government | "HII CEO cites welder shortage limiting submarine delivery schedule" |
| **Financial Risk Signal** | FCF miss, guidance cut, credit downgrade, insider selling | "MRCY cuts FCF guidance; cites program cost overruns" |
| **Sentiment Signal** | Analyst upgrade/downgrade, institutional buying/selling | "Citi upgrades NOC to Buy with $550 PT" |
| **Regulatory/Political Signal** | Export license denial, sanctions, program cancellation | "State Dept denies export license for drone system to Gulf ally" |

---

### 12.4 Signal-to-Score Mapping

When a classified signal arrives, this table determines which scoring dimensions to update and whether a portfolio action review is required.

| Signal Class | Dimension Affected | Direction | Action Required |
|-------------|-------------------|-----------|----------------|
| Contract Signal (sole-source, >$500M) | Moat (D3), Replenishment (D1), Time-to-Rev (D6) | Up | Re-score immediately; check entry trigger |
| Contract Signal (<$100M or competitive) | Replenishment (D1) | Minor up | Log; re-score at next scheduled review |
| Procurement Intent Signal (RFP issued) | Backlog (D5) — pending | Neutral | Monitor; set alert for award announcement |
| Budget Signal (supplemental introduced) | Replenishment (D1) for named programs | Up | **Portfolio A entry trigger review** |
| Budget Signal (CR activated) | Time-to-Rev (D6) for program-start companies | Down 1 pt | Apply CR adjustment rule immediately |
| Budget Signal (program cut in FYDP) | Backlog (D5), Replenishment (D1) | Down | Re-score; may trigger exit |
| Production Signal (rate increase confirmed) | Scalability (D4) | Up (remove cap if applied) | Re-score Dimension 4 |
| Production Signal (constraint disclosed in earnings) | Scalability (D4) | Cap at 3 | Apply cap; set reminder to check next quarter |
| Export Signal (FMS >$1B) | Export (D8) | Up | Re-score; may be Portfolio B entry trigger |
| Conflict Escalation Signal (proxy activation) | Domain (D2), Replenishment (D1) for relevant domains | Up | Re-evaluate phase model; update proxy vector table |
| Constraint Signal (management language) | Scalability (D4) | Cap at 3 | Apply constraint cap rule (Part 8, Heuristic 9) |
| Financial Risk Signal (FCF miss >15%) | Fundamentals (D9) | Down | Re-score D9; check if hard gate triggered |
| Financial Risk Signal (insider selling >$10M) | Valuation (D7) | Soft gate flag | Flag; do not exclude; watch for 30-day confirmation |
| Sentiment Signal (analyst upgrade) | None — do not update dimensions | N/A | Log; compare analyst thesis to own; note divergence |
| Regulatory Signal (export denial) | Export (D8) | Down sharply | Re-score; may disqualify from Portfolio C |

**Rule**: Sentiment signals (analyst upgrades, price target changes) must **never** directly update a scoring dimension. They are logged for divergence analysis only — if the market is more bullish than your own thesis, that is useful information but not a scoring input.

---

### 12.5 Noise Filter — What to Ignore

Discipline in filtering is as important as discipline in collecting.

**Always ignore:**
- Anonymous/unverified social media contract rumors (require Tier 1 source confirmation)
- Company-issued press releases about contracts **without** DoD corroboration (check SAM.gov or defense.gov same day)
- Analyst price target changes with no new fundamental data cited
- Media speculation about future programs without RFP, RFI, or budget line-item evidence
- Stock price movement alone as a signal — price moves are an effect, not a cause

**Weight down (require second-source confirmation before acting):**
- Single-journalist breaking defense news (wait for second outlet or official confirmation)
- "Sources say" budget reporting without named congressional or Pentagon official
- Earnings call management commentary about pipeline without signed contract evidence
- International media reporting on Gulf/European procurement (translation + context risk)

**Red flag for potential misinformation:**
- Contract announcements with no SAM.gov or defense.gov matching entry within 48 hours
- FMS "leaks" before formal DSCA notification (DSCA process is standardized; pre-notification leaks are rare and often inaccurate)

---

### 12.6 Immediate Action Trigger List

The following media signals require same-day portfolio review — do not defer to scheduled cadence:

1. Any universe company receives sole-source contract >$500M (re-score Dimensions 1, 3, 6; check Portfolio A entry trigger)
2. DSCA FMS notification for a system tied to a universe company, value >$1B (re-score Dimension 8; check Portfolio B entry trigger)
3. Supplemental budget request formally introduced to Congress naming specific programs (Portfolio A entry trigger review)
4. October 1 arrives with no full appropriations signed (CR activated — apply Dimension 6 downgrade across affected companies)
5. Universe company 8-K reports FCF miss >15% vs. guidance (re-score Dimension 9; check hard gate)
6. New proxy escalation event (Houthi campaign surge, Hezbollah activation, Iraqi militia strike on US assets) — update proxy vector table in Part 1; re-evaluate domain weights
7. Major program cancellation affecting a universe company (mandatory re-score; likely portfolio exit trigger)
8. Production rate increase officially confirmed by DoD or company investor relations (re-score Dimension 4; remove constraint cap if previously applied)

---
