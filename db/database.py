"""
SQLite persistence layer — stores every analysis run for historical tracking.
"""
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "analyses.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the analyses table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker            TEXT    NOT NULL,
                company_name      TEXT,
                analysis_date     TEXT    NOT NULL,
                recommendation    TEXT,
                confidence        INTEGER,
                price_at_analysis REAL,
                price_target_12m  REAL,
                upside_pct        REAL,
                downside_risk_pct REAL,
                composite_score   INTEGER,
                thesis            TEXT,
                bull_case         TEXT,
                bear_case         TEXT,
                top_risks         TEXT,   -- JSON array
                report_path       TEXT,
                status            TEXT    DEFAULT 'open',
                created_at        TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    logger.info("Database initialised at %s", DB_PATH)


def save_analysis(state: dict) -> int:
    """
    Persist an analysis result to SQLite.
    Returns the new row id.
    """
    init_db()
    rec = state.get("final_recommendation", {})
    top_risks = rec.get("top_3_risks", [])

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (
                ticker, company_name, analysis_date,
                recommendation, confidence,
                price_at_analysis, price_target_12m,
                upside_pct, downside_risk_pct, composite_score,
                thesis, bull_case, bear_case, top_risks,
                report_path
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                state.get("ticker", ""),
                state.get("company_name", ""),
                state.get("analysis_date", datetime.now().strftime("%Y-%m-%d")),
                rec.get("recommendation", ""),
                rec.get("confidence"),
                state.get("current_price"),
                rec.get("price_target_12m"),
                rec.get("upside_pct"),
                rec.get("downside_risk_pct"),
                rec.get("composite_score"),
                rec.get("thesis", ""),
                rec.get("bull_case", ""),
                rec.get("bear_case", ""),
                json.dumps(top_risks) if top_risks else "[]",
                state.get("report_path", ""),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid

    logger.info("Saved analysis for %s (id=%s)", state.get("ticker"), row_id)
    return row_id


def list_analyses(limit: int = 20) -> list[dict]:
    """Return the most recent analyses."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_analysis(ticker: str, limit: int = 5) -> list[dict]:
    """Return past analyses for a specific ticker."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE ticker = ? ORDER BY created_at DESC LIMIT ?",
            (ticker.upper(), limit),
        ).fetchall()
    return [dict(r) for r in rows]
