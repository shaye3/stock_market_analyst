"""
Visualize detect_role_reversal_levels on synthetic and live price data.

Usage:
  .venv/bin/python tests/plot_role_reversal.py              # 4 synthetic scenarios
  .venv/bin/python tests/plot_role_reversal.py --live AAPL  # live ticker
  .venv/bin/python tests/plot_role_reversal.py --out my.png # custom output path
"""
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

sys.path.insert(0, "tools")
from calculate_technicals import detect_role_reversal_levels

# ─── Helpers ─────────────────────────────────────────────────────────────────

SPREAD = 0.005


def S(arr) -> pd.Series:
    return pd.Series(arr, dtype=float)


def make_ohlc(phases, spread=SPREAD):
    segments = [np.linspace(s, e, n) for s, e, n in phases]
    close = np.concatenate(segments)
    high  = close * (1 + spread)
    low   = close * (1 - spread)
    return S(close), S(high), S(low)


# ─── Colour / style constants ────────────────────────────────────────────────

C_CONFIRMED_SUP = "#27ae60"    # confirmed former-resistance-now-support  (green)
C_PENDING_SUP   = "#a9dfbf"    # unconfirmed / pending                    (light green)
C_CONFIRMED_RES = "#c0392b"    # confirmed former-support-now-resistance  (red)
C_PENDING_RES   = "#f1948a"    # unconfirmed / pending                    (light red)
C_PRICE         = "#2c3e50"    # price line
C_HILO          = "#95a5a6"    # H/L band fill
C_CUR           = "#e67e22"    # current-price marker


# ─── Core drawing function ───────────────────────────────────────────────────

