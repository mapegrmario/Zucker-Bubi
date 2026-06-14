# dashboard_cards.py – Runde Statistik-Karten mit Canvas
import customtkinter as ctk
import tkinter as tk
from config import COLORS
from utils import status_color, tir_color, hba1c_color
import lang as L


class RoundCard(ctk.CTkFrame):
    """Karte mit rundem farbigen Wert-Kreis oben"""
    def __init__(self, parent, label: str, value: str = "–",
                 unit: str = "", circle_color: str = COLORS["primary"],
                 sub: str = ""):
        super().__init__(parent, corner_radius=16, fg_color=COLORS["card"],
                         border_width=1, border_color=COLORS["border"])
        self._label = label
        self._circ_color = circle_color
        self._build(value, unit, sub)

    def _build(self, value, unit, sub):
        self.grid_columnconfigure(0, weight=1)
        # Kreis-Canvas
        self._canvas = tk.Canvas(self, width=90, height=90,
                                  bg=COLORS["card"], highlightthickness=0)
        self._canvas.grid(row=0, column=0, pady=(14, 4))
        self._draw_circle(value, unit)

        ctk.CTkLabel(self, text=self._label,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLORS["text_muted"]
                     ).grid(row=1, column=0, padx=10)

        # Direkte Referenz speichern – kein fragiles Suchen per Fontgröße
        self._sub_lbl = ctk.CTkLabel(self, text=sub,
                                      font=ctk.CTkFont(size=9),
                                      text_color=COLORS["text_muted"])
        self._sub_lbl.grid(row=2, column=0, padx=10, pady=(0, 12))

    def _draw_circle(self, value: str, unit: str):
        c = self._canvas
        c.delete("all")
        # Äußerer Ring
        c.create_oval(5, 5, 85, 85, fill=self._circ_color,
                       outline="", width=0)
        # Innerer Kreis (weiß)
        c.create_oval(12, 12, 78, 78, fill=COLORS["card"],
                       outline="", width=0)
        # Wert-Text
        c.create_text(45, 40, text=str(value),
                       fill=self._circ_color,
                       font=("Segoe UI", 16, "bold"))
        if unit:
            c.create_text(45, 60, text=unit,
                           fill=COLORS["text_muted"],
                           font=("Segoe UI", 8))

    def update_value(self, value: str, unit: str = "",
                     circle_color: str = None, sub: str = ""):
        if circle_color:
            self._circ_color = circle_color
        self._draw_circle(value, unit)
        self._sub_lbl.configure(text=sub)   # direkte Referenz


class CardRow(ctk.CTkFrame):
    """Zeile mit 5 RoundCards"""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure((0,1,2,3,4), weight=1)
        self._cards = {}
        specs = [
            ("last",   L.t("last_value"),   COLORS["primary"]),
            ("today",  L.t("today_avg"),    COLORS["primary"]),
            ("week",   L.t("week_avg"),     COLORS["accent"]),
            ("month",  L.t("month_avg"),    COLORS["accent"]),
            ("hba1c",  L.t("hba1c_est"),    COLORS["warning"]),
        ]
        for i, (key, lbl, col) in enumerate(specs):
            card = RoundCard(self, lbl, "–", "", col)
            card.grid(row=0, column=i, padx=6, pady=8, sticky="nsew")
            self._cards[key] = card

    def refresh(self, last_m, today_stats, stats7, stats30, unit):
        from database import calc_statistik, get_today
        from models import Statistik

        def _fmt(v):
            if unit == "mg/dL": return str(round(v * 18))
            return f"{v:.1f}".replace(".", ",")

        # Letzter Wert
        if last_m:
            col = status_color(last_m.wert_mmol)
            self._cards["last"].update_value(_fmt(last_m.wert_mmol), unit, col,
                                              f"{last_m.datum[-5:]} {last_m.uhrzeit}")
        # Tages-Ø
        if today_stats.count:
            col = status_color(today_stats.avg)
            self._cards["today"].update_value(_fmt(today_stats.avg), unit, col,
                                               f"{today_stats.count}× heute")
        # 7-Tage-Ø
        if stats7.count:
            col = status_color(stats7.avg)
            self._cards["week"].update_value(_fmt(stats7.avg), unit, col,
                                              f"n={stats7.count}")
        # 30-Tage-Ø
        if stats30.count:
            col = status_color(stats30.avg)
            self._cards["month"].update_value(_fmt(stats30.avg), unit, col,
                                               f"n={stats30.count}")
        # HbA1c
        if stats30.count:
            col = hba1c_color(stats30.hba1c)
            self._cards["hba1c"].update_value(f"{stats30.hba1c:.1f}", "%", col,
                                               L.t("hba1c_est"))
