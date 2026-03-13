"""
yfinance data fetcher — retrieves all raw stock data needed by the analysis pipeline.
"""
import time
import logging
import numpy as np
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)


def _safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _clean_info(info: dict) -> dict:
    """Remove non-serializable / NaN values from yfinance info dict."""
    cleaned = {}
    for k, v in info.items():
        if isinstance(v, (list, dict)):
            continue
        if isinstance(v, float) and np.isnan(v):
            cleaned[k] = None
        elif isinstance(v, (int, float, str, bool, type(None))):
            cleaned[k] = v
    return cleaned


def _stmt_to_dict(df: pd.DataFrame, max_periods: int = 4) -> dict:
    """Convert a yfinance financial statement DataFrame to a plain dict."""
    if df is None or df.empty:
        return {}
    result = {}
    for col in df.columns[:max_periods]:
        key = str(col.date()) if hasattr(col, "date") else str(col)
        result[key] = {row: _safe_float(val) for row, val in df[col].items()}
    return result


def fetch_stock_data(ticker: str, retries: int = 3) -> dict:
    """
    Fetch comprehensive stock data from yfinance for the given ticker.

    Returns a dict with:
      ticker, company_name, current_price, info, price_history,
      financials (income_stmt, balance_sheet, cash_flow),
      news, analyst_recommendations, errors
    """
    result = {
        "ticker": ticker.upper(),
        "company_name": ticker.upper(),
        "current_price": 0.0,
        "info": {},
        "price_history": [],
        "financials": {
            "income_stmt": {},
            "balance_sheet": {},
            "cash_flow": {},
        },
        "news": [],
        "analyst_recommendations": [],
        "errors": [],
    }

    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)

            # ── Basic Info ──────────────────────────────────────────────────
            try:
                raw_info = stock.info or {}
                info = _clean_info(raw_info)
                result["info"] = info
                result["company_name"] = info.get("longName", ticker.upper())
                result["current_price"] = (
                    _safe_float(info.get("currentPrice"))
                    or _safe_float(info.get("previousClose"))
                    or _safe_float(info.get("regularMarketPrice"))
                    or 0.0
                )
            except Exception as e:
                result["errors"].append(f"info: {e}")

            # ── Price History (2 years) ──────────────────────────────────────
            try:
                hist = stock.history(period="2y", auto_adjust=True)
                if not hist.empty:
                    hist = hist.reset_index()
                    hist["Date"] = pd.to_datetime(hist["Date"]).dt.strftime("%Y-%m-%d")
                    cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
                    result["price_history"] = hist[cols].to_dict(orient="records")
            except Exception as e:
                result["errors"].append(f"price_history: {e}")

            # ── Financial Statements ─────────────────────────────────────────
            try:
                result["financials"]["income_stmt"] = _stmt_to_dict(stock.income_stmt)
            except Exception as e:
                result["errors"].append(f"income_stmt: {e}")

            try:
                result["financials"]["balance_sheet"] = _stmt_to_dict(stock.balance_sheet)
            except Exception as e:
                result["errors"].append(f"balance_sheet: {e}")

            try:
                result["financials"]["cash_flow"] = _stmt_to_dict(stock.cash_flow)
            except Exception as e:
                result["errors"].append(f"cash_flow: {e}")

            # ── News ─────────────────────────────────────────────────────────
            try:
                raw_news = stock.news or []
                result["news"] = [
                    {
                        "title": n.get("content", {}).get("title", n.get("title", "")),
                        "publisher": n.get("content", {}).get("provider", {}).get("displayName", n.get("publisher", "")),
                        "link": n.get("content", {}).get("canonicalUrl", {}).get("url", n.get("link", "")),
                    }
                    for n in raw_news[:15]
                ]
            except Exception as e:
                result["errors"].append(f"news: {e}")

            # ── Analyst Recommendations ──────────────────────────────────────
            try:
                recs = stock.recommendations
                if recs is not None and not recs.empty:
                    recs_reset = recs.tail(20).reset_index()
                    date_col = "Date" if "Date" in recs_reset.columns else ("period" if "period" in recs_reset.columns else None)
                    if date_col:
                        recs_reset["Date"] = pd.to_datetime(recs_reset[date_col], format="mixed", dayfirst=False).dt.strftime("%Y-%m-%d")
                    result["analyst_recommendations"] = recs_reset.to_dict(orient="records")
            except Exception as e:
                result["errors"].append(f"recommendations: {e}")

            break  # success — exit retry loop

        except Exception as e:
            logger.warning(f"Fetch attempt {attempt + 1} failed for {ticker}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                result["errors"].append(f"Fatal fetch error: {e}")

    return result