def plot_scenario(ax: plt.Axes,
                  close: pd.Series,
                  high:  pd.Series,
                  low:   pd.Series,
                  result: dict,
                  title: str,
                  window: int = 5) -> None:
    """
    Draw price + role-reversal levels on *ax*.

    Visual encoding
    ───────────────
    Confirmed former-resistance-now-support  → solid green  horizontal line
    Pending   former-resistance-now-support  → dashed green horizontal line
    Confirmed former-support-now-resistance  → solid red    horizontal line
    Pending   former-support-now-resistance  → dashed red   horizontal line
    Retest bar detected                      → circle marker on price line
    Current price                            → orange diamond
    """
    n    = len(close)
    bars = np.arange(n)

    # ── price line + H/L band ────────────────────────────────────────────────
    ax.fill_between(bars, low.values, high.values, alpha=0.12,
                    color=C_HILO, label="_nolegend_")
    ax.plot(bars, close.values, color=C_PRICE, lw=1.3, label="Close", zorder=3)

    # ── current price marker ─────────────────────────────────────────────────
    ax.plot(n - 1, float(close.iloc[-1]), "D", color=C_CUR, ms=8, zorder=6,
            label=f"Current  {float(close.iloc[-1]):.1f}")

    # ── draw all role-reversal levels ────────────────────────────────────────
    former_sup = result.get("former_resistance_now_support", [])
    former_res = result.get("former_support_now_resistance", [])

    def _draw_level(price, confirmed, kind):
        """Draw a horizontal line and price label for one level."""
        if kind == "support":
            color = C_CONFIRMED_SUP if confirmed else C_PENDING_SUP
        else:
            color = C_CONFIRMED_RES if confirmed else C_PENDING_RES
        lw = 1.8 if confirmed else 1.0
        ls = "-"  if confirmed else "--"
        ax.axhline(price, color=color, lw=lw, ls=ls, alpha=0.85, zorder=2)
        status = "✓" if confirmed else "?"
        label = ("S" if kind == "support" else "R") + f"→{'R' if kind=='support' else 'S'}"
        ax.text(n - 1, price, f"  {label} {status}  {price:.2f}",
                va="center", fontsize=7.5, color=color, fontweight="bold" if confirmed else "normal")

    for lv in former_sup:
        _draw_level(lv["price"], lv["confirmed"], "support")
        # mark retest bar if it can be located
        broken_ago = lv.get("broken_bars_ago", 0)
        if lv["retest_detected"] and broken_ago is not None:
            retest_bar = n - 1 - broken_ago // 2  # approximate mid-point
            ax.plot(retest_bar, lv["price"], "o", color=C_CONFIRMED_SUP if lv["confirmed"] else C_PENDING_SUP,
                    ms=7, zorder=5, label="_nolegend_")

    for lv in former_res:
        _draw_level(lv["price"], lv["confirmed"], "resistance")
        broken_ago = lv.get("broken_bars_ago", 0)
        if lv["retest_detected"] and broken_ago is not None:
            retest_bar = n - 1 - broken_ago // 2
            ax.plot(retest_bar, lv["price"], "o", color=C_CONFIRMED_RES if lv["confirmed"] else C_PENDING_RES,
                    ms=7, zorder=5, label="_nolegend_")

    # ── legend ───────────────────────────────────────────────────────────────
    legend_elements = [
        Line2D([0],[0], color=C_PRICE,         lw=1.3, label="Close price"),
        Line2D([0],[0], color=C_CONFIRMED_SUP,  lw=1.8, ls="-",  label="Res→Sup (confirmed ✓)"),
        Line2D([0],[0], color=C_PENDING_SUP,    lw=1.0, ls="--", label="Res→Sup (pending ?)"),
        Line2D([0],[0], color=C_CONFIRMED_RES,  lw=1.8, ls="-",  label="Sup→Res (confirmed ✓)"),
        Line2D([0],[0], color=C_PENDING_RES,    lw=1.0, ls="--", label="Sup→Res (pending ?)"),
        Line2D([0],[0], color=C_CUR, marker="D", lw=0, ms=7, label="Current price"),
        Line2D([0],[0], color="gray", marker="o", lw=0, ms=7, label="Retest bar (approx)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=6.5, framealpha=0.75)

    # ── summary badge ────────────────────────────────────────────────────────
    n_conf_sup = sum(1 for lv in former_sup if lv["confirmed"])
    n_conf_res = sum(1 for lv in former_res if lv["confirmed"])
    badge = f"Confirmed: {n_conf_sup} Res→Sup  |  {n_conf_res} Sup→Res"
    ax.text(0.01, 0.97, badge, transform=ax.transAxes, va="top", ha="left",
            fontsize=8, color="white", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#34495e", alpha=0.85))

    ax.set_title(title, fontsize=10, fontweight="bold", pad=5)
    ax.set_ylabel("Price", fontsize=8)
    ax.set_xlabel("Bar", fontsize=8)
    ax.grid(True, alpha=0.2, lw=0.5)


# ─── Detail panel ────────────────────────────────────────────────────────────

def plot_detail_panel(ax: plt.Axes, result: dict, title: str) -> None:
    """Table showing each level's key attributes."""
    all_levels = (
        [("Res→Sup", lv) for lv in result.get("former_resistance_now_support", [])] +
        [("Sup→Res", lv) for lv in result.get("former_support_now_resistance", [])]
    )
    ax.axis("off")
    if not all_levels:
        ax.text(0.5, 0.5, "No role-reversal levels\nwithin proximity",
                transform=ax.transAxes, ha="center", va="center", fontsize=10, color="#7f8c8d")
        ax.set_title(title, fontsize=9)
        return

    rows = [[
        kind,
        f"{lv['price']:.2f}",
        f"{lv['broken_bars_ago']}",
        "Yes" if lv["retest_detected"] else "No",
        "Yes" if lv["retest_held"]     else "No",
        "✓" if lv["confirmed"] else "✗",
    ] for kind, lv in all_levels]

    table = ax.table(
        cellText=rows,
        colLabels=["Type", "Price", "Broke\nago", "Retest\ndetected", "Retest\nheld", "Conf"],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.6)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("white")
        if row == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            kind_val = rows[row - 1][0]
            confirmed_val = rows[row - 1][5]
            if kind_val == "Res→Sup":
                base = C_CONFIRMED_SUP if confirmed_val == "✓" else C_PENDING_SUP
            else:
                base = C_CONFIRMED_RES if confirmed_val == "✓" else C_PENDING_RES
            cell.set_facecolor(base + "33")  # 20% alpha hex
            if col == 5:
                cell.set_text_props(
                    color=C_CONFIRMED_SUP if confirmed_val == "✓" else "#e74c3c",
                    fontweight="bold",
                )

    ax.set_title(title, fontsize=9, fontweight="bold", pad=4)


# ─── Synthetic figure ────────────────────────────────────────────────────────

def build_synthetic_figure() -> plt.Figure:
    """4 scenarios: confirmed, failed retest, single noise, no-retest-in-window."""

    scenarios = []

    # ── S1: Confirmed resistance → support ───────────────────────────────────
    c1, h1, lo1 = make_ohlc([
        (80, 80, 20), (80, 100, 15), (100, 80, 10),
        (80, 110, 12), (110, 101, 8), (101, 108, 8),
    ])
    r1 = detect_role_reversal_levels(c1, h1, lo1, window=5)
    scenarios.append((c1, h1, lo1, r1, "S1: Confirmed Resistance → Support"))

    # ── S2: Failed retest (2 consecutive closes back below) ───────────────────
    c2, h2, lo2 = make_ohlc([
        (80, 80, 20), (80, 100, 15), (100, 80, 10),
        (80, 110, 12), (110, 102, 5), (102, 95, 3), (95, 103, 8),
    ])
    r2 = detect_role_reversal_levels(c2, h2, lo2, window=5)
    scenarios.append((c2, h2, lo2, r2, "S2: Failed Retest (2 Consecutive Closes Back Through)"))

    # ── S3: Single noisy close — retest still holds ───────────────────────────
    c3, h3, lo3 = make_ohlc([
        (80, 80, 20), (80, 100, 15), (100, 80, 10),
        (80, 110, 12), (110, 102, 5), (102, 98, 1), (98, 108, 8),
    ])
    r3 = detect_role_reversal_levels(c3, h3, lo3, window=5)
    scenarios.append((c3, h3, lo3, r3, "S3: Single Noisy Close (Streak Resets → Held)"))

    # ── S4: Confirmed support → resistance ───────────────────────────────────
    c4, h4, lo4 = make_ohlc([
        (120, 120, 20), (120, 100, 15), (100, 120, 10),
        (120, 88, 12), (88, 99.5, 8), (99.5, 92, 8),
    ])
    r4 = detect_role_reversal_levels(c4, h4, lo4, window=5)
    scenarios.append((c4, h4, lo4, r4, "S4: Confirmed Support → Resistance"))

    fig = plt.figure(figsize=(22, 20), facecolor="#f8f9fa")
    fig.suptitle(
        "detect_role_reversal_levels — Synthetic Scenario Visualisation\n"
        "Solid line = confirmed (retested + held)  |  Dashed = pending  |  "
        "○ = approximate retest bar",
        fontsize=13, fontweight="bold", y=0.995,
    )

    gs = GridSpec(4, 2, figure=fig, hspace=0.55, wspace=0.35,
                  left=0.05, right=0.88, top=0.96, bottom=0.03)

    for row, (c, h, lo, result, title) in enumerate(scenarios):
        ax_price  = fig.add_subplot(gs[row, 0])
        ax_detail = fig.add_subplot(gs[row, 1])
        plot_scenario(ax_price, c, h, lo, result, title)
        plot_detail_panel(ax_detail, result, "Level Details")

    return fig


# ─── Live figure ─────────────────────────────────────────────────────────────

def build_live_figure(ticker: str) -> plt.Figure:
    import yfinance as yf
    from calculate_technicals import calculate_technicals

    print(f"  Fetching {ticker} price history…")
    hist   = yf.Ticker(ticker).history(period="1y")
    close  = S(hist["Close"].values)
    high_  = S(hist["High"].values)
    low_   = S(hist["Low"].values)

    rr_result = detect_role_reversal_levels(close, high_, low_)
    full      = calculate_technicals(ticker)
    summary   = full.get("summary", {})

    fig = plt.figure(figsize=(20, 12), facecolor="#f8f9fa")
    fig.suptitle(
        f"{ticker.upper()} — Role-Reversal Support / Resistance (1y)\n"
        f"Technical score: {summary.get('technical_score','—')}  |  "
        f"Signal: {summary.get('overall_signal','—').upper()}  |  "
        f"role_reversal: {summary.get('signal_detail',{}).get('role_reversal','—')}",
        fontsize=13, fontweight="bold", y=0.998,
    )

    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35,
                  height_ratios=[3, 2],
                  left=0.05, right=0.88, top=0.96, bottom=0.04)

    # Price panel (full width)
    ax_price = fig.add_subplot(gs[0, :])
    plot_scenario(ax_price, close, high_, low_, rr_result,
                  f"{ticker.upper()} — Role-Reversal Levels")

    # Detail table
    ax_detail = fig.add_subplot(gs[1, 0])
    plot_detail_panel(ax_detail, rr_result, "Role-Reversal Level Details")

    # Summary table
    ax_sum = fig.add_subplot(gs[1, 1])
    ax_sum.axis("off")

    price_struct = full.get("price_structure", {})
    rows = [
        ["Current price",                f"{float(close.iloc[-1]):.2f}"],
        ["52-week high",                 str(price_struct.get("52w_high", "—"))],
        ["52-week low",                  str(price_struct.get("52w_low",  "—"))],
        ["% from 52w high",              str(price_struct.get("pct_from_52w_high", "—"))],
        ["Nearest Fib level",            str(price_struct.get("nearest_fib_level", "—"))],
        ["Confirmed Res→Sup levels",
         str(sum(1 for lv in rr_result.get("former_resistance_now_support",[]) if lv["confirmed"]))],
        ["Confirmed Sup→Res levels",
         str(sum(1 for lv in rr_result.get("former_support_now_resistance",[]) if lv["confirmed"]))],
        ["role_reversal signal",         summary.get("signal_detail",{}).get("role_reversal", "—")],
        ["Overall signal",               summary.get("overall_signal", "—").upper()],
        ["Technical score",              str(summary.get("technical_score", "—"))],
        ["Trend",                        full.get("trend",{}).get("trend_signal", "—")],
        ["RSI(14)",                      str(full.get("momentum",{}).get("rsi_14", "—"))],
    ]

    rr_sig = summary.get("signal_detail", {}).get("role_reversal", "neutral")
    header_color = C_CONFIRMED_SUP if rr_sig == "bullish" else (
                   C_CONFIRMED_RES if rr_sig == "bearish"  else "#7f8c8d")

    table = ax_sum.table(cellText=rows, colLabels=["Field", "Value"],
                         cellLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#ecf0f1")
        cell.set_edgecolor("white")

    ax_sum.set_title(f"{ticker.upper()} Summary", fontsize=10,
                     fontweight="bold", pad=6)

    return fig


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", metavar="TICKER", help="Plot live ticker")
    parser.add_argument("--out",  default=None,     help="Output PNG path")
    args = parser.parse_args()

    if args.live:
        out = args.out or f"tests/role_reversal_{args.live.upper()}.png"
        print(f"Building live figure for {args.live.upper()}…")
        fig = build_live_figure(args.live.upper())
    else:
        out = args.out or "tests/role_reversal_plot.png"
        print("Building synthetic scenario figure…")
        fig = build_synthetic_figure()

    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved → {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
