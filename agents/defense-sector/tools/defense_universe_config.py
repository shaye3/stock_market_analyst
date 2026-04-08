#!/usr/bin/env python3
"""
Defense Sector Universe Configuration.
Central config: tickers, batches, scoring weights, theater weights,
hard gate thresholds, TWES multiplier table, and static theater baselines.

Usage: python defense_universe_config.py [--batch A|B|C|D|E|F] [--json]
"""

import json
import argparse

# ── Scoring Dimension Weights (sum = 1.0 excluding TWES multiplier) ─────────
DIMENSION_WEIGHTS = {
    "replenishment_exposure": 0.05,
    "domain_breadth": 0.15,
    "moat_sole_source": 0.18,
    "production_scalability": 0.14,
    "backlog_quality": 0.08,
    "time_to_revenue": 0.03,
    "valuation_discipline": 0.15,
    "allied_export": 0.10,
    "fundamentals": 0.12,
}

# ── Hard Gate Thresholds ────────────────────────────────────────────────────
HARD_GATES = {
    "pe_max_without_backlog_accel": {
        "pe_threshold": 40.0,
        "backlog_yoy_threshold": 0.20,
        "description": "P/E > 40x without >20% YoY backlog acceleration → exclude",
    },
    "ev_ebitda_fcf_gate": {
        "ev_ebitda_threshold": 25.0,
        "fcf_yield_threshold": 0.02,
        "description": "EV/EBITDA > 25x AND FCF yield < 2% → exclude",
    },
    "price_above_52w_avg": {
        "premium_threshold": 0.30,
        "description": "Price > 30% above 52-week average without new contract catalyst → exclude",
    },
}

# ── Theater Definitions ─────────────────────────────────────────────────────
THEATERS = {
    "ME": {"name": "Middle East", "description": "US-Israel-Iran conflict axis"},
    "EE": {"name": "Eastern Europe", "description": "Ukraine/Russia prolonged war + NATO expansion"},
    "IP": {"name": "Indo-Pacific", "description": "Taiwan Strait, South China Sea deterrence"},
    "KP": {"name": "Korean Peninsula", "description": "DPRK provocations, ROK modernization"},
    "Sahel": {"name": "Sahel/Africa", "description": "CT operations, French withdrawal aftermath"},
}

# ── Warfare Domain Definitions ──────────────────────────────────────────────
WARFARE_DOMAINS = [
    "Precision Munitions & Guided Weapons",
    "Air & Missile Defense",
    "ISR & C4ISR",
    "Electronic Warfare & Spectrum Dominance",
    "Naval & Maritime",
    "Cyber, AI & Autonomous Systems",
    "Space & Satellite Systems",
    "Rotary & Fixed Wing Platforms",
    "Ground Vehicles & Land Systems",
    "Sustainment & Defense Services",
]

# ── Sentiment Visibility Multiplier Configuration ────────────────────────────
SVM_CONFIG = {
    "enabled": True,
    "svm_range": (0.85, 1.15),
    "signal_weights": {
        "analyst_sentiment": 0.40,
        "institutional_signal": 0.35,
        "news_visibility": 0.25,
    },
    "score_to_multiplier": [
        # (min_score, max_score, multiplier)
        (8.5, 10.0, 1.15),
        (7.0, 8.49, 1.08),
        (5.5, 6.99, 1.02),
        (4.5, 5.49, 1.00),
        (3.0, 4.49, 0.95),
        (1.5, 2.99, 0.90),
        (0.0, 1.49, 0.85),
    ],
    "cache_validity_days": 7,
}

# ── MSCI World A&D Benchmark Proxy ──────────────────────────────────────────
BENCHMARK_PROXY = {
    "ITA": 0.50,
    "BA.L": 0.25,
    "RHM.DE": 0.15,
    "SAF.PA": 0.10,
}

# ── Portfolio Constraints ───────────────────────────────────────────────────
PORTFOLIO_CONSTRAINTS = {
    "min_positions": 12,
    "max_positions": 15,
    "max_single_weight": 0.15,
    "min_non_us": 3,
    "max_domain_concentration": 0.40,
    "target_beta_range": (0.8, 1.2),
    "tranches": {
        "near": {"horizon": "0-6 months", "label": "Near-Term"},
        "medium": {"horizon": "6-18 months", "label": "Medium-Term"},
        "long": {"horizon": "18-36 months", "label": "Long-Term"},
    },
}

