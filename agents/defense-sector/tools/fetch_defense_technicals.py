#!/usr/bin/env python3
"""
Batch-fetch price data + compute beta vs ITA benchmark for defense universe.
Returns: JSON dict keyed by ticker with price stats, beta, momentum metrics.

Usage:
    python fetch_defense_technicals.py --all
    python fetch_defense_technicals.py --batch A
    python fetch_defense_technicals.py --tickers LMT RTX NOC
    python fetch_defense_technicals.py --tickers ITA  (benchmark only)
"""

import sys
import json
import argparse
import concurrent.futures
from datetime import datetime

import yfinance as yf
import pandas as pd
import numpy as np

sys.path.insert(0, __import__("os").path.dirname(__file__))
from defense_universe_config import UNIVERSE, get_batch, get_tickers, BENCHMARK_PROXY


def safe_float(val) -> float | None:
    try:
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return None
        return round(float(val), 4)
    except Exception:
        return None


def compute_beta(stock_returns: pd.Series, benchmark_returns: pd.Series) -> float | None:
    """Compute beta of stock vs benchmark using 1-year daily returns."""
    try:
        aligned = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 60:
            return None
        cov = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
        var = aligned.iloc[:, 1].var()
        if var == 0:
            return None
        return round(cov / var, 3)
    except Exception:
        return None


def fetch_single_price(yf_ticker: str, period: str = "1y") -> dict:
    """Fetch price data and compute momentum metrics for one ticker."""
    try:
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period=period)

        if hist.empty or len(hist) < 20:
            return {"ticker": yf_ticker, "error": "Insufficient price data", "data_quality": "missing"}

        close = hist["Close"]
        current = float(close.iloc[-1])
        high_52w = float(hist["High"].max())
        low_52w = float(hist["Low"].min())

        # SMA crossover signals
        sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        sma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = safe_float(rsi.iloc[-1])

        # Returns
        daily_returns = close.pct_change().dropna()
        pct_1m = safe_float((close.iloc[-1] / close.iloc[-22] - 1) * 100) if len(close) >= 22 else None
        pct_3m = safe_float((close.iloc[-1] / close.iloc[-66] - 1) * 100) if len(close) >= 66 else None
        pct_6m = safe_float((close.iloc[-1] / close.iloc[-132] - 1) * 100) if len(close) >= 132 else None
        pct_1y = safe_float((close.iloc[-1] / close.iloc[0] - 1) * 100)

        # Volatility (annualized)
        vol_30d = safe_float(daily_returns.tail(30).std() * np.sqrt(252) * 100)

        return {
            "ticker": yf_ticker,
            "data_quality": "full",
            "price": round(current, 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "sma_200": round(sma_200, 2) if sma_200 else None,
            "above_sma_50": current > sma_50 if sma_50 else None,
            "above_sma_200": current > sma_200 if sma_200 else None,
            "rsi_14": rsi_val,
            "returns": {
                "pct_1m": pct_1m,
                "pct_3m": pct_3m,
                "pct_6m": pct_6m,
                "pct_1y": pct_1y,
            },
            "volatility_30d_ann": vol_30d,
            "avg_volume_30d": int(hist["Volume"].tail(30).mean()),
            "_daily_returns": daily_returns,  # for beta computation, stripped before output
        }
    except Exception as e:
        return {"ticker": yf_ticker, "error": str(e), "data_quality": "error"}


def fetch_batch_technicals(yf_tickers: list[str], max_workers: int = 8) -> dict:
    """Fetch price data for multiple tickers, compute beta vs ITA."""
    # Always fetch ITA for benchmark
    all_tickers = list(set(yf_tickers + ["ITA"]))

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_single_price, t): t for t in all_tickers}
        for future in concurrent.futures.as_completed(future_map):
            ticker = future_map[future]
            try:
                results[ticker] = future.result()
            except Exception as e:
                results[ticker] = {"ticker": ticker, "error": str(e), "data_quality": "error"}

    # Compute beta vs ITA for each stock
    ita_data = results.get("ITA", {})
    ita_returns = ita_data.get("_daily_returns")

    for ticker, data in results.items():
        if ticker == "ITA":
            continue
        stock_returns = data.get("_daily_returns")
        if stock_returns is not None and ita_returns is not None:
            data["beta_vs_ita"] = compute_beta(stock_returns, ita_returns)
        else:
            data["beta_vs_ita"] = None

    # Strip internal _daily_returns before output
    for data in results.values():
        data.pop("_daily_returns", None)

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch fetch defense universe technicals")
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

    print(f"Fetching technicals for {len(tickers)} tickers + ITA benchmark...", file=sys.stderr)
    results = fetch_batch_technicals(tickers)

    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(results),
        "successful": sum(1 for v in results.values() if v.get("data_quality") != "error"),
        "benchmark": "ITA",
        "companies": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
