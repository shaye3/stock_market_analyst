"""
Agent 6 — Risk Assessment Agent
Identifies and evaluates all major risks: company, industry, market, and event risks.
"""
import logging

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are a Risk Assessment Agent for an institutional AI investment research team.

Your role is to identify and rigorously assess all material risks associated with investing in this stock.

Risk categories to evaluate:
1. Company risks: declining growth, high debt, margin compression, management issues, competitive threats
2. Industry risks: disruption, regulation, commoditisation, demand cyclicality
3. Market/Macro risks: rate sensitivity, recession exposure, liquidity, sector rotation
4. Event risks: upcoming earnings, litigation, regulatory investigations, M&A

For each identified risk:
- Assess severity: LOW / MEDIUM / HIGH / CRITICAL
- Assess probability: LOW / MEDIUM / HIGH
- Consider mitigants

Be rigorous — challenge bullish assumptions made elsewhere in the analysis.
A good risk assessment protects capital first.

Investment horizon context: 6-24 months (long-term value investing)

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Perform risk assessment for {ticker} ({company_name}).

=== BUSINESS CONTEXT ===
Sector: {sector}
Industry: {industry}
Market Cap: ${market_cap_b:.1f}B
Company Age / Maturity: {maturity}

=== FINANCIAL RISK INDICATORS ===
Debt/Equity:        {de_ratio}
Current Ratio:      {current_ratio}
Net Cash Position:  ${net_cash_b:.2f}B
Interest Coverage:  {interest_coverage}
Revenue Growth:     {rev_growth}%
Net Margin:         {net_margin}%
FCF Margin:         {fcf_margin}%

=== PRIOR AGENT RISK SIGNALS ===
Fundamental weaknesses: {fundamental_weaknesses}
Balance sheet health:   {balance_sheet_health}
Macro environment:      {macro_verdict}
Key macro risk:         {macro_key_risk}
Technical trend:        {tech_trend}
Sentiment:              {sentiment}
Contrarian signal:      {contrarian}

=== RECENT NEWS (risk-relevant) ===
{risk_news}

Identify ALL material risks for a 6-24 month holding period.

Return a JSON object with EXACTLY this structure:
{{
  "company_risks": [
    {{"risk": "Risk description", "severity": "LOW|MEDIUM|HIGH|CRITICAL", "probability": "LOW|MEDIUM|HIGH", "mitigant": "What reduces this risk"}}
  ],
  "industry_risks": [
    {{"risk": "Risk description", "severity": "LOW|MEDIUM|HIGH|CRITICAL", "probability": "LOW|MEDIUM|HIGH", "mitigant": "What reduces this risk"}}
  ],
  "market_risks": [
    {{"risk": "Risk description", "severity": "LOW|MEDIUM|HIGH|CRITICAL", "probability": "LOW|MEDIUM|HIGH", "mitigant": "What reduces this risk"}}
  ],
  "event_risks": [
    {{"risk": "Risk description", "severity": "LOW|MEDIUM|HIGH|CRITICAL", "probability": "LOW|MEDIUM|HIGH", "mitigant": "What reduces this risk"}}
  ],
  "top_3_risks": ["Most critical risk", "Second risk", "Third risk"],
  "downside_scenario": "Description of the bear case scenario if risks materialise",
  "downside_pct_estimate": <integer, estimated % decline in worst case scenario>,
  "risk_score": <integer 1-10, where 1=extremely risky, 10=very low risk>,
  "overall_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_summary": "2-3 sentence overall risk assessment"
}}"""


def _extract_risk_news(news: list) -> str:
    risk_keywords = [
        "lawsuit", "investigation", "fraud", "debt", "loss", "decline", "warning",
        "layoff", "recall", "regulation", "sec", "fine", "penalty", "miss",
        "downgrade", "cut", "risk", "concern", "volatile", "crash", "crisis",
    ]
    relevant = []
    for n in news:
        title = (n.get("title") or "").lower()
        if any(kw in title for kw in risk_keywords):
            relevant.append(f"  ⚠ {n.get('title', '')}")
    if not relevant:
        return "  No specific risk-related news in recent headlines."
    return "\n".join(relevant[:8])


def _safe_pct(info, key):
    val = info.get(key)
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}"
    except (TypeError, ValueError):
        return "N/A"


def risk_assessment_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Risk Assessment Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    info = state.get("info", {})
    news = state.get("news", [])
    fundamental = state.get("fundamental_analysis", {})
    macro = state.get("macro_analysis", {})
    technical = state.get("technical_analysis", {})
    sentiment = state.get("sentiment_analysis", {})
    current_price = state.get("current_price", 0)

    market_cap = info.get("marketCap") or 0
    total_debt = info.get("totalDebt") or 0
    total_cash = info.get("totalCash") or 0
    total_rev = info.get("totalRevenue") or 1
    fcf = info.get("freeCashflow") or 0

    # Maturity estimate from years public / employees
    employees = info.get("fullTimeEmployees")
    maturity = "large established company" if (employees or 0) > 10000 else "mid-size company" if (employees or 0) > 1000 else "smaller company"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        sector=info.get("sector", "N/A"),
        industry=info.get("industry", "N/A"),
        market_cap_b=market_cap / 1e9,
        maturity=maturity,
        de_ratio=info.get("debtToEquity", "N/A"),
        current_ratio=info.get("currentRatio", "N/A"),
        net_cash_b=(total_cash - total_debt) / 1e9,
        interest_coverage=info.get("operatingCashflow", "N/A"),
        rev_growth=_safe_pct(info, "revenueGrowth"),
        net_margin=_safe_pct(info, "profitMargins"),
        fcf_margin=f"{fcf / total_rev * 100:.1f}" if total_rev and fcf else "N/A",
        fundamental_weaknesses="; ".join(fundamental.get("key_weaknesses", ["N/A"])),
        balance_sheet_health=fundamental.get("balance_sheet_health", "N/A"),
        macro_verdict=macro.get("overall_macro_verdict", "N/A"),
        macro_key_risk=macro.get("key_macro_risk", "N/A"),
        tech_trend=technical.get("trend_direction", "N/A"),
        sentiment=sentiment.get("news_sentiment", "N/A"),
        contrarian=sentiment.get("contrarian_signal", "N/A"),
        risk_news=_extract_risk_news(news),
    )

    logger.info("Running Risk Assessment Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=3000)

    return {"risk_assessment": result}
