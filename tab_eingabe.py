# tab_eingabe.py – Manuelle Blutzucker-Eingabe
import customtkinter as ctk
from datetime import datetime, date
from config import COLORS, MEASUREMENT_TYPES, TYPE_COLORS
from models import Messung, parse_input
from database import add_messung
from utils import now_date, now_time, type_label, status_color, wert_display
import lang as L


class TabEingabe(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._refresh = refresh_cb
        self._build()

    def _unit(self): return self._s.get("unit", "mmol/L")

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Titel
        ctk.CTkLabel(self, text=L.t("eingabe"),
                      font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, sticky="w", padx=24, pady=(20,4))

        # Formular-Karte
        card = ctk.CTkFrame(self, corner_radius=16, fg_color=COLORS["card"],
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=1, column=0, padx=24, pady=8, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        self._card = card
        self._build_form(card)

        # Vorschau-Karte (erscheint nach Eingabe)
        self._preview = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                                      border_width=1, border_color=COLORS["border"])
        self._preview.grid(row=2, column=0, padx=24, pady=8, sticky="ew")
        self._preview_lbl = ctk.CTkLabel(self._preview, text="",
                                          font=ctk.CTkFont(size=13))
        self._preview_lbl.pack(pady=10)

    def _build_form(self, card):
        pad = {"padx": 18, "pady": 7}
        LBL = {"font": ctk.CTkFont(size=12, weight="bold"),
               "text_color": COLORS["text_muted"], "anchor": "e"}

        def row(r, lbl, widget):
            ctk.CTkLabel(card, text=lbl, **LBL).grid(row=r, column=0, sticky="e", **pad)
            widget.grid(row=r, column=1, sticky="ew", **pad)

        # Datum
        self._date_var = ctk.StringVar(value=now_date())
        date_f = ctk.CTkFrame(card, fg_color="transparent")
        date_f.grid_columnconfigure(0, weight=1)
        self._date_ent = ctk.CTkEntry(date_f, textvariable=self._date_var,
                                       font=ctk.CTkFont(size=13),
                                       fg_color=COLORS["bg"])
        self._date_ent.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(date_f, text=L.t("today"), width=70, height=28,
                       fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
                       corner_radius=8, command=lambda: self._date_var.set(now_date())
                       ).grid(row=0, column=1, padx=(6,0))
        row(0, L.t("lbl_date"), date_f)

        # Uhrzeit
        self._time_var = ctk.StringVar(value=now_time())
        time_f = ctk.CTkFrame(card, fg_color="transparent")
        time_f.grid_columnconfigure(0, weight=1)
        self._time_ent = ctk.CTkEntry(time_f, textvariable=self._time_var,
                                       font=ctk.CTkFont(size=13), fg_color=COLORS["bg"])
        self._time_ent.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(time_f, text="Jetzt", width=70, height=28,
                       fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
                       corner_radius=8, command=lambda: self._time_var.set(now_time())
                       ).grid(row=0, column=1, padx=(6,0))
        row(1, L.t("lbl_time"), time_f)

        # Wert + Einheit
        val_f = ctk.CTkFrame(card, fg_color="transparent")
        val_f.grid_columnconfigure(0, weight=1)
        self._val_var = ctk.StringVar()
        self._val_ent = ctk.CTkEntry(val_f, textvariable=self._val_var,
                                      font=ctk.CTkFont(size=20, weight="bold"),
                                      fg_color=COLORS["bg"], height=44)
        self._val_ent.grid(row=0, column=0, sticky="ew")
        self._unit_lbl = ctk.CTkLabel(val_f, text=self._unit(),
                                       font=ctk.CTkFont(size=13),
                                       text_color=COLORS["text_muted"], width=65)
        self._unit_lbl.grid(row=0, column=1, padx=(8,0))
        row(2, L.t("lbl_value"), val_f)
        ctk.CTkLabel(card, text=L.t("unit_hint"),
                      font=ctk.CTkFont(size=9), text_color=COLORS["text_muted"]
                      ).grid(row=3, column=1, sticky="w", padx=18)

        # Typ
        self._typ_var = ctk.StringVar(value="nuchtern")
        typ_f = ctk.CTkFrame(card, fg_color="transparent")
        for i, t in enumerate(MEASUREMENT_TYPES):
            ctk.CTkRadioButton(typ_f, text=type_label(t), variable=self._typ_var, value=t,
                                font=ctk.CTkFont(size=12),
                                fg_color=TYPE_COLORS.get(t, COLORS["primary"]),
                                hover_color=COLORS["primary_dark"]
                                ).pack(side="left", padx=8)
        row(4, L.t("lbl_type"), typ_f)

        # Notiz
        self._note_var = ctk.StringVar()
        note_ent = ctk.CTkEntry(card, textvariable=self._note_var,
                                 placeholder_text=L.t("note_placeholder"),
                                 font=ctk.CTkFont(size=12), fg_color=COLORS["bg"])
        row(5, L.t("lbl_note"), note_ent)

        # Buttons
        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=6, column=0, columnspan=2, pady=(8,14), padx=18, sticky="e")
        ctk.CTkButton(btn_f, text=L.t("btn_cancel"), width=100, height=36,
                       fg_color=COLORS["bg2"], text_color=COLORS["text"],
                       hover_color=COLORS["border"], corner_radius=10,
                       command=self._reset).pack(side="left", padx=(0,8))
        self._save_btn = ctk.CTkButton(btn_f, text=L.t("btn_save"), width=130, height=36,
                                        fg_color=COLORS["primary"],
                                        hover_color=COLORS["primary_dark"],
                                        corner_radius=10, command=self._save)
        self._save_btn.pack(side="left")
        self._status_lbl = ctk.CTkLabel(btn_f, text="",
                                         font=ctk.CTkFont(size=12),
                                         text_color=COLORS["normal"])
        self._status_lbl.pack(side="left", padx=(12,0))

    def _save(self):
        from utils import parse_date
        from database import messung_exists
        raw   = self._val_var.get().strip()
        mmol  = parse_input(raw, self._unit())
        if not mmol:
            self._status_lbl.configure(text=L.t("value_invalid"),
                                        text_color=COLORS["danger"])
            return
        datum = parse_date(self._date_var.get())
        if not datum:
            self._status_lbl.configure(text="Ungültiges Datum", text_color=COLORS["danger"])
            return
        uhrzeit = self._time_var.get()[:5]
        uid = self._s.get("active_user_id", 1)
        # Duplikat-Warnung (kein Hard-Block – zweiter Klick speichert trotzdem)
        if messung_exists(datum, uhrzeit, uid) and not getattr(self, "_dup_ok", False):
            self._status_lbl.configure(
                text="⚠  Bereits ein Eintrag für diesen Zeitpunkt vorhanden. "
                     "Nochmals klicken zum Speichern.",
                text_color=COLORS["warning"])
            self._dup_ok = True
            return
        self._dup_ok = False
        m = Messung(None, datum, uhrzeit, mmol,
                    self._typ_var.get(), self._note_var.get().strip())
        add_messung(m, user_id=uid)
        self._status_lbl.configure(text=L.t("saved"), text_color=COLORS["normal"])
        col = status_color(mmol)
        self._preview_lbl.configure(
            text=f"✓  {wert_display(mmol, self._unit())} {self._unit()}",
            text_color=col
        )
        self._refresh()
        self.after(3000, self._reset)

    def _reset(self):
        self._date_var.set(now_date()); self._time_var.set(now_time())
        self._val_var.set(""); self._note_var.set("")
        self._status_lbl.configure(text="")
        self._preview_lbl.configure(text="")
        self._dup_ok = False

    def on_show(self):
        self._unit_lbl.configure(text=self._unit())
        self._time_var.set(now_time())
