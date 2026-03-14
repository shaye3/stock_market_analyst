"""
Visualize detect_fibonacci_signals output on synthetic and live price data.

Usage:
  .venv/bin/python tests/plot_fibonacci_signals.py           # synthetic cases
  .venv/bin/python tests/plot_fibonacci_signals.py --live AAPL   # live ticker
"""
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                      # headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

sys.path.insert(0, "tools")
from calculate_technicals import detect_fibonacci_signals

# ─── Helpers ─────────────────────────────────────────────────────────────────

def S(arr) -> pd.Series:
    return pd.Series(arr, dtype=float)

SPREAD = 0.005

def make_ohlcv(phases, spread=SPREAD):
    segments, joints = [], []
    bar = 0
    for i, (start, end, nbars) in enumerate(phases):
        segments.append(np.linspace(start, end, nbars))
        bar += nbars
        if i < len(phases) - 1:
            joints.append(bar - 1)
    close = np.concatenate(segments)
    high  = close * (1 + spread)
    low   = close * (1 - spread)
    for j in joints:
        if j > 0 and close[j] > close[j - 1]:
            high[j] = close[j] * (1 + spread * 3)
        else:
            low[j]  = close[j] * (1 - spread * 3)
    return close, high, low, np.full(len(close), 1_000_000.0)


# ─── Plotting core ───────────────────────────────────────────────────────────

FIB_COLORS = {
    "fib_0":    "#2ecc71",   # bright green  — start of move
    "fib_236":  "#a8e6cf",   # light green
    "fib_382":  "#fddb92",   # pale yellow
    "fib_500":  "#ffa07a",   # light salmon
    "fib_618":  "#e74c3c",   # red          — golden ratio (most important)
    "fib_786":  "#c0392b",   # dark red
    "fib_100":  "#922b21",   # deep red     — end of move
    "fib_1272": "#8e44ad",   # purple       — extension
    "fib_1618": "#6c3483",   # deep purple  — extension
}

FIB_LABELS = {
    "fib_0":    "0.0%",
    "fib_236":  "23.6%",
    "fib_382":  "38.2%",
    "fib_500":  "50.0%",
    "fib_618":  "61.8% ★",
    "fib_786":  "78.6%",
    "fib_100":  "100%",
    "fib_1272": "127.2% ext",
    "fib_1618": "161.8% ext",
}


