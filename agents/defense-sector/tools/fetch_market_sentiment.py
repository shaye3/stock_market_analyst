#!/usr/bin/env python3
"""
Fetch quantitative market sentiment signals for defense-sector companies.
Pulls analyst consensus, price targets, and institutional ownership from yfinance.

Produces structured JSON input for the market_sentiment sub-agent, which adds
qualitative signals (news frequency, analyst upgrade actions, featured lists)
via WebSearch.

Usage:
    python fetch_market_sentiment.py --all
    python fetch_market_sentiment.py --batch A
    python fetch_market_sentiment.py --tickers LMT RTX NOC
"""

import sys
import json
import time
import argparse
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from defense_universe_config import UNIVERSE, get_batch

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance not installed", file=sys.stderr)
    sys.exit(1)


def fetch_company_sentiment(company_key: str, yf_ticker: str) -> dict:
    """
    Fetch quantitative sentiment signals for one company via yfinance.
    Returns a dict with analyst consensus, price targets, and institutional data.
    """
    result = {
        "company_key": company_key,
        "yf_ticker": yf_ticker,
        "analyst_buy_count": None,
        "analyst_hold_count": None,
        "analyst_sell_count": None,
        "analyst_total_count": None,
        "mean_target_price": None,
        "low_target_price": None,
        "high_target_price": None,
        "current_price": None,
        "upside_pct": None,
        "recommendation_mean": None,    # 1=Strong Buy ... 5=Sell
        "institutional_holders_count": None,
        "institutional_ownership_pct": None,
        "data_quality": "none",
    }

    try:
        stock = yf.Ticker(yf_ticker)
        info = stock.info or {}

        # ── Current price ────────────────────────────────────────────────────
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        result["current_price"] = current_price

        # ── Analyst consensus ────────────────────────────────────────────────
        rec_mean = info.get("recommendationMean")
        num_analysts = info.get("numberOfAnalystOpinions", 0)
        result["recommendation_mean"] = rec_mean
        result["analyst_total_count"] = num_analysts

        # ── Price targets ────────────────────────────────────────────────────
        mean_pt = info.get("targetMeanPrice")
        low_pt = info.get("targetLowPrice")
        high_pt = info.get("targetHighPrice")
        result["mean_target_price"] = mean_pt
        result["low_target_price"] = low_pt
        result["high_target_price"] = high_pt

        if mean_pt and current_price and current_price > 0:
            result["upside_pct"] = round((mean_pt - current_price) / current_price, 4)

        # ── Buy/Hold/Sell breakdown from recommendations_summary ─────────────
        try:
            rec_summary = stock.recommendations_summary
            if rec_summary is not None and not rec_summary.empty:
                latest = rec_summary.iloc[0]
                result["analyst_buy_count"] = int(
                    (latest.get("strongBuy", 0) or 0) + (latest.get("buy", 0) or 0)
                )
                result["analyst_hold_count"] = int(latest.get("hold", 0) or 0)
                result["analyst_sell_count"] = int(
                    (latest.get("underperform", 0) or 0) + (latest.get("sell", 0) or 0)
                )
        except Exception:
            pass  # Graceful — sub-agent will fill from WebSearch

        # ── Institutional ownership ──────────────────────────────────────────
        try:
            maj = stock.major_holders
            if maj is not None and not maj.empty:
                for _, row in maj.iterrows():
                    label = str(row.get("Breakdown", "")).lower()
                    if "institution" in label:
                        pct_str = str(row.get("Value", "")).replace("%", "").strip()
                        try:
                            result["institutional_ownership_pct"] = round(
                                float(pct_str) / 100, 4
                            )
                        except ValueError:
                            pass
        except Exception:
            pass

        try:
            inst_holders = stock.institutional_holders
            if inst_holders is not None and not inst_holders.empty:
                result["institutional_holders_count"] = len(inst_holders)
        except Exception:
            pass

        # ── Determine data quality ───────────────────────────────────────────
        has_analyst = result["recommendation_mean"] is not None or result["analyst_total_count"]
        has_price_target = result["mean_target_price"] is not None
        has_institutional = result["institutional_ownership_pct"] is not None

        if has_analyst and has_price_target and has_institutional:
            result["data_quality"] = "full"
        elif has_analyst or has_price_target:
            result["data_quality"] = "partial"
        else:
            result["data_quality"] = "none"

    except Exception as e:
        result["error"] = str(e)
        result["data_quality"] = "none"

    return result


def fetch_batch_sentiment(company_keys: list[str], sleep_sec: float = 0.5) -> dict:
    """Fetch sentiment data for a list of company_keys. Returns {company_key: data}."""
    output = {}
    for i, company_key in enumerate(company_keys, 1):
        company_info = UNIVERSE.get(company_key, {})
        yf_ticker = company_info.get("yf_ticker", company_key)
        print(
            f"  [{i}/{len(company_keys)}] {company_key} ({yf_ticker})...",
            file=sys.stderr,
        )
        data = fetch_company_sentiment(company_key, yf_ticker)
        output[company_key] = data
        if i < len(company_keys):
            time.sleep(sleep_sec)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Fetch quantitative sentiment signals for defense companies"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="All 66 companies")
    group.add_argument(
        "--batch", choices=["A", "B", "C", "D", "E", "F"], help="Single batch"
    )
    group.add_argument(
        "--tickers", nargs="+", metavar="TICKER", help="Specific company_keys (e.g. LMT RTX)"
    )
    parser.add_argument(
        "--sleep", type=float, default=0.5, help="Sleep seconds between tickers (default 0.5)"
    )
    args = parser.parse_args()

    # Determine target company keys
    if args.all:
        company_keys = list(UNIVERSE.keys())
        label = "all"
    elif args.batch:
        company_keys = list(get_batch(args.batch).keys())
        label = f"batch {args.batch}"
    else:
        company_keys = args.tickers
        label = "custom"

    print(
        f"Fetching sentiment data for {len(company_keys)} companies ({label})...",
        file=sys.stderr,
    )

    companies = fetch_batch_sentiment(company_keys, sleep_sec=args.sleep)

    # Summary stats
    full_count = sum(1 for v in companies.values() if v["data_quality"] == "full")
    partial_count = sum(1 for v in companies.values() if v["data_quality"] == "partial")
    none_count = sum(1 for v in companies.values() if v["data_quality"] == "none")
    print(
        f"Done: {full_count} full, {partial_count} partial, {none_count} no-data",
        file=sys.stderr,
    )

    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "yfinance",
        "companies_requested": len(company_keys),
        "data_quality_summary": {
            "full": full_count,
            "partial": partial_count,
            "none": none_count,
        },
        "companies": companies,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
