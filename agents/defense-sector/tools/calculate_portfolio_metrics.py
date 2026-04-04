#!/usr/bin/env python3
"""
Compute portfolio-level metrics for defense sector portfolio.
Validates constraints, computes weighted beta, FX exposure, domain concentration.

Usage:
    python calculate_portfolio_metrics.py --portfolio portfolio.json --technicals technicals.json
"""

import sys
import json
import argparse
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from defense_universe_config import UNIVERSE, PORTFOLIO_CONSTRAINTS, THEATERS


# Currency mapping by country
COUNTRY_CURRENCY = {
    "US": "USD", "IL": "ILS", "DE": "EUR", "GB": "GBP", "FR": "EUR",
    "IT": "EUR", "SE": "SEK", "NO": "NOK", "KR": "KRW", "JP": "JPY",
    "CA": "CAD",
}


def validate_portfolio(portfolio: list[dict]) -> list[str]:
    """
    Validate portfolio against constraints.
    Each position: {company_key, weight, tranche, domains: [...]}
    Returns list of constraint violations (empty = valid).
    """
    violations = []
    constraints = PORTFOLIO_CONSTRAINTS

    # Position count
    n = len(portfolio)
    if n < constraints["min_positions"]:
        violations.append(f"Too few positions: {n} < {constraints['min_positions']} minimum")
    if n > constraints["max_positions"]:
        violations.append(f"Too many positions: {n} > {constraints['max_positions']} maximum")

    # Single position weight
    for pos in portfolio:
        if pos["weight"] > constraints["max_single_weight"]:
            violations.append(
                f"{pos['company_key']}: weight {pos['weight']:.1%} > "
                f"{constraints['max_single_weight']:.0%} max"
            )

    # Non-US count
    non_us = sum(1 for p in portfolio
                 if UNIVERSE.get(p["company_key"], {}).get("country", "US") != "US")
    if non_us < constraints["min_non_us"]:
        violations.append(f"Non-US positions: {non_us} < {constraints['min_non_us']} minimum")

    # Weight sum
    total_weight = sum(p["weight"] for p in portfolio)
    if abs(total_weight - 1.0) > 0.02:
        violations.append(f"Weights sum to {total_weight:.2%}, should be ~100%")

    # Domain concentration
    domain_weights = {}
    for pos in portfolio:
        for domain in pos.get("domains", []):
            domain_weights[domain] = domain_weights.get(domain, 0) + pos["weight"]
    for domain, weight in domain_weights.items():
        if weight > constraints["max_domain_concentration"]:
            violations.append(
                f"Domain '{domain}': {weight:.1%} > {constraints['max_domain_concentration']:.0%} max"
            )

    return violations


def compute_portfolio_metrics(
    portfolio: list[dict],
    technicals: dict,
) -> dict:
    """
    Compute portfolio-level analytics.

    Args:
        portfolio: [{company_key, weight, tranche, domains}]
        technicals: {yf_ticker: {beta_vs_ita, price, volatility_30d_ann, ...}}
    """
    # Weighted beta
    weighted_beta = 0.0
    beta_coverage = 0.0
    for pos in portfolio:
        yf_ticker = UNIVERSE.get(pos["company_key"], {}).get("yf_ticker", "")
        tech = technicals.get(yf_ticker, {})
        beta = tech.get("beta_vs_ita")
        if beta is not None:
            weighted_beta += pos["weight"] * beta
            beta_coverage += pos["weight"]

    portfolio_beta = round(weighted_beta / beta_coverage, 3) if beta_coverage > 0 else None

    # Weighted volatility
    weighted_vol = 0.0
    vol_coverage = 0.0
    for pos in portfolio:
        yf_ticker = UNIVERSE.get(pos["company_key"], {}).get("yf_ticker", "")
        tech = technicals.get(yf_ticker, {})
        vol = tech.get("volatility_30d_ann")
        if vol is not None:
            weighted_vol += pos["weight"] * vol
            vol_coverage += pos["weight"]

    portfolio_vol = round(weighted_vol / vol_coverage, 2) if vol_coverage > 0 else None

    # FX exposure
    fx_exposure = {}
    for pos in portfolio:
        country = UNIVERSE.get(pos["company_key"], {}).get("country", "US")
        ccy = COUNTRY_CURRENCY.get(country, "USD")
        fx_exposure[ccy] = fx_exposure.get(ccy, 0) + pos["weight"]
    fx_exposure = {k: round(v, 4) for k, v in sorted(fx_exposure.items(), key=lambda x: -x[1])}

    # Geographic exposure
    geo_exposure = {}
    for pos in portfolio:
        country = UNIVERSE.get(pos["company_key"], {}).get("country", "US")
        geo_exposure[country] = geo_exposure.get(country, 0) + pos["weight"]
    geo_exposure = {k: round(v, 4) for k, v in sorted(geo_exposure.items(), key=lambda x: -x[1])}

    # Tranche allocation
    tranche_weights = {}
    for pos in portfolio:
        tr = pos.get("tranche", "unknown")
        tranche_weights[tr] = tranche_weights.get(tr, 0) + pos["weight"]
    tranche_weights = {k: round(v, 4) for k, v in tranche_weights.items()}

    # Domain concentration
    domain_weights = {}
    for pos in portfolio:
        for domain in pos.get("domains", []):
            domain_weights[domain] = domain_weights.get(domain, 0) + pos["weight"]
    domain_weights = {k: round(v, 4) for k, v in sorted(domain_weights.items(), key=lambda x: -x[1])}

    # Tier distribution
    tier_weights = {}
    for pos in portfolio:
        tier = UNIVERSE.get(pos["company_key"], {}).get("tier", "unknown")
        tier_weights[tier] = tier_weights.get(tier, 0) + pos["weight"]
    tier_weights = {k: round(v, 4) for k, v in tier_weights.items()}

    # Theater exposure (weighted by position size and baseline)
    theater_exposure = {t: 0.0 for t in THEATERS}
    for pos in portfolio:
        baseline = UNIVERSE.get(pos["company_key"], {}).get("theater_baseline", {})
        for theater_id in THEATERS:
            theater_exposure[theater_id] += pos["weight"] * baseline.get(theater_id, 0)
    theater_exposure = {k: round(v, 4) for k, v in theater_exposure.items()}

    # Constraint validation
    violations = validate_portfolio(portfolio)

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "positions": len(portfolio),
        "portfolio_beta_vs_ita": portfolio_beta,
        "beta_in_target_range": (
            PORTFOLIO_CONSTRAINTS["target_beta_range"][0] <= portfolio_beta <= PORTFOLIO_CONSTRAINTS["target_beta_range"][1]
            if portfolio_beta else None
        ),
        "portfolio_volatility_ann": portfolio_vol,
        "fx_exposure": fx_exposure,
        "geographic_exposure": geo_exposure,
        "tranche_allocation": tranche_weights,
        "domain_concentration": domain_weights,
        "tier_distribution": tier_weights,
        "theater_exposure": theater_exposure,
        "constraint_violations": violations,
        "portfolio_valid": len(violations) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Compute defense portfolio metrics")
    parser.add_argument("--portfolio", required=True, help="Path to portfolio JSON")
    parser.add_argument("--technicals", required=True, help="Path to technicals JSON")
    args = parser.parse_args()

    with open(args.portfolio) as f:
        portfolio = json.load(f)

    with open(args.technicals) as f:
        tech_data = json.load(f)
    technicals = tech_data.get("companies", tech_data)

    result = compute_portfolio_metrics(portfolio, technicals)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