def plot_fib_panel(ax: plt.Axes, close: np.ndarray, high: np.ndarray,
                   low: np.ndarray, volume: np.ndarray,
                   result: dict, title: str) -> None:
    """Draw price + Fibonacci levels + signal annotations on *ax*."""
    n = len(close)
    bars = np.arange(n)

    # ── price line ───────────────────────────────────────────────────────────
    ax.plot(bars, close, color="#2c3e50", lw=1.4, label="Close", zorder=3)
    ax.fill_between(bars, low, high, alpha=0.15, color="#95a5a6", label="H/L band")

    if "error" in result:
        ax.text(0.5, 0.5, f"⚠ {result['error']}", transform=ax.transAxes,
                ha="center", va="center", fontsize=12, color="red")
        ax.set_title(title, fontsize=11, fontweight="bold")
        return

    ret  = result.get("retracement_levels", {})
    ext  = result.get("extension_levels", {})
    confl= set(result.get("confluence_levels", []))

    # ── draw all Fib levels ──────────────────────────────────────────────────
    for levels_dict in (ret, ext):
        for key, price in levels_dict.items():
            color = FIB_COLORS.get(key, "#7f8c8d")
            lw    = 2.0 if key == "fib_618" else 1.0
            ls    = "--" if key in ("fib_1272", "fib_1618") else "-"
            ax.axhline(price, color=color, lw=lw, ls=ls, alpha=0.7, zorder=2)
            label = FIB_LABELS.get(key, key)
            # Bold if golden ratio
            weight = "bold" if key == "fib_618" else "normal"
            ax.text(n - 1, price, f" {label} {price:.2f}",
                    va="center", fontsize=7, color=color, fontweight=weight)

    # ── MA confluence markers ────────────────────────────────────────────────
    ma_map = {
        "sma20":  result.get("retracement_levels", {}).get("fib_618"),  # placeholder
        "sma50":  None,
        "sma200": None,
    }
    # Draw star where confluence hits golden ratio
    if result.get("has_confluence_at_golden_ratio"):
        fib618_price = ret.get("fib_618", None)
        if fib618_price:
            ax.axhline(fib618_price, color="#e74c3c", lw=2.5, ls="-", alpha=0.9, zorder=4)
            ax.annotate("◆ MA Confluence", xy=(n // 2, fib618_price),
                        fontsize=8, color="#c0392b", fontweight="bold",
                        xytext=(0, 6), textcoords="offset points")

    # ── swing pivot markers ──────────────────────────────────────────────────
    sh_ago = result.get("swing_high_bars_ago", 0)
    sl_ago = result.get("swing_low_bars_ago", 0)
    sh_bar = n - 1 - sh_ago
    sl_bar = n - 1 - sl_ago
    if 0 <= sh_bar < n:
        ax.plot(sh_bar, result["swing_high"], "v", color="#27ae60", ms=9, zorder=5, label="Swing High")
    if 0 <= sl_bar < n:
        ax.plot(sl_bar, result["swing_low"],  "^", color="#e74c3c", ms=9, zorder=5, label="Swing Low")

    # ── entry signal marker ───────────────────────────────────────────────────
    entry = result.get("entry_signal", "none")
    cp    = result.get("current_price", close[-1])
    if entry == "bullish_entry":
        ax.plot(n - 1, cp, "D", color="#27ae60", ms=12, zorder=6, label="Bullish Entry")
        ax.annotate("  BULLISH\n  ENTRY", xy=(n - 1, cp), fontsize=9,
                    color="#27ae60", fontweight="bold")
    elif entry == "bearish_entry":
        ax.plot(n - 1, cp, "D", color="#c0392b", ms=12, zorder=6, label="Bearish Entry")
        ax.annotate("  BEARISH\n  ENTRY", xy=(n - 1, cp), fontsize=9,
                    color="#c0392b", fontweight="bold")

    # ── stop-loss line ───────────────────────────────────────────────────────
    sl_lvl = result.get("stop_loss_level")
    if sl_lvl:
        ax.axhline(sl_lvl, color="#e67e22", lw=1.5, ls=":", alpha=0.9, zorder=3)
        ax.text(1, sl_lvl, f" Stop {sl_lvl:.2f}", va="center", fontsize=7,
                color="#e67e22", fontweight="bold")

    # ── direction badge ──────────────────────────────────────────────────────
    direction = result.get("anchor_direction", "?")
    badge_color = "#27ae60" if direction == "uptrend" else "#c0392b"
    ax.text(0.01, 0.97, f"  {direction.upper()}  ", transform=ax.transAxes,
            va="top", ha="left", fontsize=9, fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=badge_color, alpha=0.85))

    ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
    ax.set_ylabel("Price", fontsize=9)
    ax.set_xlabel("Bar", fontsize=9)
    ax.legend(loc="upper left", fontsize=7, framealpha=0.7)
    ax.grid(True, alpha=0.25, lw=0.5)


def plot_conditions_panel(ax: plt.Axes, result: dict, title: str) -> None:
    """Bar chart showing which entry conditions passed/failed."""
    conds = result.get("entry_conditions", {})
    if not conds:
        ax.text(0.5, 0.5, "No entry conditions\n(error result)", transform=ax.transAxes,
                ha="center", va="center", fontsize=10)
        ax.set_title(title, fontsize=10)
        return

    labels = list(conds.keys())
    values = [1 if v else 0 for v in conds.values()]
    colors = ["#27ae60" if v else "#e74c3c" for v in values]

    bars = ax.barh(labels, values, color=colors, edgecolor="white", height=0.5)
    for bar, val, lbl in zip(bars, values, conds.values()):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                "✓ PASS" if lbl else "✗ FAIL",
                va="center", fontsize=9, fontweight="bold",
                color="#27ae60" if lbl else "#e74c3c")

    entry = result.get("entry_signal", "none")
    entry_color = "#27ae60" if entry == "bullish_entry" else (
                  "#c0392b" if entry == "bearish_entry" else "#7f8c8d")
    ax.set_title(f"{title}\nSignal: {entry}", fontsize=10, color=entry_color, fontweight="bold")
    ax.set_xlim(0, 1.5)
    ax.set_xticks([])
    ax.grid(False)


# ─── Build figures ────────────────────────────────────────────────────────────

