"""
LangGraph pipeline — wires all agents into a sequential state graph.

Flow:
  fetch_data → market_intelligence → macro → fundamental → technical
             → sentiment → risk → committee → write_report → save_to_db
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langgraph.graph import StateGraph, START, END

from agents.committee import committee_node
from agents.fundamental import fundamental_analysis_node
from agents.macro import macro_analysis_node
from agents.market_intelligence import market_intelligence_node
from agents.risk import risk_assessment_node
from agents.sentiment import sentiment_analysis_node
from agents.technical import technical_analysis_node
from data.fetcher import fetch_stock_data
from db.database import save_analysis
from graph.state import AnalysisState

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
REPORTS_DIR = Path(__file__).parent.parent / "reports"


# ── Fetch node ───────────────────────────────────────────────────────────────

def fetch_data_node(state: AnalysisState) -> dict:
    """Fetch all raw data from yfinance and populate state."""
    ticker = state.get("ticker", "")
    logger.info("Fetching data for %s …", ticker)

    data = fetch_stock_data(ticker)

    errors = list(state.get("errors", []))
    if data.get("errors"):
        errors.extend([f"[fetcher] {e}" for e in data["errors"]])

    return {
        "company_name": data["company_name"],
        "current_price": data["current_price"],
        "info": data["info"],
        "price_history": data["price_history"],
        "financials": data["financials"],
        "news": data["news"],
        "analyst_recommendations": data["analyst_recommendations"],
        "errors": errors,
    }


# ── Report writer node ───────────────────────────────────────────────────────

def write_report_node(state: AnalysisState) -> dict:
    """Render Markdown + HTML investment memo from the Jinja2 template."""
    ticker = state.get("ticker", "")
    analysis_date = state.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
    report_dir = REPORTS_DIR / f"{ticker}_{analysis_date}"
    report_dir.mkdir(parents=True, exist_ok=True)

    try:
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("report.md.j2")
        markdown = template.render(**state)

        md_path = report_dir / "report.md"
        md_path.write_text(markdown, encoding="utf-8")

        # Basic HTML wrapper
        html_content = _md_to_html(markdown, ticker, state.get("company_name", ""))
        html_path = report_dir / "report.html"
        html_path.write_text(html_content, encoding="utf-8")

        logger.info("Report written to %s", report_dir)
        return {"report_markdown": markdown, "report_path": str(report_dir)}

    except Exception as e:
        logger.error("Report generation failed: %s", e)
        errors = list(state.get("errors", []))
        errors.append(f"[report_writer] {e}")
        return {"report_path": str(report_dir), "errors": errors}


def _md_to_html(markdown: str, ticker: str, company_name: str) -> str:
    """Wrap markdown in a minimal styled HTML page."""
    # Convert basic markdown to HTML (minimal, no heavy dep needed)
    import re
    html = markdown
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*</li>)", r"<ul>\1</ul>", html, flags=re.DOTALL)
    html = re.sub(r"^(?!<[hul])(.+)$", r"<p>\1</p>", html, flags=re.MULTILINE)
    html = html.replace("\n\n", "\n")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} ({ticker}) — Investment Research</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6;
         color: #1a1a1a; }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #e63946; padding-bottom: 8px; }}
  h2 {{ color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-top: 2em; }}
  h3 {{ color: #0f3460; }}
  strong {{ color: #1a1a1a; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
  blockquote {{ border-left: 4px solid #e63946; margin: 0; padding: 0 16px; color: #555; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #f4f4f4; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #1a1a1a; color: #e0e0e0; }}
    h1, h2, h3 {{ color: #e0e0e0; }}
    blockquote {{ color: #aaa; }}
    code {{ background: #333; color: #e0e0e0; }}
    th {{ background: #333; }}
    td, th {{ border-color: #555; }}
  }}
</style>
</head>
<body>
{html}
</body>
</html>"""


# ── DB save node ─────────────────────────────────────────────────────────────

def save_to_db_node(state: AnalysisState) -> dict:
    """Persist the analysis to SQLite."""
    try:
        save_analysis(dict(state))
    except Exception as e:
        logger.error("DB save failed: %s", e)
        errors = list(state.get("errors", []))
        errors.append(f"[db_save] {e}")
        return {"errors": errors}
    return {}


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_pipeline():
    """Compile and return the full analysis pipeline as a LangGraph."""
    builder = StateGraph(AnalysisState)

    # Register nodes
    builder.add_node("fetch_data", fetch_data_node)
    builder.add_node("market_intelligence", market_intelligence_node)
    builder.add_node("macro_analysis", macro_analysis_node)
    builder.add_node("fundamental_analysis", fundamental_analysis_node)
    builder.add_node("technical_analysis", technical_analysis_node)
    builder.add_node("sentiment_analysis", sentiment_analysis_node)
    builder.add_node("risk_assessment", risk_assessment_node)
    builder.add_node("committee", committee_node)
    builder.add_node("write_report", write_report_node)
    builder.add_node("save_to_db", save_to_db_node)

    # Sequential edges
    builder.add_edge(START, "fetch_data")
    builder.add_edge("fetch_data", "market_intelligence")
    builder.add_edge("market_intelligence", "macro_analysis")
    builder.add_edge("macro_analysis", "fundamental_analysis")
    builder.add_edge("fundamental_analysis", "technical_analysis")
    builder.add_edge("technical_analysis", "sentiment_analysis")
    builder.add_edge("sentiment_analysis", "risk_assessment")
    builder.add_edge("risk_assessment", "committee")
    builder.add_edge("committee", "write_report")
    builder.add_edge("write_report", "save_to_db")
    builder.add_edge("save_to_db", END)

    return builder.compile()


def run_analysis(ticker: str, verbose: bool = False) -> dict:
    """
    Run the full analysis pipeline for a given ticker.
    Returns the final state dict.
    """
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(name)-30s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        logging.basicConfig(level=logging.WARNING)

    pipeline = build_pipeline()

    initial_state: AnalysisState = {
        "ticker": ticker.upper(),
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "company_name": "",
        "current_price": 0.0,
        "info": {},
        "price_history": [],
        "financials": {},
        "news": [],
        "analyst_recommendations": [],
        "market_intelligence": {},
        "macro_analysis": {},
        "fundamental_analysis": {},
        "technical_analysis": {},
        "sentiment_analysis": {},
        "risk_assessment": {},
        "final_recommendation": {},
        "report_markdown": "",
        "report_path": "",
        "errors": [],
    }

    logger.info("Starting analysis pipeline for %s", ticker.upper())
    final_state = pipeline.invoke(initial_state)
    return final_state
