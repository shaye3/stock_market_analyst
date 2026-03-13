#!/usr/bin/env python3
"""
Fetch historical price data for a stock ticker using yfinance.
Output: JSON with OHLCV data and basic price statistics.

Usage: python fetch_price_data.py AAPL [--period 1y]
"""

import sys
import json
import argparse
import yfinance as yf
import pandas as pd
from datetime import datetime


def fetch_price_data(ticker: str, period: str = "1y") -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    if hist.empty:
        return {"error": f"No price data found for {ticker}"}

    hist.index = hist.index.strftime("%Y-%m-%d")
    current_price = float(hist["Close"].iloc[-1])
    price_52w_high = float(hist["High"].max())
    price_52w_low = float(hist["Low"].min())
    avg_volume_30d = int(hist["Volume"].tail(30).mean())
    price_change_1y = float(
        ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
    )

    # Recent 90 days for context
    recent = hist.tail(90)

    return {
        "ticker": ticker.upper(),
        "period": period,
        "current_price": round(current_price, 2),
        "price_52w_high": round(price_52w_high, 2),
        "price_52w_low": round(price_52w_low, 2),
        "price_change_1y_pct": round(price_change_1y, 2),
        "avg_volume_30d": avg_volume_30d,
        "data_points": len(hist),
        "date_range": {
            "start": hist.index[0],
            "end": hist.index[-1],
        },
        "recent_90d": {
            "dates": recent.index.tolist(),
            "close": [round(x, 2) for x in recent["Close"].tolist()],
            "volume": [int(x) for x in recent["Volume"].tolist()],
            "high": [round(x, 2) for x in recent["High"].tolist()],
            "low": [round(x, 2) for x in recent["Low"].tolist()],
        },
        "full_close_series": {
            date: round(float(price), 2)
            for date, price in hist["Close"].items()
        },
        "full_volume_series": {
            date: int(vol)
            for date, vol in hist["Volume"].items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch stock price data")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("--period", default="1y", help="Period: 1y, 2y, 6mo, etc.")
    args = parser.parse_args()

    result = fetch_price_data(args.ticker, args.period)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
