#!/usr/bin/env python3
"""
Fetch fundamental financial data for a stock ticker using yfinance.
Output: JSON with income statement, balance sheet, cash flow, and key metrics.

Usage: python fetch_financials.py AAPL
"""

import sys
import json
import argparse
import yfinance as yf
import pandas as pd


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


def df_to_dict(df: pd.DataFrame, max_cols: int = 4) -> dict:
    """Convert a yfinance DataFrame (rows=metrics, cols=dates) to a clean dict."""
    if df is None or df.empty:
        return {}
    result = {}
    df = df.iloc[:, :max_cols]  # Keep up to max_cols most recent periods
    for col in df.columns:
        col_label = str(col)[:10] if hasattr(col, '__str__') else str(col)
        result[col_label] = {}
        for idx in df.index:
            val = df.loc[idx, col]
            result[col_label][str(idx)] = safe_float(val)
    return result


def fetch_financials(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    # ── Key Stats from info ──────────────────────────────────────────────────
    key_stats = {
        "company_name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "employees": safe_int(info.get("fullTimeEmployees")),
        "market_cap": safe_int(info.get("marketCap")),
        "enterprise_value": safe_int(info.get("enterpriseValue")),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "website": info.get("website"),
        "business_summary": (info.get("longBusinessSummary") or "")[:500],
    }

    # ── Valuation ────────────────────────────────────────────────────────────
    valuation = {
        "trailing_pe": safe_float(info.get("trailingPE")),
        "forward_pe": safe_float(info.get("forwardPE")),
        "peg_ratio": safe_float(info.get("pegRatio")),
        "price_to_sales": safe_float(info.get("priceToSalesTrailing12Months")),
        "price_to_book": safe_float(info.get("priceToBook")),
        "ev_to_ebitda": safe_float(info.get("enterpriseToEbitda")),
        "ev_to_revenue": safe_float(info.get("enterpriseToRevenue")),
    }

    # ── Profitability ────────────────────────────────────────────────────────
    profitability = {
        "gross_margin": safe_float(info.get("grossMargins")),
        "operating_margin": safe_float(info.get("operatingMargins")),
        "net_margin": safe_float(info.get("profitMargins")),
        "roe": safe_float(info.get("returnOnEquity")),
        "roa": safe_float(info.get("returnOnAssets")),
        "ebitda": safe_int(info.get("ebitda")),
        "trailing_eps": safe_float(info.get("trailingEps")),
        "forward_eps": safe_float(info.get("forwardEps")),
    }

    # ── Growth ───────────────────────────────────────────────────────────────
    growth = {
        "revenue_growth_yoy": safe_float(info.get("revenueGrowth")),
        "earnings_growth_yoy": safe_float(info.get("earningsGrowth")),
        "earnings_quarterly_growth": safe_float(info.get("earningsQuarterlyGrowth")),
        "revenue_ttm": safe_int(info.get("totalRevenue")),
    }

    # ── Balance Sheet ────────────────────────────────────────────────────────
    balance_sheet = {
        "total_cash": safe_int(info.get("totalCash")),
        "total_debt": safe_int(info.get("totalDebt")),
        "net_debt": (
            safe_int(info.get("totalDebt", 0) or 0) - safe_int(info.get("totalCash", 0) or 0)
            if info.get("totalDebt") is not None else None
        ),
        "debt_to_equity": safe_float(info.get("debtToEquity")),
        "current_ratio": safe_float(info.get("currentRatio")),
        "quick_ratio": safe_float(info.get("quickRatio")),
        "book_value_per_share": safe_float(info.get("bookValue")),
    }

    # ── Cash Flow ────────────────────────────────────────────────────────────
    cash_flow = {
        "operating_cash_flow": safe_int(info.get("operatingCashflow")),
        "free_cash_flow": safe_int(info.get("freeCashflow")),
        "capex": None,  # derived below if available
    }
    if cash_flow["operating_cash_flow"] and cash_flow["free_cash_flow"]:
        cash_flow["capex"] = cash_flow["operating_cash_flow"] - cash_flow["free_cash_flow"]

    # ── Dividend & Shares ────────────────────────────────────────────────────
    dividend_shares = {
        "dividend_yield": safe_float(info.get("dividendYield")),
        "dividend_rate": safe_float(info.get("dividendRate")),
        "payout_ratio": safe_float(info.get("payoutRatio")),
        "shares_outstanding": safe_int(info.get("sharesOutstanding")),
        "float_shares": safe_int(info.get("floatShares")),
        "shares_short": safe_int(info.get("sharesShort")),
        "short_ratio": safe_float(info.get("shortRatio")),
        "short_percent_of_float": safe_float(info.get("shortPercentOfFloat")),
    }

    # ── Analyst Consensus ────────────────────────────────────────────────────
    analyst = {
        "target_mean_price": safe_float(info.get("targetMeanPrice")),
        "target_high_price": safe_float(info.get("targetHighPrice")),
        "target_low_price": safe_float(info.get("targetLowPrice")),
        "recommendation_key": info.get("recommendationKey"),
        "number_of_analyst_opinions": safe_int(info.get("numberOfAnalystOpinions")),
    }

    # ── Historical Financials (last 4 annual periods) ────────────────────────
    try:
        income_stmt = df_to_dict(stock.financials)
    except Exception:
        income_stmt = {}

    try:
        balance_sheet_hist = df_to_dict(stock.balance_sheet)
    except Exception:
        balance_sheet_hist = {}

    try:
        cashflow_hist = df_to_dict(stock.cashflow)
    except Exception:
        cashflow_hist = {}

    try:
        quarterly_income_stmt = df_to_dict(stock.quarterly_financials, max_cols=3)
    except Exception:
        quarterly_income_stmt = {}

    try:
        quarterly_balance_sheet_hist = df_to_dict(stock.quarterly_balance_sheet, max_cols=3)
    except Exception:
        quarterly_balance_sheet_hist = {}

    try:
        quarterly_cashflow_hist = df_to_dict(stock.quarterly_cashflow, max_cols=3)
    except Exception:
        quarterly_cashflow_hist = {}

    return {
        "ticker": ticker.upper(),
        "key_stats": key_stats,
        "valuation": valuation,
        "profitability": profitability,
        "growth": growth,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "dividend_shares": dividend_shares,
        "analyst_consensus": analyst,
        "historical_income_statement": income_stmt,
        "historical_balance_sheet": balance_sheet_hist,
        "historical_cash_flow": cashflow_hist,
        "quarterly_income_statement": quarterly_income_stmt,
        "quarterly_balance_sheet": quarterly_balance_sheet_hist,
        "quarterly_cash_flow": quarterly_cashflow_hist,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch stock fundamental data")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    args = parser.parse_args()

    result = fetch_financials(args.ticker)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
