"""
Agent 5 — Analyst Sentiment Agent
Analyses professional analyst opinions, news sentiment, and institutional commentary.
"""
import logging

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are an Analyst Sentiment Agent for an institutional AI investment research team.

Your role is to synthesise sentiment from multiple sources:
1. Professional analyst ratings and price targets
2. Recent news sentiment (positive, neutral, or negative narratives)
3. Institutional and hedge fund commentary where available

Critical thinking rules:
- Do NOT blindly accept analyst consensus — identify potential biases
- Highlight when analysts disagree significantly
- Note if a narrative shift is occurring (e.g., previously bearish analysts upgrading)
- Verify whether analyst claims are supported by the fundamental data
- Identify sentiment extremes (extreme bullishness can be a contrarian sell signal)

For a value investor, the most interesting sentiment signal is:
  - Analyst pessimism / low ratings on a fundamentally sound company (potential opportunity)
  - Recent upgrades after a large selloff (momentum confirmation)

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Analyse analyst sentiment for {ticker} ({company_name}).

=== ANALYST CONSENSUS (from yfinance) ===
Consensus Rating:    {recommendation_key}
Number of Analysts:  {num_analysts}
Mean Price Target:   ${target_mean}
High Price Target:   ${target_high}
Low Price Target:    ${target_low}
Implied Upside:      {implied_upside}%

=== RECENT ANALYST ACTIONS ===
{analyst_actions}

=== RECENT NEWS HEADLINES ({news_count} items) ===
{news_headlines}

=== FUNDAMENTAL CONTEXT ===
Valuation verdict: {valuation_verdict}
Fundamental score: {fundamental_score}/10

Using the above, perform a critical sentiment analysis.

Return a JSON object with EXACTLY this structure:
{{
  "news_sentiment": "bullish|neutral|bearish",
  "news_sentiment_explanation": "What the news narrative says about this company",

  "analyst_consensus": "strong_buy|buy|hold|sell|strong_sell",
  "analyst_consensus_confidence": "high|medium|low",
  "analyst_price_target_mean": <float>,
  "analyst_upside_pct": <float>,
  "analyst_disagreement": "high|medium|low",

  "analyst_bias_assessment": "Potential biases in analyst coverage",
  "contrarian_signal": "none|mildly_contrarian_bullish|strongly_contrarian_bullish|mildly_contrarian_bearish|strongly_contrarian_bearish",
  "contrarian_explanation": "Why the contrarian signal (if any) is relevant",

  "narrative_shift": "positive_shift|stable|negative_shift",
  "narrative_shift_explanation": "Whether analyst/media sentiment is improving or deteriorating",

  "institutional_activity": "accumulating|neutral|distributing|unknown",

  "sentiment_score": <integer 1-10, where 10=extremely bullish sentiment>,
  "sentiment_summary": "2-3 sentence overall sentiment assessment"
}}"""


def _format_analyst_actions(recs: list) -> str:
    if not recs:
        return "  No recent analyst actions available."
    lines = []
    for r in recs[:10]:
        period = r.get("period", r.get("Date", "N/A"))
        firm = r.get("Firm", r.get("firm", "Unknown Firm"))
        action = r.get("Action", r.get("action", ""))
        to_grade = r.get("To Grade", r.get("toGrade", ""))
        from_grade = r.get("From Grade", r.get("fromGrade", ""))
        if to_grade:
            line = f"  [{period}] {firm}: {action} → {to_grade}"
            if from_grade:
                line += f" (from {from_grade})"
            lines.append(line)
    return "\n".join(lines) if lines else "  No structured analyst actions available."


def _format_news_headlines(news: list) -> str:
    if not news:
        return "  No recent news available."
    lines = []
    for i, n in enumerate(news[:12], 1):
        title = n.get("title", "").strip()
        pub = n.get("publisher", "")
        if title:
            lines.append(f"  {i}. [{pub}] {title}")
    return "\n".join(lines)


def sentiment_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Analyst Sentiment Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    info = state.get("info", {})
    news = state.get("news", [])
    recs = state.get("analyst_recommendations", [])
    fundamental = state.get("fundamental_analysis", {})

    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    current_price = state.get("current_price", 0)

    implied_upside = "N/A"
    if target_mean and current_price:
        try:
            implied_upside = f"{(float(target_mean) / float(current_price) - 1) * 100:.1f}"
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        recommendation_key=info.get("recommendationKey", "N/A").upper(),
        num_analysts=info.get("numberOfAnalystOpinions", "N/A"),
        target_mean=f"{target_mean:.2f}" if target_mean else "N/A",
        target_high=f"{target_high:.2f}" if target_high else "N/A",
        target_low=f"{target_low:.2f}" if target_low else "N/A",
        implied_upside=implied_upside,
        analyst_actions=_format_analyst_actions(recs if isinstance(recs, list) else []),
        news_count=len(news),
        news_headlines=_format_news_headlines(news),
        valuation_verdict=fundamental.get("valuation_verdict", "N/A"),
        fundamental_score=fundamental.get("fundamental_score", "N/A"),
    )

    logger.info("Running Analyst Sentiment Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    return {"sentiment_analysis": result}
