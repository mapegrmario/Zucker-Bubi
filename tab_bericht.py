# tab_bericht.py – Arztbericht mit Patientendaten aus der users-Tabelle
import customtkinter as ctk
import tkinter.filedialog as fd
import os, threading
from config import COLORS
from database import get_messungen, calc_statistik, get_user
from chart_utils import build_pdf_chart
from pdf_generator import generate_pdf
import lang as L

PERIODS = [7, 14, 30, 90]


class TabBericht(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._days = 30
        self._build()

    def _unit(self): return self._s.get("unit", "mmol/L")
    def _uid(self):  return self._s.get("active_user_id", 1)

    def _get_user_settings(self) -> dict:
        """Patientendaten aus der users-Tabelle holen und mit settings mergen."""
        merged = self._s.copy()
        user = get_user(self._uid())
        if user:
            merged["patient_name"]    = user.name
            merged["patient_dob"]     = user.dob
            merged["patient_id"]      = user.patient_id
            merged["doctor_name"]     = user.doctor_name
            merged["doctor_address"]  = user.doctor_address
            merged["target_low"]      = user.target_low
            merged["target_high"]     = user.target_high
        return merged

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text=L.t("bericht"),
                      font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 8))

        # Optionen-Karte
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=COLORS["card"],
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)
        self._build_options(card)

        # Vorschau
        preview = ctk.CTkFrame(self, corner_radius=16, fg_color=COLORS["card"],
                                border_width=1, border_color=COLORS["border"])
        preview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 18))
        preview.grid_columnconfigure(0, weight=1)
        self._build_preview(preview)

    def _build_options(self, card):
        pad = {"padx": 18, "pady": 8}
        LBL = {"font": ctk.CTkFont(size=12, weight="bold"),
               "text_color": COLORS["text_muted"], "anchor": "e"}

        ctk.CTkLabel(card, text=L.t("report_period"), **LBL
                      ).grid(row=0, column=0, sticky="e", **pad)

        per_f = ctk.CTkFrame(card, fg_color="transparent")
        per_f.grid(row=0, column=1, sticky="w", **pad)
        self._per_btns = {}
        for d in PERIODS:
            btn = ctk.CTkButton(
                per_f, text=L.t(f"days_{d}"), width=80, height=32,
                corner_radius=8, font=ctk.CTkFont(size=11),
                fg_color=COLORS["primary"] if d == self._days else COLORS["bg2"],
                text_color="white" if d == self._days else COLORS["text"],
                hover_color=COLORS["primary_dark"],
                command=lambda x=d: self._set_days(x))
            btn.pack(side="left", padx=4)
            self._per_btns[d] = btn

        # Patienteninfo-Zeile (live aus DB)
        self._pat_lbl = ctk.CTkLabel(card, text="",
                                      font=ctk.CTkFont(size=11),
                                      text_color=COLORS["text_muted"])
        self._pat_lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 4))

        # PDF-Button
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="e", padx=18, pady=(4, 14))
        self._pdf_btn = ctk.CTkButton(
            btn_row, text=L.t("btn_pdf"), width=180, height=38,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_pdf)
        self._pdf_btn.pack(side="left", padx=(0, 10))
        self._status_lbl = ctk.CTkLabel(btn_row, text="",
                                         font=ctk.CTkFont(size=11),
                                         text_color=COLORS["normal"])
        self._status_lbl.pack(side="left")

    def _build_preview(self, parent):
        self._prev_labels = {}
        rows_spec = [
            ("count", L.t("today_count")),
            ("avg",   L.t("avg")),
            ("min",   L.t("min")),
            ("max",   L.t("max")),
            ("hba1c", L.t("hba1c_est")),
            ("tir",   L.t("tir")),
        ]
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(pady=16, padx=20, fill="x")
        for i, (key, lbl) in enumerate(rows_spec):
            col = (i % 3) * 2
            row = i // 3
            ctk.CTkLabel(grid, text=lbl + ":",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color=COLORS["text_muted"]
                          ).grid(row=row, column=col, sticky="e", padx=(12, 4), pady=6)
            val_lbl = ctk.CTkLabel(grid, text="–",
                                    font=ctk.CTkFont(size=13), text_color=COLORS["text"])
            val_lbl.grid(row=row, column=col + 1, sticky="w", padx=(0, 20), pady=6)
            self._prev_labels[key] = val_lbl

        ctk.CTkLabel(parent, text="⚠  " + L.t("disclaimer"),
                      font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"],
                      wraplength=500).pack(pady=(0, 14))

    def _set_days(self, days: int):
        self._days = days
        for d, btn in self._per_btns.items():
            btn.configure(fg_color=COLORS["primary"] if d == days else COLORS["bg2"],
                          text_color="white" if d == days else COLORS["text"])
        self._update_preview()

    def _update_preview(self):
        s = self._get_user_settings()
        unit = self._unit()
        low  = s.get("target_low", 3.9)
        high = s.get("target_high", 7.8)
        stat = calc_statistik(self._days, low, high, user_id=self._uid())

        def v(mmol):
            return f"{round(mmol*18)} {unit}" if unit == "mg/dL" else f"{mmol:.1f} {unit}"

        self._prev_labels["count"].configure(text=str(stat.count))
        self._prev_labels["avg"  ].configure(text=v(stat.avg)     if stat.count else "–")
        self._prev_labels["min"  ].configure(text=v(stat.min_val) if stat.count else "–")
        self._prev_labels["max"  ].configure(text=v(stat.max_val) if stat.count else "–")
        self._prev_labels["hba1c"].configure(text=f"{stat.hba1c:.1f} %" if stat.count else "–")
        self._prev_labels["tir"  ].configure(text=f"{stat.tir_pct:.1f} %" if stat.count else "–")

        pat = s.get("patient_name", "–") or "–"
        doc = s.get("doctor_name",  "–") or "–"
        self._pat_lbl.configure(
            text=f"Patient: {pat}   |   Arzt: {doc}")

    def _create_pdf(self):
        path = fd.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"ZuckerBubi_Bericht_{self._days}Tage.pdf")
        if not path:
            return
        self._pdf_btn.configure(state="disabled", text="⏳ Erstelle PDF …")

        def _run():
            try:
                # Patientendaten aus DB laden
                s    = self._get_user_settings()
                unit = self._unit()
                low  = s.get("target_low", 3.9)
                high = s.get("target_high", 7.8)
                ms   = get_messungen(self._days, user_id=self._uid())
                stat = calc_statistik(self._days, low, high, user_id=self._uid())
                chart = build_pdf_chart(ms, unit, low, high, self._days)
                generate_pdf(ms, stat, s, unit, self._days, chart, path)
                self.after(0, lambda: self._on_done(path, None))
            except Exception as e:
                self.after(0, lambda: self._on_done(None, str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, path, err):
        self._pdf_btn.configure(state="normal", text=L.t("btn_pdf"))
        if err:
            self._status_lbl.configure(text=f"❌ {err}", text_color=COLORS["danger"])
        else:
            self._status_lbl.configure(
                text=f"✓ {os.path.basename(path)}", text_color=COLORS["normal"])

    def on_show(self):
        self._update_preview()

    def refresh(self):
        self._update_preview()
