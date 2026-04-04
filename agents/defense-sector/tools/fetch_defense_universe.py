#!/usr/bin/env python3
"""
Batch-fetch slim financial metrics for defense universe companies.
Returns: JSON dict keyed by ticker with valuation, profitability, balance sheet, cash flow.

Usage:
    python fetch_defense_universe.py --all
    python fetch_defense_universe.py --batch A
    python fetch_defense_universe.py --tickers LMT RTX NOC
"""

import sys
import json
import argparse
import concurrent.futures
from datetime import datetime

import yfinance as yf
import pandas as pd

# Import config from same directory
sys.path.insert(0, __import__("os").path.dirname(__file__))
from defense_universe_config import UNIVERSE, get_batch, get_tickers


def safe_float(val) -> float | None:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return round(float(val), 4)
    except Exception:
        return None


def safe_int(val) -> int | None:
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return int(val)
    except Exception:
        return None


def fetch_single(yf_ticker: str) -> dict:
    """Fetch slim financials for one ticker. Returns dict or error."""
    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info or {}

        if not info.get("longName") and not info.get("shortName"):
            return {"ticker": yf_ticker, "error": "No data available", "data_quality": "missing"}

        market_cap = safe_int(info.get("marketCap"))
        enterprise_value = safe_int(info.get("enterpriseValue"))
        ebitda = safe_int(info.get("ebitda"))
        fcf = safe_int(info.get("freeCashflow"))
        revenue = safe_int(info.get("totalRevenue"))

        # Compute FCF yield
        fcf_yield = None
        if fcf and market_cap and market_cap > 0:
            fcf_yield = round(fcf / market_cap, 4)

        # Compute price vs 52-week average (from info)
        price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        high_52w = safe_float(info.get("fiftyTwoWeekHigh"))
        low_52w = safe_float(info.get("fiftyTwoWeekLow"))
        avg_52w = None
        pct_above_52w_avg = None
        if high_52w and low_52w:
            avg_52w = round((high_52w + low_52w) / 2, 2)
            if price and avg_52w > 0:
                pct_above_52w_avg = round((price - avg_52w) / avg_52w, 4)

        return {
            "ticker": yf_ticker,
            "name": info.get("longName") or info.get("shortName"),
            "currency": info.get("currency"),
            "data_quality": "full",
            "price": price,
            "market_cap": market_cap,
            "enterprise_value": enterprise_value,
            "valuation": {
                "trailing_pe": safe_float(info.get("trailingPE")),
                "forward_pe": safe_float(info.get("forwardPE")),
                "peg_ratio": safe_float(info.get("pegRatio")),
                "ev_to_ebitda": safe_float(info.get("enterpriseToEbitda")),
                "ev_to_revenue": safe_float(info.get("enterpriseToRevenue")),
                "price_to_book": safe_float(info.get("priceToBook")),
                "price_to_sales": safe_float(info.get("priceToSalesTrailing12Months")),
            },
            "profitability": {
                "gross_margin": safe_float(info.get("grossMargins")),
                "operating_margin": safe_float(info.get("operatingMargins")),
                "net_margin": safe_float(info.get("profitMargins")),
                "roe": safe_float(info.get("returnOnEquity")),
                "roa": safe_float(info.get("returnOnAssets")),
                "ebitda": ebitda,
                "revenue_ttm": revenue,
            },
            "growth": {
                "revenue_growth_yoy": safe_float(info.get("revenueGrowth")),
                "earnings_growth_yoy": safe_float(info.get("earningsGrowth")),
            },
            "balance_sheet": {
                "total_debt": safe_int(info.get("totalDebt")),
                "total_cash": safe_int(info.get("totalCash")),
                "debt_to_equity": safe_float(info.get("debtToEquity")),
                "current_ratio": safe_float(info.get("currentRatio")),
            },
            "cash_flow": {
                "operating_cash_flow": safe_int(info.get("operatingCashflow")),
                "free_cash_flow": fcf,
                "fcf_yield": fcf_yield,
            },
            "price_context": {
                "high_52w": high_52w,
                "low_52w": low_52w,
                "avg_52w": avg_52w,
                "pct_above_52w_avg": pct_above_52w_avg,
            },
            "analyst": {
                "target_mean_price": safe_float(info.get("targetMeanPrice")),
                "recommendation_key": info.get("recommendationKey"),
                "num_analysts": safe_int(info.get("numberOfAnalystOpinions")),
            },
        }
    except Exception as e:
        return {"ticker": yf_ticker, "error": str(e), "data_quality": "error"}


def fetch_batch(yf_tickers: list[str], max_workers: int = 8) -> dict:
    """Fetch financials for multiple tickers in parallel."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_single, t): t for t in yf_tickers}
        for future in concurrent.futures.as_completed(future_map):
            ticker = future_map[future]
            try:
                results[ticker] = future.result()
            except Exception as e:
                results[ticker] = {"ticker": ticker, "error": str(e), "data_quality": "error"}
    return results


def main():
    parser = argparse.ArgumentParser(description="Batch fetch defense universe financials")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Fetch all companies")
    group.add_argument("--batch", choices=["A", "B", "C", "D", "E", "F"],
                       help="Fetch specific batch")
    group.add_argument("--tickers", nargs="+", help="Fetch specific tickers")
    args = parser.parse_args()

    if args.all:
        tickers = get_tickers()
    elif args.batch:
        tickers = get_tickers(args.batch)
    else:
        tickers = args.tickers

    print(f"Fetching financials for {len(tickers)} tickers...", file=sys.stderr)
    results = fetch_batch(tickers)

    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(results),
        "successful": sum(1 for v in results.values() if v.get("data_quality") != "error"),
        "companies": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
