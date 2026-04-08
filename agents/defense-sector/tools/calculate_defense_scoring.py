#!/usr/bin/env python3
"""
Compute composite defense scores, apply TWES (Theater-Weighted Exposure Score)
multipliers, enforce hard gates, and produce ranked output.

Input: JSON files from batch scoring agents (dimension scores per company)
       + financials JSON for hard gate checks.
Output: JSON with ranked companies, hard gate exclusions, and composite scores.

Usage:
    python calculate_defense_scoring.py --scores scores.json --financials financials.json
    python calculate_defense_scoring.py --scores-dir /tmp/defense_scores/ --financials financials.json
"""

import sys
import json
import argparse
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from defense_universe_config import (
    UNIVERSE, DIMENSION_WEIGHTS, HARD_GATES, THEATERS, PORTFOLIO_CONSTRAINTS, SVM_CONFIG
)


def compute_twes(company_key: str, theater_weights: dict) -> float:
    """
    Compute Theater-Weighted Exposure Score.
    TWES = sum(theater_weight_i * company_baseline_i) for each theater.
    Result is a multiplier centered around 1.0.
    """
    company = UNIVERSE.get(company_key)
    if not company:
        return 1.0

    baseline = company.get("theater_baseline", {})
    score = 0.0
    total_theater_weight = sum(theater_weights.values())

    if total_theater_weight == 0:
        return 1.0

    for theater_id, theater_weight in theater_weights.items():
        exposure = baseline.get(theater_id, 0.0)
        score += theater_weight * exposure

    # Normalize by actual weight sum so the multiplier is stable regardless of
    # whether theater weights sum to exactly 1.0.
    # Max normalized score = 1.0 → multiplier = 1.3; min = 0.0 → multiplier = 0.7.
    normalized_score = score / total_theater_weight
    multiplier = 0.7 + (normalized_score * 0.6)
    return round(min(max(multiplier, 0.7), 1.3), 4)


def compute_composite_score(dimension_scores: dict) -> float:
    """
    Compute weighted composite score from dimension scores (each 0-10).
    Returns: composite score 0-10.
    """
    total = 0.0
    weight_sum = 0.0

    for dim, weight in DIMENSION_WEIGHTS.items():
        score = dimension_scores.get(dim)
        if score is not None:
            total += weight * score
            weight_sum += weight

    if weight_sum == 0:
        return 0.0

    # Normalize by actual weights used (in case some dimensions missing)
    return round(total / weight_sum * 10 / 10, 2)


def check_hard_gates(company_financials: dict) -> list[str]:
    """
    Check hard gate exclusion rules. Returns list of gate violations.
    Empty list = passes all gates.
    """
    violations = []
    val = company_financials.get("valuation", {})
    cf = company_financials.get("cash_flow", {})
    pc = company_financials.get("price_context", {})

    # Gate 1: P/E > 40x without backlog acceleration
    pe = val.get("trailing_pe")
    if pe and pe > HARD_GATES["pe_max_without_backlog_accel"]["pe_threshold"]:
        # Without backlog data from API, flag for agent review
        violations.append(
            f"P/E={pe:.1f}x exceeds 40x threshold — requires >20% YoY backlog acceleration to pass"
        )

    # Gate 2: EV/EBITDA > 25x AND FCF yield < 2%
    ev_ebitda = val.get("ev_to_ebitda")
    fcf_yield = cf.get("fcf_yield")
    if ev_ebitda and fcf_yield is not None:
        if (ev_ebitda > HARD_GATES["ev_ebitda_fcf_gate"]["ev_ebitda_threshold"]
                and fcf_yield < HARD_GATES["ev_ebitda_fcf_gate"]["fcf_yield_threshold"]):
            violations.append(
                f"EV/EBITDA={ev_ebitda:.1f}x AND FCF yield={fcf_yield:.2%} — dual gate fail"
            )

    # Gate 3: Price > 30% above 52-week average
    pct_above = pc.get("pct_above_52w_avg")
    if pct_above and pct_above > HARD_GATES["price_above_52w_avg"]["premium_threshold"]:
        violations.append(
            f"Price {pct_above:.1%} above 52W avg — requires new contract catalyst to pass"
        )

    return violations


def compute_svm(company_key: str, sentiment_data: dict | None) -> float:
    """
    Compute Sentiment Visibility Multiplier from pre-computed sentiment scores.
    Returns multiplier in range [0.85, 1.15]. Default 1.0 when no data present.

    sentiment_data format: {company_key: {"svm_raw_score": float, ...}}
    """
    if not sentiment_data:
        return 1.0
    entry = sentiment_data.get(company_key)
    if not entry:
        return 1.0
    raw = entry.get("svm_raw_score")
    if raw is None:
        return 1.0
    for min_score, max_score, multiplier in SVM_CONFIG["score_to_multiplier"]:
        if min_score <= raw <= max_score:
            return multiplier
    # Clamp: if raw > 10.0 use highest tier, if raw < 0 use lowest tier
    return 1.15 if raw > 10.0 else 0.85


