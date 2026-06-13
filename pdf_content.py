# pdf_content.py – PDF-Inhaltsbausteine
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from typing import List
from models import Messung, Statistik
from config import TYPE_COLORS
import lang as L

C_PRIMARY = colors.HexColor("#2E86AB")
C_LIGHT   = colors.HexColor("#D6EEF5")
C_GREEN   = colors.HexColor("#48BB78")
C_ORANGE  = colors.HexColor("#F6AD55")
C_RED     = colors.HexColor("#FC8181")
C_BORDER  = colors.HexColor("#CBD5E0")
C_HEADER  = colors.HexColor("#EFF3F8")
C_TEXT    = colors.HexColor("#1A202C")


def _val_color(wert: float, low: float, high: float):
    if wert < 3.0 or wert > 10.0: return C_RED
    if wert < low or wert > high:  return C_ORANGE
    return C_GREEN


def build_stat_table(stat: Statistik, unit: str, s: dict) -> Table:
    def v(mmol): return f"{round(mmol*18)} {unit}" if unit == "mg/dL" else f"{mmol:.1f} {unit}"
    rows = [
        [L.t("today_count"), str(stat.count),
         L.t("hba1c_est"),   f"{stat.hba1c:.1f} %"],
        [L.t("avg"),         v(stat.avg),
         L.t("min"),         v(stat.min_val)],
        [L.t("std"),         v(stat.std),
         L.t("max"),         v(stat.max_val)],
    ]
    t = Table(rows, colWidths=[4.0*cm, 3.5*cm, 4.0*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), C_HEADER),
        ("BACKGROUND", (2,0), (2,-1), C_HEADER),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",   (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTNAME",   (2,0), (2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8.5),
        ("TEXTCOLOR",  (0,0), (-1,-1), C_TEXT),
        ("GRID",       (0,0), (-1,-1), 0.4, C_BORDER),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, C_HEADER]),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
    ]))
    return t


def build_tir_bar(tir_pct: float, s: dict) -> Drawing:
    """Horizontaler Balken für Zeit im Zielbereich"""
    w = 480
    d = Drawing(w, 28)
    outside = max(0, 100 - tir_pct)
    tir_w = int(w * tir_pct / 100)
    out_w = w - tir_w
    d.add(Rect(0,   8, tir_w, 14, fillColor=C_GREEN,  strokeColor=None))
    d.add(Rect(tir_w, 8, out_w, 14, fillColor=C_ORANGE, strokeColor=None))
    d.add(String(tir_w/2, 10, f"Im Ziel: {tir_pct:.1f}%",
                 fontSize=7.5, fillColor=colors.white, textAnchor="middle"))
    d.add(String(tir_w + out_w/2, 10, f"Außerhalb: {outside:.1f}%",
                 fontSize=7.5, fillColor=colors.white, textAnchor="middle"))
    return d


def build_measurements_table(messungen: List[Messung], unit: str,
                              settings: dict, s: dict) -> Table:
    low  = settings.get("target_low",  3.9)
    high = settings.get("target_high", 7.8)
    header = [L.t("lbl_date"), L.t("lbl_time"), L.t("lbl_value"),
              L.t("lbl_type"), L.t("lbl_note")]
    rows = [header]
    row_styles = [
        ("BACKGROUND", (0,0), (-1,0), C_PRIMARY),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("GRID",       (0,0), (-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",     (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 4),
        ("LEFTPADDING",    (0,0), (-1,-1), 5),
    ]
    for i, m in enumerate(messungen[:60]):  # max 60 Zeilen
        from utils import format_date_de, type_label, wert_display
        val_str = f"{wert_display(m.wert_mmol, unit)} {unit}"
        row = [format_date_de(m.datum), m.uhrzeit, val_str,
               type_label(m.typ), m.notiz[:30]]
        rows.append(row)
        vc = _val_color(m.wert_mmol, low, high)
        row_styles.append(("BACKGROUND", (2, i+1), (2, i+1), vc))
        if i % 2 == 0:
            row_styles.append(("BACKGROUND", (0,i+1),(1,i+1), C_HEADER))
            row_styles.append(("BACKGROUND", (3,i+1),(4,i+1), C_HEADER))

    t = Table(rows, colWidths=[2.8*cm, 2.0*cm, 2.8*cm, 3.0*cm, None])
    t.setStyle(TableStyle(row_styles))
    return t
