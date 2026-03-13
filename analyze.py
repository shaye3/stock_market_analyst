#!/usr/bin/env python3
"""
analyze.py — CLI entry point for the AI Multi-Agent Stock Analysis System.

Usage:
    python analyze.py AAPL
    python analyze.py MSFT --verbose
    python analyze.py TSLA --output-dir ~/my_reports
    python analyze.py --history AAPL
    python analyze.py --list
"""
import json
import logging
import sys
from pathlib import Path

import click

# Ensure project root is on sys.path when running directly
sys.path.insert(0, str(Path(__file__).parent))

RECOMMENDATION_COLORS = {
    "STRONG BUY": "\033[92m",   # green
    "BUY":        "\033[32m",   # dark green
    "HOLD":       "\033[93m",   # yellow
    "AVOID":      "\033[91m",   # red
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _color(text: str, rec: str) -> str:
    color = RECOMMENDATION_COLORS.get(rec.upper(), "")
    return f"{BOLD}{color}{text}{RESET}"


def _print_summary(state: dict) -> None:
    """Print a concise summary to the terminal after analysis."""
    ticker = state.get("ticker", "")
    company = state.get("company_name", ticker)
    price = state.get("current_price", 0)
    rec = state.get("final_recommendation", {})

    recommendation = rec.get("recommendation", "N/A")
    confidence = rec.get("confidence", "N/A")
    target = rec.get("price_target_12m", "N/A")
    upside = rec.get("upside_pct", "N/A")
    downside = rec.get("downside_risk_pct", "N/A")
    composite = rec.get("composite_score", "N/A")
    horizon = rec.get("investment_horizon", "N/A")
    thesis = rec.get("thesis", "")
    report_path = state.get("report_path", "")

    click.echo()
    click.echo("━" * 70)
    click.echo(f"  {BOLD}{company} ({ticker}){RESET}  |  Current Price: ${price:.2f}")
    click.echo("━" * 70)
    click.echo(f"  Recommendation:  {_color(recommendation, recommendation)}")
    click.echo(f"  Confidence:      {confidence}/10   Composite Score: {composite}/10")
    click.echo(f"  Price Target:    ${target}   ({upside}% upside / -{downside}% downside)")
    click.echo(f"  Horizon:         {horizon}")
    click.echo()
    if thesis:
        click.echo(f"  {BOLD}Thesis:{RESET}")
        # Word-wrap thesis at 65 chars
        words = thesis.split()
        line = "    "
        for word in words:
            if len(line) + len(word) > 67:
                click.echo(line)
                line = "    " + word + " "
            else:
                line += word + " "
        if line.strip():
            click.echo(line)
    click.echo()
    if report_path:
        click.echo(f"  Report saved to: {report_path}/")
    click.echo("━" * 70)
    click.echo()


# ── CLI commands ──────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True, context_settings={"allow_interspersed_args": False})
@click.argument("ticker", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show agent-by-agent progress.")
@click.option("--output-dir", default=None, help="Custom directory for reports.")
@click.option("--json-output", is_flag=True, help="Dump full state as JSON to stdout.")
@click.pass_context
def cli(ctx, ticker, verbose, output_dir, json_output):
    """
    AI Multi-Agent Stock Analysis System.

    Run a full analysis pipeline on a stock ticker.

    \b
    Examples:
        python analyze.py AAPL
        python analyze.py MSFT --verbose
        python analyze.py TSLA --json-output
    """
    if ctx.invoked_subcommand is not None:
        return  # a sub-command was called

    if not ticker:
        click.echo(ctx.get_help())
        return

    from graph.pipeline import run_analysis

    if output_dir:
        # Override the reports directory
        import graph.pipeline as pl_module
        pl_module.REPORTS_DIR = Path(output_dir)

    click.echo(f"\n  Starting analysis for {ticker.upper()} …")
    click.echo("  This may take 1-3 minutes.\n")

    try:
        state = run_analysis(ticker, verbose=verbose)
    except Exception as e:
        click.echo(f"\n  Error during analysis: {e}", err=True)
        sys.exit(1)

    if json_output:
        # Dump full state (without huge price history)
        out = {k: v for k, v in state.items() if k not in ("price_history", "report_markdown")}
        click.echo(json.dumps(out, indent=2, default=str))
    else:
        _print_summary(state)

    if state.get("errors"):
        click.echo(f"  {len(state['errors'])} data warnings — see report for details.\n")


@cli.command()
@click.argument("ticker")
@click.option("--limit", "-n", default=5, help="Number of past analyses to show.")
def history(ticker, limit):
    """Show past analyses for a ticker from the database."""
    from db.database import get_analysis

    rows = get_analysis(ticker.upper(), limit=limit)
    if not rows:
        click.echo(f"\n  No past analyses found for {ticker.upper()}.\n")
        return

    click.echo(f"\n  Past analyses for {ticker.upper()} (most recent first):\n")
    for r in rows:
        rec = r.get("recommendation", "N/A")
        date = r.get("analysis_date", "N/A")
        price = r.get("price_at_analysis", 0)
        target = r.get("price_target_12m", "N/A")
        conf = r.get("confidence", "N/A")
        click.echo(f"  {date}  |  {_color(rec, rec)}  |  Price: ${price:.2f}  Target: ${target}  Conf: {conf}/10")
    click.echo()


@cli.command("list")
@click.option("--limit", "-n", default=20, help="Number of analyses to show.")
def list_analyses(limit):
    """List all analyses in the database."""
    from db.database import list_analyses as _list

    rows = _list(limit=limit)
    if not rows:
        click.echo("\n  No analyses in database yet.\n")
        return

    click.echo(f"\n  Recent analyses (most recent first):\n")
    click.echo(f"  {'DATE':<12} {'TICKER':<8} {'COMPANY':<30} {'REC':<12} {'CONF':<6} {'TARGET'}")
    click.echo("  " + "─" * 80)
    for r in rows:
        rec = r.get("recommendation", "N/A")
        click.echo(
            f"  {r.get('analysis_date', 'N/A'):<12} "
            f"{r.get('ticker', 'N/A'):<8} "
            f"{(r.get('company_name') or '')[:29]:<30} "
            f"{_color(rec, rec):<20} "
            f"{str(r.get('confidence', 'N/A')):<6} "
            f"${r.get('price_target_12m', 'N/A')}"
        )
    click.echo()


if __name__ == "__main__":
    cli()
