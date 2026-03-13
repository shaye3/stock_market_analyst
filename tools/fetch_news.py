#!/usr/bin/env python3
"""
Fetch recent news and company metadata for a stock ticker using yfinance.
Output: JSON with news headlines, summaries, and company info.

Usage: python fetch_news.py AAPL [--limit 20]
"""

import sys
import json
import argparse
import yfinance as yf
from datetime import datetime


def fetch_news(ticker: str, limit: int = 20) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    # ── Company Profile ───────────────────────────────────────────────────────
    profile = {
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "website": info.get("website"),
        "summary": (info.get("longBusinessSummary") or "")[:800],
        "ceo": info.get("companyOfficers", [{}])[0].get("name") if info.get("companyOfficers") else None,
        "employees": info.get("fullTimeEmployees"),
    }

    # ── Major Holders ─────────────────────────────────────────────────────────
    holders = {}
    try:
        inst = stock.institutional_holders
        if inst is not None and not inst.empty:
            holders["top_institutional"] = inst.head(5).to_dict(orient="records")
    except Exception:
        pass

    try:
        major = stock.major_holders
        if major is not None and not major.empty:
            holders["major_holders_summary"] = major.to_dict(orient="records")
    except Exception:
        pass

    # ── News ─────────────────────────────────────────────────────────────────
    news_items = []
    try:
        raw_news = stock.news or []
        for item in raw_news[:limit]:
            content = item.get("content", {})
            pub_date = content.get("pubDate", "")
            title = content.get("title", item.get("title", ""))
            summary = content.get("summary", "")
            provider = content.get("provider", {}).get("displayName", "") if isinstance(content.get("provider"), dict) else ""
            url = ""
            if isinstance(content.get("canonicalUrl"), dict):
                url = content["canonicalUrl"].get("url", "")
            elif isinstance(content.get("clickThroughUrl"), dict):
                url = content["clickThroughUrl"].get("url", "")

            news_items.append({
                "title": title,
                "summary": summary[:300] if summary else "",
                "publisher": provider,
                "published": pub_date,
                "url": url,
            })
    except Exception as e:
        news_items = [{"error": str(e)}]

    # ── Earnings Calendar ─────────────────────────────────────────────────────
    earnings_info = {}
    try:
        cal = stock.calendar
        if cal:
            earnings_info = {k: str(v) for k, v in cal.items()}
    except Exception:
        pass

    # ── Recent Earnings ───────────────────────────────────────────────────────
    earnings_history = []
    try:
        eh = stock.earnings_history
        if eh is not None and not eh.empty:
            for _, row in eh.head(8).iterrows():
                earnings_history.append({
                    "date": str(row.get("Earnings Date", ""))[:10],
                    "eps_estimate": round(float(row["EPS Estimate"]), 2) if row.get("EPS Estimate") else None,
                    "eps_actual": round(float(row["Reported EPS"]), 2) if row.get("Reported EPS") else None,
                    "surprise_pct": round(float(row["Surprise(%)"]), 2) if row.get("Surprise(%)") else None,
                })
    except Exception:
        pass

    return {
        "ticker": ticker.upper(),
        "company_profile": profile,
        "shareholders": holders,
        "recent_news": news_items,
        "earnings_calendar": earnings_info,
        "earnings_history": earnings_history,
        "data_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch stock news and company info")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("--limit", type=int, default=20, help="Max news items")
    args = parser.parse_args()

    result = fetch_news(args.ticker, args.limit)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
