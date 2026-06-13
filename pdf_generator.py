# pdf_generator.py – PDF-Arztbericht (Patientendaten prominent neben Arzt)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import date
from typing import List
from config import APP_NAME, APP_VERSION, AUTHOR, AVATAR_PATH
from models import Messung, Statistik
import lang as L

C_PRIMARY = colors.HexColor("#2E86AB")
C_DARK    = colors.HexColor("#1A6B8A")
C_LIGHT   = colors.HexColor("#D6EEF5")
C_TEXT    = colors.HexColor("#1A202C")
C_MUTED   = colors.HexColor("#718096")
C_BORDER  = colors.HexColor("#CBD5E0")
C_PAT_BG  = colors.HexColor("#EFF8FF")   # Patientendaten-Hintergrund
C_DOC_BG  = colors.HexColor("#F0FFF4")   # Arztdaten-Hintergrund


def _styles():
    return {
        "title":   ParagraphStyle("title",  fontSize=20, textColor=C_PRIMARY,
                                   spaceAfter=4, fontName="Helvetica-Bold"),
        "h2":      ParagraphStyle("h2",     fontSize=11, textColor=C_PRIMARY,
                                   spaceAfter=3, fontName="Helvetica-Bold", spaceBefore=10),
        "pat":     ParagraphStyle("pat",    fontSize=10, textColor=C_TEXT,
                                   fontName="Helvetica-Bold", leading=16),
        "pat_sub": ParagraphStyle("pat_sub",fontSize=8.5, textColor=C_MUTED,
                                   fontName="Helvetica", leading=13),
        "normal":  ParagraphStyle("normal", fontSize=8.5, textColor=C_TEXT,
                                   fontName="Helvetica", leading=13),
        "small":   ParagraphStyle("small",  fontSize=7.5, textColor=C_MUTED,
                                   fontName="Helvetica"),
        "center":  ParagraphStyle("center", fontSize=7, alignment=TA_CENTER,
                                   textColor=C_MUTED, fontName="Helvetica"),
    }


def _header_table(settings: dict, s: dict):
    """Drei-Spalten-Header: Avatar | Patient (hervorgehoben) | Arzt"""
    # Avatar
    avatar_cell = ""
    if AVATAR_PATH.exists():
        try:
            avatar_cell = Image(str(AVATAR_PATH), width=2.0*cm, height=2.0*cm)
        except Exception:
            pass

    # Patientendaten (hervorgehoben)
    pname = settings.get("patient_name", "–")
    pdob  = settings.get("patient_dob",  "–")
    pid   = settings.get("patient_id",   "–")
    pat_content = [
        Paragraph("PATIENT", ParagraphStyle("lbl", fontSize=7, textColor=C_PRIMARY,
                                             fontName="Helvetica-Bold")),
        Paragraph(pname, ParagraphStyle("pn", fontSize=13, textColor=C_DARK,
                                         fontName="Helvetica-Bold", leading=16)),
        Paragraph(f"Geb.: {pdob}", s["pat_sub"]),
        Paragraph(f"ID:   {pid}",  s["pat_sub"]),
    ]

    # Arztdaten
    doc_name = settings.get("doctor_name",    "–")
    doc_addr = settings.get("doctor_address", "–")
    doc_content = [
        Paragraph("ARZT / PRAXIS", ParagraphStyle("lbl2", fontSize=7, textColor=C_DARK,
                                                   fontName="Helvetica-Bold")),
        Paragraph(doc_name, s["normal"]),
        Paragraph(doc_addr, s["small"]),
        Spacer(1, 4),
        Paragraph(f"Erstellt: {date.today().strftime('%d.%m.%Y')}", s["small"]),
        Paragraph(f"Zeitraum: {settings.get('_days',30)} Tage", s["small"]),
    ]

    tbl = Table(
        [[avatar_cell, pat_content, doc_content]],
        colWidths=[2.4*cm, 8.5*cm, None]
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (1, 0), (1,  0),  10),
        ("LEFTPADDING", (2, 0), (2,  0),  14),
        ("BACKGROUND",  (1, 0), (1,  0),  C_PAT_BG),
        ("BACKGROUND",  (2, 0), (2,  0),  C_DOC_BG),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
        ("TOPPADDING",  (1, 0), (2,  0),  8),
        ("BOTTOMPADDING",(1,0), (2,  0),  8),
        ("RIGHTPADDING",(1, 0), (2,  0),  10),
    ]))
    return tbl


def generate_pdf(
    messungen: List[Messung],
    statistik: Statistik,
    settings: dict,
    unit: str,
    days: int,
    chart_png: bytes,
    output_path: str
):
    settings["_days"] = days   # für Header
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=1.8*cm, bottomMargin=2.5*cm)
    s = _styles()
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story += [_header_table(settings, s),
              HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceAfter=8)]

    # ── Statistik ────────────────────────────────────────────────────────────
    story.append(Paragraph(L.t("report_stats"), s["h2"]))
    from pdf_content import build_stat_table, build_tir_bar, build_measurements_table
    story += [build_stat_table(statistik, unit, s), Spacer(1, 6),
              build_tir_bar(statistik.tir_pct, s), Spacer(1, 8)]

    # ── Chart ────────────────────────────────────────────────────────────────
    story.append(Paragraph(L.t("report_chart"), s["h2"]))
    story += [Image(io.BytesIO(chart_png), width=16*cm, height=5.2*cm), Spacer(1, 8)]

    # ── Messwert-Tabelle ─────────────────────────────────────────────────────
    story.append(Paragraph(L.t("report_table"), s["h2"]))
    story += [build_measurements_table(messungen, unit, settings, s), Spacer(1, 10)]

    # ── Footer ───────────────────────────────────────────────────────────────
    story += [
        HRFlowable(width="100%", thickness=0.5, color=C_BORDER),
        Paragraph(
            f"Erstellt mit {APP_NAME} v{APP_VERSION}  ·  Autor: {AUTHOR}  ·  {L.t('disclaimer')}",
            s["center"])
    ]

    doc.build(story)
    with open(output_path, "wb") as f:
        f.write(buf.getvalue())
