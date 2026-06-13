# tab_dashboard.py – Dashboard Tab
import customtkinter as ctk
import tkinter as tk
from config import COLORS, TYPE_COLORS
import lang as L
from database import get_last_messung, get_today, get_messungen, calc_statistik
from dashboard_cards import CardRow
from chart_utils import build_week_chart
from utils import format_date_de, type_label, status_color, wert_display


class TabDashboard(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._chart_canvas = None
        self._chart_widget = None
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Statistik-Karten
        self._card_row = CardRow(self)
        self._card_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,4))

        # Chart
        chart_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                                    border_width=1, border_color=COLORS["border"])
        chart_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=6)
        chart_frame.grid_columnconfigure(0, weight=1)
        self._chart_host = chart_frame

        # Heutige Messungen
        today_lbl = ctk.CTkLabel(self, text=L.t("today_count"),
                                  font=ctk.CTkFont(size=13, weight="bold"),
                                  text_color=COLORS["text"])
        today_lbl.grid(row=2, column=0, sticky="w", padx=20, pady=(10,4))

        self._today_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._today_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0,14))
        self._today_frame.grid_columnconfigure((0,1,2), weight=1)

        self.refresh()

    def refresh(self):
        unit   = self._s.get("unit", "mmol/L")
        low    = self._s.get("target_low",  3.9)
        high   = self._s.get("target_high", 7.8)
        last_m = get_last_messung(user_id=self._s.get("active_user_id",1))
        today  = get_today(user_id=self._s.get("active_user_id",1))
        ms7    = get_messungen(7, user_id=self._s.get("active_user_id",1))
        stat7  = calc_statistik(7, low, high, user_id=self._s.get("active_user_id",1))
        stat30 = calc_statistik(30, low, high, user_id=self._s.get("active_user_id",1))

        # Tagesdurchschnitt
        from models import Statistik
        import math
        if today:
            vals  = [m.wert_mmol for m in today]
            n     = len(vals)
            avg   = sum(vals)/n
            std   = math.sqrt(sum((v-avg)**2 for v in vals)/n) if n>1 else 0
            stat_today = Statistik(n, round(avg,2), round(std,2),
                                   round(min(vals),2), round(max(vals),2), 0, 0)
        else:
            stat_today = Statistik.empty()

        self._card_row.refresh(last_m, stat_today, stat7, stat30, unit)
        self._rebuild_chart(ms7, unit, low, high)
        self._rebuild_today(today, unit, low, high)

    def _rebuild_chart(self, ms, unit, low, high):
        # Alten Chart entfernen
        for w in self._chart_host.winfo_children():
            w.destroy()
        self._chart_widget = build_week_chart(self._chart_host, ms, unit, low, high)
        self._chart_widget.get_tk_widget().pack(fill="x", expand=True, padx=4, pady=8)

    def _rebuild_today(self, today, unit, low, high):
        for w in self._today_frame.winfo_children():
            w.destroy()
        if not today:
            ctk.CTkLabel(self._today_frame, text=L.t("no_data"),
                          text_color=COLORS["text_muted"],
                          font=ctk.CTkFont(size=12)
                          ).grid(row=0, column=0)
            return
        for i, m in enumerate(today):
            col = status_color(m.wert_mmol, low, high)
            tc  = TYPE_COLORS.get(m.typ, COLORS["border"])
            card = ctk.CTkFrame(self._today_frame, corner_radius=12,
                                 fg_color=COLORS["card"],
                                 border_width=2, border_color=col)
            card.grid(row=i // 3, column=i % 3, padx=6, pady=4, sticky="ew")
            self._today_frame.grid_columnconfigure(i % 3, weight=1)

            val_str = f"{wert_display(m.wert_mmol, unit)} {unit}"
            ctk.CTkLabel(card, text=val_str,
                          font=ctk.CTkFont(size=20, weight="bold"),
                          text_color=col).pack(pady=(10,2))
            ctk.CTkLabel(card, text=f"{m.uhrzeit}  ·  {type_label(m.typ)}",
                          font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]
                          ).pack()
            if m.notiz:
                ctk.CTkLabel(card, text=m.notiz[:28], font=ctk.CTkFont(size=9),
                              text_color=COLORS["text_muted"]).pack(pady=(0,6))
            else:
                ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    def on_show(self):
        self.refresh()
