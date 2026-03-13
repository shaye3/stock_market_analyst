"""
Agent 3 — Fundamental Analysis Agent
Evaluates financial strength, profitability, growth, valuation, and balance sheet health.
Investment lens: long-term value investing (6-24 month horizon).
"""
import logging
from typing import Any

from agents.base import BaseAgent
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

_agent = BaseAgent()

SYSTEM_PROMPT = """You are a Fundamental Analysis Agent for an institutional AI investment research team.

You evaluate stocks through a VALUE INVESTING lens (6-24 month holding period).

Your tasks:
1. Assess profitability: margins, ROE, ROIC quality
2. Evaluate growth: revenue, earnings, free cash flow trends
3. Analyse valuation: determine if the stock is undervalued, fairly valued, or overvalued
4. Review balance sheet: debt levels, liquidity, financial stability
5. Compare against sector/industry where possible

Key value metrics to emphasise: P/E, EV/EBITDA, P/FCF, P/B, PEG
A stock is attractive when: low P/E relative to growth, strong FCF, low debt, high ROE.

If data is missing, note it explicitly and reduce confidence accordingly.

Respond with a VALID JSON OBJECT ONLY. No extra text."""

USER_PROMPT_TEMPLATE = """Perform fundamental analysis for {ticker} ({company_name}).

=== VALUATION METRICS ===
Current Price:      ${current_price:.2f}
Market Cap:         ${market_cap_b:.2f}B
Trailing P/E:       {pe_trailing}
Forward P/E:        {pe_forward}
PEG Ratio:          {peg}
Price/Book:         {pb}
Price/Sales:        {ps}
EV/EBITDA:          {ev_ebitda}
Enterprise Value:   ${ev_b}B

=== PROFITABILITY ===
EPS (TTM):          ${eps}
Gross Margin:       {gross_margin}%
Operating Margin:   {op_margin}%
Net Margin:         {net_margin}%
ROE:                {roe}%
ROA:                {roa}%

=== GROWTH (YoY) ===
Revenue Growth:     {rev_growth}%
Earnings Growth:    {earn_growth}%
Quarterly EPS Growth: {qtrly_eps_growth}%

=== BALANCE SHEET ===
Total Debt:         ${total_debt_b:.2f}B
Total Cash:         ${total_cash_b:.2f}B
Net Cash:           ${net_cash_b:.2f}B
Debt/Equity:        {de_ratio}
Current Ratio:      {current_ratio}
Quick Ratio:        {quick_ratio}

=== CASH FLOW ===
Operating Cash Flow: ${op_cf_b:.2f}B
Free Cash Flow:      ${fcf_b:.2f}B
FCF Yield:           {fcf_yield}%
Capex/Revenue:       {capex_pct}%

=== INCOME STATEMENT TREND (last 4 periods) ===
{income_trend}

Return a JSON object with EXACTLY this structure:
{{
  "profitability_assessment": "Strong/Good/Average/Weak",
  "profitability_score": <integer 1-10>,
  "profitability_notes": "Key observations about margins and returns",

  "growth_assessment": "Accelerating/Steady/Decelerating/Declining",
  "growth_score": <integer 1-10>,
  "growth_notes": "Key observations about revenue/earnings/FCF trends",

  "valuation_verdict": "Undervalued|Fairly Valued|Overvalued",
  "valuation_score": <integer 1-10, 10=extremely undervalued>,
  "pe_vs_peers": "cheap|fair|expensive",
  "valuation_notes": "Why the stock is cheap/fair/expensive",
  "intrinsic_value_estimate": "Brief qualitative estimate (e.g. 'worth ~15-20x FCF')",

  "balance_sheet_health": "Strong|Adequate|Stretched|Distressed",
  "balance_sheet_score": <integer 1-10>,
  "debt_concern_level": "none|low|medium|high",
  "balance_sheet_notes": "Key balance sheet observations",

  "fcf_quality": "Excellent|Good|Fair|Poor|Negative",
  "fcf_score": <integer 1-10>,

  "fundamental_score": <integer 1-10, overall fundamental attractiveness>,
  "key_strengths": ["strength 1", "strength 2", "strength 3"],
  "key_weaknesses": ["weakness 1", "weakness 2"],
  "fundamental_summary": "2-3 sentence overall fundamental assessment"
}}"""


def _v(info: dict, key: str, default="N/A") -> Any:
    val = info.get(key)
    if val is None:
        return default
    if isinstance(val, float) and val != val:  # NaN check
        return default
    return val


def _pct(info: dict, key: str) -> str:
    val = info.get(key)
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}"
    except (TypeError, ValueError):
        return "N/A"


