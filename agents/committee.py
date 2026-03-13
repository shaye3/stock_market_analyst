"""
Agent 7 — Chief Investment Analyst Agent
Synthesises all 6 agent outputs into a final investment thesis and recommendation.
Produces both a structured JSON recommendation and a full narrative memo.
"""
import json
import logging

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are the Chief Investment Analyst — the final decision-maker for an AI hedge fund research team.

You have received analysis from 6 specialised agents. Your job is to:
1. Synthesise all evidence into a coherent investment thesis
2. Weigh bullish factors against bearish factors objectively
3. Determine the final risk/reward profile
4. Make a clear, actionable investment recommendation

Investment philosophy: Long-term VALUE investing (6-24 month horizon)
- Fundamentals drive 70% of the decision weight
- Macro and sentiment provide context (15%)
- Technical analysis guides entry timing (15%)
- Always prioritise capital preservation — when in doubt, stay out

Recommendation levels:
- STRONG BUY: High conviction, significantly undervalued, strong fundamentals, low risk
- BUY: Good conviction, moderately attractive risk/reward
- HOLD: Fairly valued or mixed signals — wait for better entry or more clarity
- AVOID: Overvalued, deteriorating fundamentals, or risk too high

You must be honest and balanced. Challenge your own bullish assumptions.
If the data is insufficient, say so clearly and reflect this in a lower confidence score.

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Make the final investment recommendation for {ticker} ({company_name}).
Current Price: ${current_price:.2f}
Analysis Date: {analysis_date}

═══════════════════════════════════════════════════════
AGENT 1 — MARKET INTELLIGENCE
═══════════════════════════════════════════════════════
Company Quality Score: {company_quality_score}/10
Competitive Advantages: {competitive_advantages}
Management Score: {management_score}/10
Key Insights: {market_key_insight}

═══════════════════════════════════════════════════════
AGENT 2 — MACRO ECONOMY
═══════════════════════════════════════════════════════
Overall Macro Verdict: {macro_verdict}
Sector Impact: {sector_macro_impact}
Macro Score: {macro_score}/10
Key Macro Risk: {key_macro_risk}
Summary: {macro_summary}

═══════════════════════════════════════════════════════
AGENT 3 — FUNDAMENTAL ANALYSIS
═══════════════════════════════════════════════════════
Valuation Verdict: {valuation_verdict}
Fundamental Score: {fundamental_score}/10
Profitability: {profitability_assessment} ({profitability_score}/10)
Growth: {growth_assessment} ({growth_score}/10)
Balance Sheet: {balance_sheet_health} ({balance_sheet_score}/10)
FCF Quality: {fcf_quality} ({fcf_score}/10)
Key Strengths: {fundamental_strengths}
Key Weaknesses: {fundamental_weaknesses}
Summary: {fundamental_summary}

═══════════════════════════════════════════════════════
AGENT 4 — TECHNICAL ANALYSIS
═══════════════════════════════════════════════════════
Trend Direction: {trend_direction}
Momentum Signal: {momentum_signal}
Entry Timing: {entry_timing}
Technical Score: {technical_score}/10
Support Level: ${support_level}
Resistance Level: ${resistance_level}
Summary: {technical_summary}

═══════════════════════════════════════════════════════
AGENT 5 — ANALYST SENTIMENT
═══════════════════════════════════════════════════════
Analyst Consensus: {analyst_consensus}
Analyst Price Target: ${analyst_target}  ({analyst_upside}% upside)
News Sentiment: {news_sentiment}
Contrarian Signal: {contrarian_signal}
Narrative Shift: {narrative_shift}
Sentiment Score: {sentiment_score}/10
Summary: {sentiment_summary}

═══════════════════════════════════════════════════════
AGENT 6 — RISK ASSESSMENT
═══════════════════════════════════════════════════════
Overall Risk Level: {overall_risk_level}
Risk Score: {risk_score}/10
Top 3 Risks:
{top_3_risks}
Downside Scenario: {downside_scenario}
Estimated Max Downside: -{downside_pct}%
Summary: {risk_summary}

═══════════════════════════════════════════════════════
Now make your final recommendation.

