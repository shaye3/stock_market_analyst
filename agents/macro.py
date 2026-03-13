"""
Agent 2 — Macro Economy Agent
Evaluates the global economic environment and determines how macro conditions
affect this specific stock and its sector.
"""
import logging

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are a Macro Economy Agent for an institutional AI investment research team.

Your role is to analyse the global macroeconomic environment and determine whether it is:
  - SUPPORTIVE: tailwinds for the company's sector
  - NEUTRAL: macro is not a major driver either way
  - HOSTILE: headwinds that could hurt the sector/company

Evaluate:
1. Interest rate environment and central bank policy direction
2. Inflation trends and their impact on the company's sector
3. Economic growth outlook (GDP, consumer spending)
4. Sector rotation and risk-on vs risk-off sentiment
5. Geopolitical risks relevant to the company
6. Currency risks (if international exposure exists)

Important: Your macro knowledge has a cutoff. Note any uncertainty about very recent data.

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Analyse the macro environment for {ticker} ({company_name}).

=== COMPANY CONTEXT ===
Sector: {sector}
Industry: {industry}
Country: {country}
International Exposure: {international}

=== MARKET INTELLIGENCE CONTEXT ===
{market_intel_summary}

=== RECENT MACRO-RELEVANT NEWS ===
{macro_news}

As of today ({analysis_date}), analyse the macro environment for this company's sector.

Return a JSON object with EXACTLY this structure:
{{
  "interest_rate_environment": "supportive|neutral|hostile",
  "interest_rate_analysis": "Explanation of how rate environment affects this company",
  "inflation_trend": "declining|stable|rising",
  "inflation_impact": "How inflation affects this company specifically",
  "economic_cycle": "expansion|peak|contraction|recovery",
  "gdp_outlook": "Brief GDP growth assessment",
  "sector_macro_impact": "tailwind|neutral|headwind",
  "sector_macro_explanation": "Why macro is a tailwind/neutral/headwind for this sector",
  "geopolitical_risks": ["risk 1", "risk 2"],
  "currency_risk": "Assessment of FX exposure (if any)",
  "liquidity_conditions": "tight|neutral|loose",
  "overall_macro_verdict": "supportive|neutral|hostile",
  "macro_score": <integer 1-10, where 10 = highly supportive macro>,
  "key_macro_risk": "Single biggest macro risk for this investment",
  "macro_summary": "2-3 sentence overall macro assessment"
}}"""


def _extract_macro_news(news: list) -> str:
    macro_keywords = [
        "fed", "interest rate", "inflation", "gdp", "economy", "recession",
        "central bank", "rate", "monetary", "fiscal", "tariff", "geopolit",
        "china", "trade", "treasury", "yield", "employment", "jobs",
    ]
    relevant = []
    for n in news:
        title = (n.get("title") or "").lower()
        if any(kw in title for kw in macro_keywords):
            relevant.append(f"  - {n.get('title', '')}")
    if not relevant:
        return "  No macro-specific news found in recent headlines."
    return "\n".join(relevant[:8])


def macro_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Macro Economy Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    info = state.get("info", {})
    news = state.get("news", [])
    market_intel = state.get("market_intelligence", {})
    analysis_date = state.get("analysis_date", "")

    # Summarise market intelligence context
    intel_summary = ""
    if market_intel and "error" not in market_intel:
        intel_summary = (
            f"Industry Position: {market_intel.get('industry_position', 'N/A')}\n"
            f"Key Insights: {market_intel.get('key_insights', 'N/A')}"
        )
    else:
        intel_summary = "Market intelligence not available."

    # International exposure from info
    intl_exposure = "unknown"
    total_rev = info.get("totalRevenue")
    if info.get("country") != "United States":
        intl_exposure = "significant international operations"
    elif info.get("sector") in ("Technology", "Consumer Cyclical", "Energy"):
        intl_exposure = "likely significant international revenue"
    else:
        intl_exposure = "primarily domestic US"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        sector=info.get("sector", "N/A"),
        industry=info.get("industry", "N/A"),
        country=info.get("country", "N/A"),
        international=intl_exposure,
        market_intel_summary=intel_summary,
        macro_news=_extract_macro_news(news),
        analysis_date=analysis_date,
    )

    logger.info("Running Macro Economy Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    return {"macro_analysis": result}
