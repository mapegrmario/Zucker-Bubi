# chart_utils.py – Matplotlib-Charts (Agg-Backend, TkAgg-Canvas explizit)
# WICHTIG: matplotlib.use() NIE innerhalb von Funktionen aufrufen –
#           das führt zu Backend-Konflikten. Agg ist immer kompatibel.
import matplotlib
matplotlib.use("Agg")   # Einmalig vor plt-Import – FigureCanvasTkAgg läuft auch mit Agg

import matplotlib.pyplot as plt
from datetime import date, timedelta
from typing import List
from config import COLORS
from models import Messung
import lang as L
import io


def _apply_style(ax, fig):
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFBFC")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(COLORS["border"])
    ax.spines["bottom"].set_color(COLORS["border"])
    ax.tick_params(colors=COLORS["text_muted"], labelsize=8)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4, color=COLORS["border"])


def build_week_chart(parent, messungen: List[Messung], unit: str,
                     low: float = 3.9, high: float = 7.8):
    """Eingebettetes Dashboard-Chart – FigureCanvasTkAgg funktioniert mit Agg-Backend."""
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    fig, ax = plt.subplots(figsize=(7.5, 2.8), dpi=96)
    _apply_style(ax, fig)
    fig.tight_layout(pad=1.5)

    if not messungen:
        ax.text(0.5, 0.5, L.t("no_data"), transform=ax.transAxes,
                ha="center", va="center", color=COLORS["text_muted"], fontsize=11)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas._mpl_fig = fig
        return canvas

    today  = date.today()
    dates  = [(today - timedelta(days=6 - i)) for i in range(7)]
    vals   = []
    for d in dates:
        day_ms = [m.wert_mmol for m in messungen if m.datum == d.isoformat()]
        vals.append(sum(day_ms) / len(day_ms) if day_ms else None)

    y_lo = low  if unit == "mmol/L" else low  * 18
    y_hi = high if unit == "mmol/L" else high * 18
    ymax = max((v for v in vals if v), default=high) * 1.3 + 2
    ax.axhspan(0,    y_lo, alpha=0.10, color=COLORS["very_low"],  zorder=0)
    ax.axhspan(y_lo, y_hi, alpha=0.10, color=COLORS["normal"],    zorder=0)
    ax.axhspan(y_hi, ymax, alpha=0.10, color=COLORS["high"],      zorder=0)
    ax.axhline(y_lo, color=COLORS["low"],  linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axhline(y_hi, color=COLORS["high"], linewidth=0.8, linestyle="--", alpha=0.6)

    xs = list(range(7))
    dv = [(v * 18 if unit == "mg/dL" else v) if v is not None else None for v in vals]
    filled = [(x, y) for x, y in zip(xs, dv) if y is not None]
    if filled:
        fx, fy = zip(*filled)
        ax.plot(fx, fy, color=COLORS["primary"], linewidth=2.2,
                marker="o", markersize=5, zorder=5)
        ax.fill_between(fx, fy, alpha=0.15, color=COLORS["primary"])
        for x, y in zip(fx, fy):
            lbl = f"{y:.1f}" if unit == "mmol/L" else str(int(y))
            ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=7, color=COLORS["text_muted"])

    ax.set_xticks(xs)
    ax.set_xticklabels([d.strftime("%d.%m") for d in dates], fontsize=7.5)
    ax.set_ylabel(unit, fontsize=8, color=COLORS["text_muted"])
    ax.set_title(L.t("last_7days"), fontsize=9, color=COLORS["text"], pad=6)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas._mpl_fig = fig   # für sauberes plt.close() durch den Caller
    return canvas


def build_pdf_chart(messungen: List[Messung], unit: str,
                    low: float, high: float, days: int) -> bytes:
    """Chart als PNG-Bytes für PDF-Einbettung (kein Tk nötig)."""
    fig, ax = plt.subplots(figsize=(6.5, 2.5), dpi=120)
    _apply_style(ax, fig)
    fig.tight_layout(pad=1.5)

    today = date.today()
    dates = [(today - timedelta(days=days - 1 - i)) for i in range(days)]
    vals  = []
    for d in dates:
        day_ms = [m.wert_mmol for m in messungen if m.datum == d.isoformat()]
        vals.append(sum(day_ms) / len(day_ms) if day_ms else None)

    lo, hi = (low * 18, high * 18) if unit == "mg/dL" else (low, high)
    ys = [(v * 18 if unit == "mg/dL" else v) if v else None for v in vals]

    ax.axhspan(lo, hi, alpha=0.12, color="#48BB78")
    ax.axhline(lo, color="#9F7AEA", linewidth=0.8, linestyle="--")
    ax.axhline(hi, color="#F6AD55", linewidth=0.8, linestyle="--")

    filled = [(i, y) for i, y in enumerate(ys) if y is not None]
    if filled:
        fx, fy = zip(*filled)
        ax.plot(fx, fy, color="#2E86AB", linewidth=1.8, marker="o", markersize=3.5)
        ax.fill_between(fx, fy, alpha=0.10, color="#2E86AB")

    step = max(1, days // 10)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i].strftime("%d.%m") for i in range(0, len(dates), step)],
                        fontsize=6.5, rotation=30)
    ax.set_ylabel(unit, fontsize=7)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    return buf.getvalue()
