"""
Agent 1 — Market Intelligence Agent
Builds a complete company profile: business model, competitive advantages,
management quality, industry position, and recent events.
"""
import json
import logging

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are a Market Intelligence Agent for an institutional AI investment research team.

Your role is to analyse a company and produce a thorough business intelligence profile.

You must:
- Describe the business model and revenue streams clearly
- Identify competitive advantages (economic moat)
- Assess management quality based on available data
- Summarise recent significant events (earnings, M&A, launches, regulatory)
- Evaluate industry position and competitive landscape

Rules:
- Base your analysis only on the data provided
- If a field has insufficient data, say so explicitly
- Be objective — neither unduly bullish nor bearish
- Respond with a VALID JSON OBJECT ONLY. No extra text, no markdown prose outside the JSON."""

USER_PROMPT_TEMPLATE = """Analyse {ticker} ({company_name}).

=== COMPANY PROFILE ===
Sector: {sector}
Industry: {industry}
Country: {country}
Employees: {employees}
Market Cap: ${market_cap_b:.1f}B

Business Description:
{business_summary}

=== RECENT NEWS ({news_count} items) ===
{news_text}

=== KEY STATS ===
{key_stats}

Return a JSON object with EXACTLY this structure:
{{
  "business_description": "2-3 sentence summary of what the company does",
  "revenue_streams": ["stream 1", "stream 2"],
  "competitive_advantages": ["advantage 1", "advantage 2"],
  "competitive_risks": ["risk 1", "risk 2"],
  "management_assessment": "Assessment of management team quality",
  "management_score": <integer 1-10>,
  "recent_events": ["event 1", "event 2"],
  "industry_position": "Description of position within the industry",
  "market_size_assessment": "Assessment of addressable market",
  "company_quality_score": <integer 1-10>,
  "key_insights": "Most important single insight about this company"
}}"""


def _format_news(news: list) -> str:
    if not news:
        return "No recent news available."
    lines = []
    for i, n in enumerate(news[:10], 1):
        title = n.get("title", "").strip()
        pub = n.get("publisher", "")
        if title:
            lines.append(f"{i}. [{pub}] {title}")
    return "\n".join(lines) if lines else "No recent news available."


def _format_key_stats(info: dict) -> str:
    fields = [
        ("Revenue (TTM)", info.get("totalRevenue"), "B", 1e9),
        ("Revenue Growth (YoY)", info.get("revenueGrowth"), "%", 100),
        ("Gross Margin", info.get("grossMargins"), "%", 100),
        ("Net Margin", info.get("profitMargins"), "%", 100),
        ("ROE", info.get("returnOnEquity"), "%", 100),
        ("Free Cash Flow", info.get("freeCashflow"), "B", 1e9),
        ("Dividend Yield", info.get("dividendYield"), "%", 100),
    ]
    lines = []
    for label, val, unit, divisor in fields:
        if val is not None:
            if unit == "B":
                lines.append(f"  {label}: ${val / divisor:.2f}B")
            else:
                lines.append(f"  {label}: {val * divisor:.1f}%")
    return "\n".join(lines) if lines else "  (Limited financial data available)"


def market_intelligence_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Market Intelligence Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    info = state.get("info", {})
    news = state.get("news", [])

    market_cap = info.get("marketCap") or 0
    market_cap_b = market_cap / 1e9

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        sector=info.get("sector", "N/A"),
        industry=info.get("industry", "N/A"),
        country=info.get("country", "N/A"),
        employees=f"{info.get('fullTimeEmployees', 'N/A'):,}" if isinstance(info.get("fullTimeEmployees"), int) else "N/A",
        market_cap_b=market_cap_b,
        business_summary=info.get("longBusinessSummary", "Not available.")[:1500],
        news_count=len(news),
        news_text=_format_news(news),
        key_stats=_format_key_stats(info),
    )

    logger.info("Running Market Intelligence Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    return {"market_intelligence": result}