def build_synthetic_figure() -> plt.Figure:
    SW_LO = 100.0; SW_HI = 200.0
    fib618_up = SW_HI - 0.618 * (SW_HI - SW_LO)
    fib618_dn = SW_LO + 0.618 * (SW_HI - SW_LO)
    fib500    = SW_HI - 0.500 * (SW_HI - SW_LO)

    # ── Four scenarios ────────────────────────────────────────────────────────
    scenarios = []

    # 1: Uptrend pullback at 61.8% — bullish entry, MA confluence
    c,h,l,v = make_ohlcv([(150,SW_LO,25),(SW_LO,SW_HI,40),(SW_HI,fib618_up,30)])
    n = len(c)
    rsi = S(np.full(n, 40.0))
    sma50 = S(np.full(n, fib618_up * 0.997))
    r1 = detect_fibonacci_signals(S(c),S(h),S(l),S(v),rsi,
                                   S(np.full(n, fib618_up+5)), sma50, S(np.full(n,80.0)))
    scenarios.append((c,h,l,v,r1,"S1: Uptrend @ 61.8% — Bullish Entry + Confluence"))

    # 2: Downtrend bounce at 61.8% — bearish entry
    c2,h2,l2,v2 = make_ohlcv([(150,SW_HI,25),(SW_HI,SW_LO,40),(SW_LO,fib618_dn,30)])
    n2 = len(c2)
    rsi2 = S(np.full(n2, 60.0))
    sma50_2 = S(np.full(n2, fib618_dn*1.003))
    r2 = detect_fibonacci_signals(S(c2),S(h2),S(l2),S(v2),rsi2,
                                   S(np.full(n2,fib618_dn+10)), sma50_2, S(np.full(n2,220.0)))
    scenarios.append((c2,h2,l2,v2,r2,"S2: Downtrend @ 61.8% — Bearish Entry + Confluence"))

    # 3: Uptrend at 61.8% but RSI too high → no entry
    rsi3 = S(np.full(n, 60.0))
    r3 = detect_fibonacci_signals(S(c),S(h),S(l),S(v),rsi3,
                                   S(np.full(n, fib618_up+5)), sma50, S(np.full(n,80.0)))
    scenarios.append((c,h,l,v,r3,"S3: Uptrend @ 61.8% — RSI Too High (No Entry)"))

    # 4: Uptrend at 50% level → not golden ratio, no confluence
    c4,h4,l4,v4 = make_ohlcv([(150,SW_LO,25),(SW_LO,SW_HI,40),(SW_HI,fib500,30)])
    n4 = len(c4)
    rsi4 = S(np.full(n4, 40.0))
    sma_far = S(np.full(n4, 50.0))
    r4 = detect_fibonacci_signals(S(c4),S(h4),S(l4),S(v4),rsi4,sma_far,sma_far,sma_far)
    scenarios.append((c4,h4,l4,v4,r4,"S4: Uptrend @ 50% — Not Golden Ratio, No Confluence"))

    fig = plt.figure(figsize=(20, 24), facecolor="#f8f9fa")
    fig.suptitle("detect_fibonacci_signals — Synthetic Scenario Visualisation",
                 fontsize=14, fontweight="bold", y=0.995)

    gs = GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.35,
                  left=0.06, right=0.88, top=0.97, bottom=0.03)

    for row, (c, h, l, v, result, title) in enumerate(scenarios):
        ax_price = fig.add_subplot(gs[row, 0])
        ax_conds = fig.add_subplot(gs[row, 1])
        plot_fib_panel(ax_price, c, h, l, v, result, title)
        plot_conditions_panel(ax_conds, result, "Entry Conditions")

    return fig


