# utils.py – Allgemeine Hilfsfunktionen
from datetime import datetime, date
from config import COLORS, REF
import lang as L


def status_color(wert_mmol: float, low: float = None, high: float = None) -> str:
    lo = low  if low  is not None else REF["low"]
    hi = high if high is not None else REF["normal_hi"]
    if wert_mmol < REF["very_low"]: return COLORS["very_low"]
    if wert_mmol < lo:              return COLORS["low"]
    if wert_mmol <= hi:             return COLORS["normal"]
    if wert_mmol <= REF["high"]:    return COLORS["high"]
    return COLORS["very_high"]


def status_label(wert_mmol: float, low: float = None, high: float = None) -> str:
    lo = low  if low  is not None else REF["low"]
    hi = high if high is not None else REF["normal_hi"]
    if wert_mmol < REF["very_low"]: return L.t("status_very_low")
    if wert_mmol < lo:              return L.t("status_low")
    if wert_mmol <= hi:             return L.t("status_normal")
    if wert_mmol <= REF["high"]:    return L.t("status_high")
    return L.t("status_very_high")


def now_date() -> str:
    return date.today().isoformat()


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def format_date_de(iso: str) -> str:
    """YYYY-MM-DD → DD.MM.YYYY"""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return d.strftime("%d.%m.%Y")
    except Exception:
        return iso


def parse_date(s: str) -> str | None:
    """DD.MM.YYYY oder YYYY-MM-DD → YYYY-MM-DD oder None"""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def type_label(typ: str) -> str:
    return L.t(f"type_{typ}")


def hba1c_color(hba1c: float) -> str:
    if hba1c < 6.5:  return COLORS["normal"]
    if hba1c < 7.5:  return COLORS["high"]
    return COLORS["very_high"]


def tir_color(tir: float) -> str:
    if tir >= 70: return COLORS["normal"]
    if tir >= 50: return COLORS["high"]
    return COLORS["very_high"]


def wert_display(wert_mmol: float, unit: str) -> str:
    if unit == "mg/dL":
        return str(round(wert_mmol * 18))
    return f"{wert_mmol:.1f}".replace(".", ",")