def _bil(info: dict, key: str) -> float:
    val = info.get(key)
    if val is None:
        return 0.0
    try:
        return float(val) / 1e9
    except (TypeError, ValueError):
        return 0.0


def _format_income_trend(income_stmt: dict) -> str:
    if not income_stmt:
        return "  (Not available)"
    lines = []
    for period, data in sorted(income_stmt.items(), reverse=True):
        rev = data.get("Total Revenue")
        ni = data.get("Net Income")
        rev_str = f"${rev/1e9:.2f}B" if rev else "N/A"
        ni_str = f"${ni/1e9:.2f}B" if ni else "N/A"
        lines.append(f"  {period}: Revenue={rev_str}  Net Income={ni_str}")
    return "\n".join(lines[:4])


def fundamental_analysis_node(state: AnalysisState) -> dict:
    """LangGraph node — runs the Fundamental Analysis Agent."""
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", ticker)
    info = state.get("info", {})
    financials = state.get("financials", {})
    current_price = state.get("current_price", 0.0)

    market_cap = info.get("marketCap") or 0
    ev = info.get("enterpriseValue") or 0
    total_debt = info.get("totalDebt") or 0
    total_cash = info.get("totalCash") or 0
    op_cf = info.get("operatingCashflow") or 0
    fcf = info.get("freeCashflow") or 0
    capex = op_cf - fcf if op_cf and fcf else 0
    total_rev = info.get("totalRevenue") or 1  # avoid div/0
    fcf_yield = (fcf / market_cap * 100) if market_cap and fcf else 0
    capex_pct = (capex / total_rev * 100) if total_rev and capex else 0

    user_prompt = USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        current_price=current_price,
        market_cap_b=market_cap / 1e9,
        pe_trailing=f"{_v(info, 'trailingPE'):.1f}" if isinstance(_v(info, "trailingPE"), float) else _v(info, "trailingPE"),
        pe_forward=f"{_v(info, 'forwardPE'):.1f}" if isinstance(_v(info, "forwardPE"), float) else _v(info, "forwardPE"),
        peg=f"{_v(info, 'pegRatio'):.2f}" if isinstance(_v(info, "pegRatio"), float) else _v(info, "pegRatio"),
        pb=f"{_v(info, 'priceToBook'):.2f}" if isinstance(_v(info, "priceToBook"), float) else _v(info, "priceToBook"),
        ps=f"{_v(info, 'priceToSalesTrailingTwelveMonths'):.2f}" if isinstance(_v(info, "priceToSalesTrailingTwelveMonths"), float) else _v(info, "priceToSalesTrailingTwelveMonths"),
        ev_ebitda=f"{_v(info, 'enterpriseToEbitda'):.1f}" if isinstance(_v(info, "enterpriseToEbitda"), float) else _v(info, "enterpriseToEbitda"),
        ev_b=f"{ev/1e9:.2f}" if ev else "N/A",
        eps=f"{_v(info, 'trailingEps')}" if _v(info, 'trailingEps') != "N/A" else "N/A",
        gross_margin=_pct(info, "grossMargins"),
        op_margin=_pct(info, "operatingMargins"),
        net_margin=_pct(info, "profitMargins"),
        roe=_pct(info, "returnOnEquity"),
        roa=_pct(info, "returnOnAssets"),
        rev_growth=_pct(info, "revenueGrowth"),
        earn_growth=_pct(info, "earningsGrowth"),
        qtrly_eps_growth=_pct(info, "earningsQuarterlyGrowth"),
        total_debt_b=total_debt / 1e9,
        total_cash_b=total_cash / 1e9,
        net_cash_b=(total_cash - total_debt) / 1e9,
        de_ratio=f"{_v(info, 'debtToEquity'):.1f}" if isinstance(_v(info, "debtToEquity"), float) else _v(info, "debtToEquity"),
        current_ratio=f"{_v(info, 'currentRatio'):.2f}" if isinstance(_v(info, "currentRatio"), float) else _v(info, "currentRatio"),
        quick_ratio=f"{_v(info, 'quickRatio'):.2f}" if isinstance(_v(info, "quickRatio"), float) else _v(info, "quickRatio"),
        op_cf_b=op_cf / 1e9,
        fcf_b=fcf / 1e9,
        fcf_yield=f"{fcf_yield:.1f}",
        capex_pct=f"{capex_pct:.1f}",
        income_trend=_format_income_trend(financials.get("income_stmt", {})),
    )

    logger.info("Running Fundamental Analysis Agent for %s", ticker)
    result = _agent.call_and_parse(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    return {"fundamental_analysis": result}