def merge_batch_scores(scores_input: dict | list) -> dict:
    """
    Merge scoring data from multiple batch files or a single file.
    Expected format per company: {dimension_scores: {...}, notes: str}
    """
    if isinstance(scores_input, list):
        merged = {}
        for batch in scores_input:
            if isinstance(batch, dict):
                merged.update(batch)
        return merged
    return scores_input


def compute_rankings(
    dimension_scores: dict,
    financials: dict,
    theater_weights: dict | None = None,
    sentiment_data: dict | None = None,
) -> dict:
    """
    Main ranking computation.

    Args:
        dimension_scores: {company_key: {dimension: score_0_to_10, ...}}
        financials: {yf_ticker: {valuation: {...}, cash_flow: {...}, ...}}
        theater_weights: {theater_id: weight} (from theater intelligence agent)
        sentiment_data: {company_key: {svm_raw_score: float, ...}} (optional)
            When provided, applies SVM to final scores: final = composite * TWES * SVM.
            When None, SVM defaults to 1.0 for all companies (no effect).

    Returns: Full ranking output with scores, gates, and rankings.
    """
    if theater_weights is None:
        # Default equal weights
        theater_weights = {t: 0.2 for t in THEATERS}

    results = []
    excluded = []

    for company_key, scores in dimension_scores.items():
        company_info = UNIVERSE.get(company_key, {})
        yf_ticker = company_info.get("yf_ticker", company_key)

        # Find financials by yf_ticker
        fin = financials.get(yf_ticker, {})

        # Check hard gates
        gate_violations = check_hard_gates(fin)

        # Compute base composite
        composite = compute_composite_score(scores)

        # Compute TWES multiplier
        twes = compute_twes(company_key, theater_weights)

        # Compute SVM (1.0 when no sentiment data — no effect)
        svm = compute_svm(company_key, sentiment_data)

        # Final score = composite * TWES * SVM
        final_score = round(composite * twes * svm, 2)

        entry = {
            "company_key": company_key,
            "yf_ticker": yf_ticker,
            "name": company_info.get("name", company_key),
            "country": company_info.get("country", ""),
            "batch": company_info.get("batch", ""),
            "tier": company_info.get("tier", ""),
            "dimension_scores": scores,
            "composite_score": composite,
            "twes_multiplier": twes,
            "svm_multiplier": svm,
            "final_score": final_score,
            "hard_gate_violations": gate_violations,
            "excluded": len(gate_violations) > 0,
        }

        if gate_violations:
            excluded.append(entry)
        else:
            results.append(entry)

    # Sort by final score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)
    excluded.sort(key=lambda x: x["final_score"], reverse=True)

    # Add rank
    for i, entry in enumerate(results):
        entry["rank"] = i + 1

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "theater_weights_used": theater_weights,
        "sentiment_applied": sentiment_data is not None,
        "total_scored": len(results) + len(excluded),
        "passing": len(results),
        "excluded": len(excluded),
        "rankings": results,
        "hard_gate_exclusions": excluded,
        "top_10": [
            {"rank": e["rank"], "ticker": e["yf_ticker"], "name": e["name"],
             "score": e["final_score"], "twes": e["twes_multiplier"],
             "svm": e["svm_multiplier"]}
            for e in results[:10]
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Compute defense sector rankings")
    parser.add_argument("--scores", help="Path to JSON file with dimension scores")
    parser.add_argument("--scores-dir", help="Directory containing batch score JSON files")
    parser.add_argument("--financials", required=True, help="Path to financials JSON")
    parser.add_argument("--theater-weights", help="Path to theater weights JSON")
    parser.add_argument("--sentiment", help="Path to sentiment JSON from analyze-defense-sentiment (optional)")
    args = parser.parse_args()

    # Load financials
    with open(args.financials) as f:
        fin_data = json.load(f)
    financials = fin_data.get("companies", fin_data)

    # Load dimension scores
    if args.scores:
        with open(args.scores) as f:
            scores = json.load(f)
    elif args.scores_dir:
        batch_scores = []
        for fname in sorted(os.listdir(args.scores_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(args.scores_dir, fname)) as f:
                    batch_scores.append(json.load(f))
        scores = merge_batch_scores(batch_scores)
    else:
        print("Error: provide --scores or --scores-dir", file=sys.stderr)
        sys.exit(1)

    # Load theater weights
    theater_weights = None
    if args.theater_weights:
        with open(args.theater_weights) as f:
            theater_weights = json.load(f)

    # Load sentiment data (optional)
    sentiment_data = None
    if args.sentiment:
        with open(args.sentiment) as f:
            sd = json.load(f)
        # Support both {company_key: {...}} and {"companies": {company_key: {...}}}
        sentiment_data = sd.get("companies", sd)

    result = compute_rankings(scores, financials, theater_weights, sentiment_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