def build_live_figure(ticker: str) -> plt.Figure:
    import yfinance as yf
    from calculate_technicals import calculate_technicals
    import ta

    data = calculate_technicals(ticker)
    fib_result = data.get("fibonacci", {})

    stock = yf.Ticker(ticker)
    hist  = stock.history(period="1y")
    close  = hist["Close"].values
    high_  = hist["High"].values
    low_   = hist["Low"].values
    volume = hist["Volume"].values.astype(float)

    # RSI for the subplot
    rsi_series = ta.momentum.RSIIndicator(hist["Close"], window=14).rsi()

    fig = plt.figure(figsize=(20, 12), facecolor="#f8f9fa")
    fig.suptitle(f"{ticker.upper()} — Fibonacci Signal Analysis (1y)", fontsize=14,
                 fontweight="bold", y=0.998)

    gs = GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35,
                  height_ratios=[3, 1, 2],
                  left=0.06, right=0.88, top=0.97, bottom=0.04)

    # Price + Fib panel (spans full width top row)
    ax_price = fig.add_subplot(gs[0, :])
    plot_fib_panel(ax_price, close, high_, low_, volume, fib_result,
                   f"{ticker.upper()} — Fibonacci Levels")

    # RSI subplot
    ax_rsi = fig.add_subplot(gs[1, :])
    bars   = np.arange(len(rsi_series))
    ax_rsi.plot(bars, rsi_series.values, color="#3498db", lw=1.2)
    ax_rsi.axhline(70, color="#e74c3c", lw=0.8, ls="--", alpha=0.7)
    ax_rsi.axhline(30, color="#27ae60", lw=0.8, ls="--", alpha=0.7)
    ax_rsi.axhline(45, color="#f39c12", lw=0.8, ls=":", alpha=0.6, label="Bull threshold 45")
    ax_rsi.axhline(55, color="#9b59b6", lw=0.8, ls=":", alpha=0.6, label="Bear threshold 55")
    ax_rsi.fill_between(bars, 30, 70, alpha=0.05, color="#3498db")
    current_rsi = rsi_series.dropna().iloc[-1]
    ax_rsi.plot(len(rsi_series)-1, current_rsi, "o", color="#e74c3c", ms=6, zorder=5)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_title(f"RSI(14) — current: {current_rsi:.1f}", fontsize=9)
    ax_rsi.legend(fontsize=7, loc="upper left")
    ax_rsi.grid(True, alpha=0.25, lw=0.5)

    # Entry conditions panel
    ax_conds = fig.add_subplot(gs[2, 0])
    plot_conditions_panel(ax_conds, fib_result, "Entry Conditions")

    # Summary table
    ax_table = fig.add_subplot(gs[2, 1])
    ax_table.axis("off")

    rows = [
        ["Anchor direction",        fib_result.get("anchor_direction", "—")],
        ["Bars since anchor",        str(fib_result.get("bars_since_anchor", "—"))],
        ["Swing high",               f"{fib_result.get('swing_high','—'):.2f}" if fib_result.get('swing_high') else "—"],
        ["Swing low",                f"{fib_result.get('swing_low','—'):.2f}" if fib_result.get('swing_low') else "—"],
        ["Current price",            f"{fib_result.get('current_price','—'):.2f}" if fib_result.get('current_price') else "—"],
        ["Nearest retracement",      fib_result.get("nearest_retracement", "—")],
        ["At golden ratio (61.8%)",  "Yes ★" if fib_result.get("at_golden_ratio") else "No"],
        ["MA confluence at 61.8%",   "Yes ★" if fib_result.get("has_confluence_at_golden_ratio") else "No"],
        ["Confluence levels",        ", ".join(fib_result.get("confluence_levels", [])) or "None"],
        ["Entry signal",             fib_result.get("entry_signal", "none").upper()],
        ["Stop-loss level",          f"{fib_result.get('stop_loss_level','—'):.2f}" if fib_result.get("stop_loss_level") else "None"],
        ["Target 1 (swing end)",     f"{fib_result.get('target_1_swing_end','—'):.2f}" if fib_result.get('target_1_swing_end') else "—"],
        ["Target 2 (127.2%)",        f"{fib_result.get('target_2_ext_1272','—'):.2f}" if fib_result.get('target_2_ext_1272') else "—"],
        ["Target 3 (161.8%)",        f"{fib_result.get('target_3_ext_1618','—'):.2f}" if fib_result.get('target_3_ext_1618') else "—"],
    ]

    entry = fib_result.get("entry_signal", "none")
    header_color = "#27ae60" if entry == "bullish_entry" else (
                   "#c0392b" if entry == "bearish_entry" else "#7f8c8d")

    table = ax_table.table(
        cellText=rows,
        colLabels=["Field", "Value"],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#ecf0f1")
        cell.set_edgecolor("white")
    ax_table.set_title(f"{ticker.upper()} Fibonacci Summary", fontsize=10,
                       fontweight="bold", pad=8)

    return fig


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", metavar="TICKER", help="Plot live ticker data")
    parser.add_argument("--out",  default="tests/fibonacci_plot.png", help="Output PNG path")
    args = parser.parse_args()

    if args.live:
        print(f"Fetching live data for {args.live.upper()}...")
        fig = build_live_figure(args.live.upper())
    else:
        print("Building synthetic scenario plot...")
        fig = build_synthetic_figure()

    out = args.out if args.out else "tests/fibonacci_plot.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved → {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