# ── Company Universe ────────────────────────────────────────────────────────
# Each entry: ticker, yfinance_ticker, name, country, batch, market_cap_tier
# Theater baselines: {ME, EE, IP, KP, Sahel} scored 0.0-1.0

UNIVERSE = {
    # ── Batch A: US Large-Cap ───────────────────────────────────────────────
    "LMT": {
        "yf_ticker": "LMT", "name": "Lockheed Martin", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.8, "EE": 0.7, "IP": 0.7, "KP": 0.4, "Sahel": 0.1},
    },
    "RTX": {
        "yf_ticker": "RTX", "name": "RTX Corporation", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.9, "EE": 0.8, "IP": 0.6, "KP": 0.5, "Sahel": 0.15},
    },
    "NOC": {
        "yf_ticker": "NOC", "name": "Northrop Grumman", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.5, "EE": 0.6, "IP": 0.8, "KP": 0.5, "Sahel": 0.1},
    },
    "GD": {
        "yf_ticker": "GD", "name": "General Dynamics", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.6, "EE": 0.7, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "LHX": {
        "yf_ticker": "LHX", "name": "L3Harris Technologies", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.7, "EE": 0.7, "IP": 0.6, "KP": 0.4, "Sahel": 0.2},
    },
    "BA": {
        "yf_ticker": "BA", "name": "Boeing", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.6, "EE": 0.5, "IP": 0.7, "KP": 0.5, "Sahel": 0.05},
    },
    "HII": {
        "yf_ticker": "HII", "name": "Huntington Ingalls Industries", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.8, "KP": 0.4, "Sahel": 0.0},
    },
    "GE": {
        "yf_ticker": "GE", "name": "GE Aerospace", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.5, "EE": 0.5, "IP": 0.6, "KP": 0.4, "Sahel": 0.1},
    },
    "TXT": {
        "yf_ticker": "TXT", "name": "Textron", "country": "US",
        "batch": "A", "tier": "large",
        "theater_baseline": {"ME": 0.4, "EE": 0.5, "IP": 0.4, "KP": 0.3, "Sahel": 0.15},
    },

    # ── Batch B: US Mid-Cap ─────────────────────────────────────────────────
    "PLTR": {
        "yf_ticker": "PLTR", "name": "Palantir Technologies", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.7, "EE": 0.7, "IP": 0.6, "KP": 0.5, "Sahel": 0.3},
    },
    "LDOS": {
        "yf_ticker": "LDOS", "name": "Leidos Holdings", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.6, "EE": 0.5, "IP": 0.5, "KP": 0.3, "Sahel": 0.2},
    },
    "BAH": {
        "yf_ticker": "BAH", "name": "Booz Allen Hamilton", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.5, "EE": 0.5, "IP": 0.5, "KP": 0.3, "Sahel": 0.2},
    },
    "CACI": {
        "yf_ticker": "CACI", "name": "CACI International", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.5, "EE": 0.5, "IP": 0.5, "KP": 0.3, "Sahel": 0.2},
    },
    "KTOS": {
        "yf_ticker": "KTOS", "name": "Kratos Defense", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.6, "EE": 0.5, "IP": 0.7, "KP": 0.4, "Sahel": 0.1},
    },
    "AVAV": {
        "yf_ticker": "AVAV", "name": "AeroVironment", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.6, "EE": 0.8, "IP": 0.5, "KP": 0.4, "Sahel": 0.2},
    },
    "TDG": {
        "yf_ticker": "TDG", "name": "TransDigm Group", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.4, "EE": 0.4, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "BWXT": {
        "yf_ticker": "BWXT", "name": "BWX Technologies", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.2, "EE": 0.3, "IP": 0.7, "KP": 0.5, "Sahel": 0.0},
    },
    "CW": {
        "yf_ticker": "CW", "name": "Curtiss-Wright", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.6, "KP": 0.4, "Sahel": 0.05},
    },
    "DRS": {
        "yf_ticker": "DRS", "name": "Leonardo DRS", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.5, "EE": 0.6, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "HWM": {
        "yf_ticker": "HWM", "name": "Howmet Aerospace", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "HEI": {
        "yf_ticker": "HEI", "name": "HEICO Corporation", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.4, "KP": 0.3, "Sahel": 0.1},
    },
    "PSN": {
        "yf_ticker": "PSN", "name": "Parsons Corporation", "country": "US",
        "batch": "B", "tier": "mid",
        "theater_baseline": {"ME": 0.5, "EE": 0.5, "IP": 0.5, "KP": 0.3, "Sahel": 0.15},
    },

    # ── Batch C: US Small-Cap ───────────────────────────────────────────────
    "MRCY": {
        "yf_ticker": "MRCY", "name": "Mercury Systems", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.5, "EE": 0.4, "IP": 0.6, "KP": 0.3, "Sahel": 0.1},
    },
    "MOG.A": {
        "yf_ticker": "MOG-A", "name": "Moog Inc", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.4, "EE": 0.5, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "TDY": {
        "yf_ticker": "TDY", "name": "Teledyne Technologies", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.4, "EE": 0.4, "IP": 0.5, "KP": 0.3, "Sahel": 0.1},
    },
    "RKLB": {
        "yf_ticker": "RKLB", "name": "Rocket Lab", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.2, "EE": 0.3, "IP": 0.6, "KP": 0.4, "Sahel": 0.05},
    },
    "KRMN": {
        "yf_ticker": "KRMN", "name": "Karman Holdings", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.3, "EE": 0.3, "IP": 0.5, "KP": 0.3, "Sahel": 0.05},
    },
    "NPK": {
        "yf_ticker": "NPK", "name": "National Presto Industries", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.5, "EE": 0.6, "IP": 0.2, "KP": 0.2, "Sahel": 0.1},
    },
    "VVX": {
        "yf_ticker": "VVX", "name": "V2X Inc", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.7, "EE": 0.5, "IP": 0.4, "KP": 0.3, "Sahel": 0.3},
    },
    "RCAT": {
        "yf_ticker": "RCAT", "name": "Red Cat Holdings", "country": "US",
        "batch": "C", "tier": "small",
        "theater_baseline": {"ME": 0.4, "EE": 0.7, "IP": 0.4, "KP": 0.3, "Sahel": 0.1},
    },

    # ── Batch D: Israel ─────────────────────────────────────────────────────
    "ESLT": {
        "yf_ticker": "ESLT", "name": "Elbit Systems", "country": "IL",
        "batch": "D", "tier": "mid",
        "theater_baseline": {"ME": 0.95, "EE": 0.7, "IP": 0.5, "KP": 0.3, "Sahel": 0.3},
    },
    "SMSH": {
        "yf_ticker": "SMSH.TA", "name": "Smart Shooter", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.8, "EE": 0.5, "IP": 0.3, "KP": 0.2, "Sahel": 0.2},
    },
    "ARYT": {
        "yf_ticker": "ARYT.TA", "name": "Aryt Industries", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.7, "EE": 0.3, "IP": 0.2, "KP": 0.1, "Sahel": 0.1},
    },
    "ORBI": {
        "yf_ticker": "ORBI.TA", "name": "Orbit Technologies", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.6, "EE": 0.4, "IP": 0.4, "KP": 0.2, "Sahel": 0.1},
    },
    "ISI": {
        "yf_ticker": "ISI.TA", "name": "Imagesat International", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.5, "EE": 0.5, "IP": 0.6, "KP": 0.3, "Sahel": 0.2},
    },
    "AXN": {
        "yf_ticker": "AXN.TA", "name": "Axon Vision", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.6, "EE": 0.3, "IP": 0.3, "KP": 0.2, "Sahel": 0.1},
    },
    "ISHI": {
        "yf_ticker": "ISHI.TA", "name": "Israel Shipyards Industries", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.6, "EE": 0.2, "IP": 0.2, "KP": 0.1, "Sahel": 0.05},
    },
    "ASHO": {
        "yf_ticker": "ASHO.TA", "name": "Ashot Ashkelon", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.7, "EE": 0.3, "IP": 0.3, "KP": 0.1, "Sahel": 0.05},
    },
    "BSEN": {
        "yf_ticker": "BSEN.TA", "name": "Beth Shemesh Engines", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.7, "EE": 0.3, "IP": 0.3, "KP": 0.2, "Sahel": 0.05},
    },
    "FBRT": {
        "yf_ticker": "FBRT.TA", "name": "FMS Enterprises Migun", "country": "IL",
        "batch": "D", "tier": "small",
        "theater_baseline": {"ME": 0.5, "EE": 0.3, "IP": 0.3, "KP": 0.2, "Sahel": 0.1},
    },

    # ── Batch E: Europe ─────────────────────────────────────────────────────
    "RHM": {
        "yf_ticker": "RHM.DE", "name": "Rheinmetall", "country": "DE",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.3, "EE": 0.95, "IP": 0.3, "KP": 0.1, "Sahel": 0.2},
    },
    "HAG": {
        "yf_ticker": "HAG.DE", "name": "Hensoldt", "country": "DE",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.8, "IP": 0.3, "KP": 0.1, "Sahel": 0.15},
    },
    "MTX": {
        "yf_ticker": "MTX.DE", "name": "MTU Aero Engines", "country": "DE",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.2, "EE": 0.5, "IP": 0.4, "KP": 0.2, "Sahel": 0.1},
    },
    "BA.L": {
        "yf_ticker": "BA.L", "name": "BAE Systems", "country": "GB",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.7, "EE": 0.8, "IP": 0.6, "KP": 0.3, "Sahel": 0.2},
    },
    "RR.L": {
        "yf_ticker": "RR.L", "name": "Rolls-Royce Holdings", "country": "GB",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.3, "EE": 0.5, "IP": 0.6, "KP": 0.3, "Sahel": 0.1},
    },
    "BAB.L": {
        "yf_ticker": "BAB.L", "name": "Babcock International", "country": "GB",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.5, "IP": 0.4, "KP": 0.2, "Sahel": 0.15},
    },
    "QQ.L": {
        "yf_ticker": "QQ.L", "name": "QinetiQ Group", "country": "GB",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.5, "IP": 0.4, "KP": 0.2, "Sahel": 0.1},
    },
    "CHG.L": {
        "yf_ticker": "CHG.L", "name": "Chemring Group", "country": "GB",
        "batch": "E", "tier": "small",
        "theater_baseline": {"ME": 0.5, "EE": 0.7, "IP": 0.3, "KP": 0.2, "Sahel": 0.2},
    },
    "AIR.PA": {
        "yf_ticker": "AIR.PA", "name": "Airbus", "country": "FR",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.3, "EE": 0.6, "IP": 0.5, "KP": 0.2, "Sahel": 0.2},
    },
    "SAF.PA": {
        "yf_ticker": "SAF.PA", "name": "Safran", "country": "FR",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.3, "EE": 0.5, "IP": 0.4, "KP": 0.2, "Sahel": 0.15},
    },
    "AM.PA": {
        "yf_ticker": "AM.PA", "name": "Dassault Aviation", "country": "FR",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.4, "EE": 0.5, "IP": 0.5, "KP": 0.2, "Sahel": 0.3},
    },
    "HO.PA": {
        "yf_ticker": "HO.PA", "name": "Thales", "country": "FR",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.5, "EE": 0.7, "IP": 0.5, "KP": 0.2, "Sahel": 0.25},
    },
    "LDO.MI": {
        "yf_ticker": "LDO.MI", "name": "Leonardo SpA", "country": "IT",
        "batch": "E", "tier": "large",
        "theater_baseline": {"ME": 0.5, "EE": 0.6, "IP": 0.4, "KP": 0.2, "Sahel": 0.2},
    },
    "SAAB-B": {
        "yf_ticker": "SAAB-B.ST", "name": "Saab AB", "country": "SE",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.2, "EE": 0.8, "IP": 0.4, "KP": 0.2, "Sahel": 0.1},
    },
    "KOG": {
        "yf_ticker": "KOG.OL", "name": "Kongsberg Gruppen", "country": "NO",
        "batch": "E", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.7, "IP": 0.5, "KP": 0.2, "Sahel": 0.1},
    },

    # ── Batch F: Asia-Pacific ───────────────────────────────────────────────
    "HANWHA_AD": {
        "yf_ticker": "012450.KS", "name": "Hanwha Aerospace", "country": "KR",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.5, "IP": 0.4, "KP": 0.9, "Sahel": 0.05},
    },
    "HANWHA_OC": {
        "yf_ticker": "047810.KS", "name": "Hanwha Ocean", "country": "KR",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.2, "EE": 0.3, "IP": 0.5, "KP": 0.8, "Sahel": 0.0},
    },
    "HYUNDAI_ROT": {
        "yf_ticker": "064350.KS", "name": "Hyundai Rotem", "country": "KR",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.2, "EE": 0.6, "IP": 0.3, "KP": 0.85, "Sahel": 0.05},
    },
    "LIG_NEX1": {
        "yf_ticker": "272210.KS", "name": "LIG Nex1", "country": "KR",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.4, "KP": 0.85, "Sahel": 0.05},
    },
    "KOREAN_AIR": {
        "yf_ticker": "079550.KS", "name": "Korean Air (Defense)", "country": "KR",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.1, "EE": 0.2, "IP": 0.3, "KP": 0.7, "Sahel": 0.0},
    },
    "MHI": {
        "yf_ticker": "7011.T", "name": "Mitsubishi Heavy Industries", "country": "JP",
        "batch": "F", "tier": "large",
        "theater_baseline": {"ME": 0.1, "EE": 0.2, "IP": 0.8, "KP": 0.5, "Sahel": 0.0},
    },
    "KHI": {
        "yf_ticker": "7012.T", "name": "Kawasaki Heavy Industries", "country": "JP",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.1, "EE": 0.2, "IP": 0.7, "KP": 0.4, "Sahel": 0.0},
    },
    "IHI": {
        "yf_ticker": "7013.T", "name": "IHI Corporation", "country": "JP",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.1, "EE": 0.2, "IP": 0.6, "KP": 0.3, "Sahel": 0.0},
    },
    "CAE": {
        "yf_ticker": "CAE.TO", "name": "CAE Inc", "country": "CA",
        "batch": "F", "tier": "mid",
        "theater_baseline": {"ME": 0.3, "EE": 0.4, "IP": 0.4, "KP": 0.3, "Sahel": 0.1},
    },
}