Return a JSON object with EXACTLY this structure:
{{
  "recommendation": "STRONG BUY|BUY|HOLD|AVOID",
  "confidence": <integer 1-10>,

  "price_target_12m": <float — your 12-month price target>,
  "price_target_rationale": "How you arrived at this target",
  "upside_pct": <float — upside from current price>,
  "downside_risk_pct": <float — downside in bear case>,

  "investment_horizon": "6-12 months|12-18 months|18-24 months",

  "composite_score": <integer 1-10 — weighted average of all agents>,
  "score_breakdown": {{
    "business_quality": <1-10>,
    "financial_strength": <1-10>,
    "valuation": <1-10>,
    "macro_environment": <1-10>,
    "technical_timing": <1-10>,
    "sentiment": <1-10>,
    "risk_adjusted": <1-10>
  }},

  "thesis": "The core investment thesis in 3-5 sentences",
  "bull_case": "The optimistic scenario if things go well (2-3 sentences)",
  "bear_case": "The pessimistic scenario if risks materialise (2-3 sentences)",
  "top_3_risks": ["Risk 1", "Risk 2", "Risk 3"],

  "suggested_entry_zone": "Ideal price range to initiate a position",
  "position_sizing": "conservative|moderate|aggressive",
  "position_sizing_rationale": "Why this position size",

  "key_catalysts_to_watch": ["Catalyst 1", "Catalyst 2", "Catalyst 3"],
  "key_metrics_to_monitor": ["Metric 1", "Metric 2"],

  "executive_summary": "A single compelling paragraph (5-7 sentences) summarising the entire investment case"
}}"""


def _get(d: dict, key: str, default="N/A"):
    val = d.get(key, default)
    return val if val is not None else default


def _fmt_risks(risks: list) -> str:
    if not risks:
        return "  Not available"
    return "\n".join(f"  {i+1}. {r}" for i, r in enumerate(risks[:3]))


def committee_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Chief Investment Analyst Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    current_price = state.get("current_price", 0.0)
    analysis_date = state.get("analysis_date", "")

    mi = state.get("market_intelligence", {})
    macro = state.get("macro_analysis", {})
    fund = state.get("fundamental_analysis", {})
    tech = state.get("technical_analysis", {})
    sent = state.get("sentiment_analysis", {})
    risk = state.get("risk_assessment", {})

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        current_price=current_price,
        analysis_date=analysis_date,
        # Market intelligence
        company_quality_score=_get(mi, "company_quality_score"),
        competitive_advantages=", ".join(_get(mi, "competitive_advantages", [])) if isinstance(_get(mi, "competitive_advantages", []), list) else _get(mi, "competitive_advantages"),
        management_score=_get(mi, "management_score"),
        market_key_insight=_get(mi, "key_insights"),
        # Macro
        macro_verdict=_get(macro, "overall_macro_verdict"),
        sector_macro_impact=_get(macro, "sector_macro_impact"),
        macro_score=_get(macro, "macro_score"),
        key_macro_risk=_get(macro, "key_macro_risk"),
        macro_summary=_get(macro, "macro_summary"),
        # Fundamental
        valuation_verdict=_get(fund, "valuation_verdict"),
        fundamental_score=_get(fund, "fundamental_score"),
        profitability_assessment=_get(fund, "profitability_assessment"),
        profitability_score=_get(fund, "profitability_score"),
        growth_assessment=_get(fund, "growth_assessment"),
        growth_score=_get(fund, "growth_score"),
        balance_sheet_health=_get(fund, "balance_sheet_health"),
        balance_sheet_score=_get(fund, "balance_sheet_score"),
        fcf_quality=_get(fund, "fcf_quality"),
        fcf_score=_get(fund, "fcf_score"),
        fundamental_strengths=", ".join(_get(fund, "key_strengths", []) or []),
        fundamental_weaknesses=", ".join(_get(fund, "key_weaknesses", []) or []),
        fundamental_summary=_get(fund, "fundamental_summary"),
        # Technical
        trend_direction=_get(tech, "trend_direction"),
        momentum_signal=_get(tech, "momentum_signal"),
        entry_timing=_get(tech, "entry_timing"),
        technical_score=_get(tech, "technical_score"),
        support_level=_get(tech, "support_level", 0),
        resistance_level=_get(tech, "resistance_level", 0),
        technical_summary=_get(tech, "technical_summary"),
        # Sentiment
        analyst_consensus=_get(sent, "analyst_consensus"),
        analyst_target=_get(sent, "analyst_price_target_mean", "N/A"),
        analyst_upside=_get(sent, "analyst_upside_pct", "N/A"),
        news_sentiment=_get(sent, "news_sentiment"),
        contrarian_signal=_get(sent, "contrarian_signal"),
        narrative_shift=_get(sent, "narrative_shift"),
        sentiment_score=_get(sent, "sentiment_score"),
        sentiment_summary=_get(sent, "sentiment_summary"),
        # Risk
        overall_risk_level=_get(risk, "overall_risk_level"),
        risk_score=_get(risk, "risk_score"),
        top_3_risks=_fmt_risks(_get(risk, "top_3_risks", [])),
        downside_scenario=_get(risk, "downside_scenario"),
        downside_pct=_get(risk, "downside_pct_estimate", "N/A"),
        risk_summary=_get(risk, "risk_summary"),
    )

    logger.info("Running Chief Investment Analyst Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=3500)

    return {"final_recommendation": result}
