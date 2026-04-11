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


def _extract_cf_row(df: pd.DataFrame, *row_names: str) -> dict:
    """Try multiple row name variants; return {date_str: value} for first match found."""
    if df is None or df.empty:
        return {}
    for name in row_names:
        if name in df.index:
            row = df.loc[name]
            return {str(col)[:10]: safe_float(val) for col, val in row.items()}
    return {}


def _build_capital_allocation(stock: yf.Ticker, info: dict, cash_flow: dict) -> dict:
    """Compute capital allocation metrics: FCF yield, dividends, buybacks, total shareholder yield."""
    cf = stock.cashflow          # rows=metric names, cols=dates
    bs = stock.balance_sheet

    market_cap = safe_int(info.get("marketCap"))
    current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
    fcf_ttm = cash_flow.get("free_cash_flow")

    # FCF yield = FCF / market cap (stored as decimal, e.g. 0.0238 = 2.38%)
    fcf_yield = safe_float(fcf_ttm / market_cap) if fcf_ttm and market_cap else None

    # Normalize dividend yield to decimal fraction (yfinance sometimes returns percent)
    raw_div_yield = info.get("dividendYield")
    div_rate = safe_float(info.get("dividendRate"))
    if raw_div_yield is not None and current_price and current_price > 0 and div_rate:
        # Recompute from dividendRate / price for consistency
        div_yield_decimal = safe_float(div_rate / current_price)
    elif raw_div_yield is not None:
        # Normalize: yfinance may return 1.35 (percent) or 0.0135 (decimal)
        raw = float(raw_div_yield)
        div_yield_decimal = safe_float(raw / 100 if raw > 0.5 else raw)
    else:
        div_yield_decimal = None

    # Historical dividends paid (negative in CF statement → make positive)
    dividends_by_year = _extract_cf_row(
        cf,
        "Cash Dividends Paid",
        "Common Stock Dividend Paid",
        "Payment Of Dividends",
        "Dividends Paid",
    )
    dividends_by_year = {k: abs(v) if v is not None else None for k, v in dividends_by_year.items()}

    # Historical buybacks (negative in CF statement → make positive)
    buybacks_by_year = _extract_cf_row(
        cf,
        "Repurchase Of Capital Stock",
        "Common Stock Repurchased",
        "Repurchase Of Common Stock",
        "Purchase Of Common Stock",
    )
    buybacks_by_year = {k: abs(v) if v is not None else None for k, v in buybacks_by_year.items()}

    # FCF by year
    fcf_by_year = _extract_cf_row(cf, "Free Cash Flow")

    # Shares outstanding history from balance sheet
    shares_by_year: dict = {}
    if bs is not None and not bs.empty:
        for name in ("Ordinary Shares Number", "Share Issued", "Common Stock Shares Outstanding"):
            if name in bs.index:
                row = bs.loc[name]
                shares_by_year = {str(col)[:10]: safe_int(val) for col, val in row.items()}
                break

    # Cash returned = dividends + buybacks, by year
    all_years = sorted(
        set(list(dividends_by_year.keys()) + list(buybacks_by_year.keys())),
        reverse=True,
    )
    cash_returned_by_year = {
        y: (dividends_by_year.get(y) or 0) + (buybacks_by_year.get(y) or 0)
        for y in all_years
    }

    # FCF payout ratio (most recent year) = (dividends + buybacks) / FCF
    most_recent_year = all_years[0] if all_years else None
    fcf_payout_ratio: float | None = None
    if most_recent_year:
        total_returned = cash_returned_by_year.get(most_recent_year, 0)
        fcf_val = fcf_by_year.get(most_recent_year)
        if total_returned and fcf_val and fcf_val > 0:
            fcf_payout_ratio = safe_float(total_returned / fcf_val)

    # Buyback yield (most recent year buybacks / market cap)
    buyback_yield: float | None = None
    if most_recent_year and market_cap:
        recent_buybacks = buybacks_by_year.get(most_recent_year)
        if recent_buybacks:
            buyback_yield = safe_float(recent_buybacks / market_cap)

    # Total shareholder yield = dividend yield + buyback yield (all decimal fractions)
    if div_yield_decimal is not None and buyback_yield is not None:
        total_shareholder_yield: float | None = safe_float(div_yield_decimal + buyback_yield)
    else:
        total_shareholder_yield = div_yield_decimal  # at minimum the dividend yield

    # Dividend CAGR from historical dividends paid (annualized over available years)
    div_cagr: float | None = None
    sorted_div_years = sorted(
        [y for y, v in dividends_by_year.items() if v and v > 0]
    )
    if len(sorted_div_years) >= 2:
        oldest = dividends_by_year[sorted_div_years[0]]
        newest = dividends_by_year[sorted_div_years[-1]]
        n = len(sorted_div_years) - 1
        if oldest and newest and oldest > 0:
            div_cagr = safe_float((newest / oldest) ** (1 / n) - 1)

    return {
        "fcf_yield": fcf_yield,
        "dividend_yield_ttm": div_yield_decimal,
        "dividend_rate_annual": div_rate,
        "dividend_5yr_avg_yield": safe_float(info.get("fiveYearAvgDividendYield")),
        "dividend_cagr_4yr": div_cagr,
        "payout_ratio_eps": safe_float(info.get("payoutRatio")),
        "buyback_yield": buyback_yield,
        "total_shareholder_yield": total_shareholder_yield,
        "fcf_payout_ratio": fcf_payout_ratio,
        "dividends_paid_by_year": dividends_by_year,
        "buybacks_by_year": buybacks_by_year,
        "fcf_by_year": fcf_by_year,
        "shares_outstanding_by_year": shares_by_year,
        "cash_returned_by_year": cash_returned_by_year,
    }


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

    # ── Current Price ────────────────────────────────────────────────────────
    current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))

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

    # ── Capital Allocation (computed) ────────────────────────────────────────
    try:
        capital_allocation = _build_capital_allocation(stock, info, cash_flow)
    except Exception:
        capital_allocation = {}

    return {
        "ticker": ticker.upper(),
        "current_price": current_price,
        "key_stats": key_stats,
        "valuation": valuation,
        "profitability": profitability,
        "growth": growth,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
        "dividend_shares": dividend_shares,
        "capital_allocation": capital_allocation,
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