def get_batch(batch_id: str) -> dict:
    """Return companies in a specific batch."""
    return {k: v for k, v in UNIVERSE.items() if v["batch"] == batch_id}


def get_tickers(batch_id: str | None = None) -> list[str]:
    """Return yfinance ticker symbols, optionally filtered by batch."""
    companies = get_batch(batch_id) if batch_id else UNIVERSE
    return [v["yf_ticker"] for v in companies.values()]


def get_all_config() -> dict:
    """Return the full configuration as a dict."""
    return {
        "dimension_weights": DIMENSION_WEIGHTS,
        "hard_gates": HARD_GATES,
        "theaters": THEATERS,
        "warfare_domains": WARFARE_DOMAINS,
        "benchmark_proxy": BENCHMARK_PROXY,
        "portfolio_constraints": PORTFOLIO_CONSTRAINTS,
        "svm_config": SVM_CONFIG,
        "universe": UNIVERSE,
        "universe_size": len(UNIVERSE),
        "batches": {
            "A": {"label": "US Large-Cap", "count": len(get_batch("A"))},
            "B": {"label": "US Mid-Cap", "count": len(get_batch("B"))},
            "C": {"label": "US Small-Cap", "count": len(get_batch("C"))},
            "D": {"label": "Israel", "count": len(get_batch("D"))},
            "E": {"label": "Europe", "count": len(get_batch("E"))},
            "F": {"label": "Asia-Pacific", "count": len(get_batch("F"))},
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Defense universe configuration")
    parser.add_argument("--batch", choices=["A", "B", "C", "D", "E", "F"],
                        help="Filter by batch")
    parser.add_argument("--json", action="store_true", help="Output full config as JSON")
    parser.add_argument("--tickers", action="store_true", help="Output ticker list only")
    args = parser.parse_args()

    if args.tickers:
        tickers = get_tickers(args.batch)
        print(json.dumps(tickers, indent=2))
    elif args.json:
        print(json.dumps(get_all_config(), indent=2))
    else:
        config = get_all_config()
        print(f"Defense Universe: {config['universe_size']} companies")
        for batch_id, info in config["batches"].items():
            print(f"  Batch {batch_id}: {info['label']} ({info['count']} companies)")
        if args.batch:
            batch = get_batch(args.batch)
            print(f"\nBatch {args.batch} tickers:")
            for key, co in batch.items():
                print(f"  {co['yf_ticker']:15s} {co['name']}")


if __name__ == "__main__":
    main()
