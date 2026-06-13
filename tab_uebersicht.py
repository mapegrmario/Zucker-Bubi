# tab_uebersicht.py – Übersicht mit Bearbeiten, Löschen und Sichern
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import zipfile, shutil, os
from datetime import date, datetime
from config import COLORS, MEASUREMENT_TYPES, TYPE_COLORS, DATA_DIR, DB_PATH, SETTINGS_PATH
from database import get_messungen, delete_messung, update_messung
from models import Messung, parse_input
from utils import format_date_de, type_label, status_color, wert_display, parse_date, now_time
import lang as L

PERIOD_KEYS = ["days_7", "days_14", "days_30", "days_90"]
PERIOD_DAYS = [7, 14, 30, 90]


class TabUebersicht(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._refresh = refresh_cb
        self._days = 30
        self._selected_id = None
        self._build()

    def _unit(self): return self._s.get("unit", "mmol/L")

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Kopfzeile ──────────────────────────────────────────────────────
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 6))
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text=L.t("uebersicht"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text"]).grid(row=0, column=0, sticky="w")

        per_f = ctk.CTkFrame(head, fg_color="transparent")
        per_f.grid(row=0, column=2, sticky="e")
        self._per_btns = {}
        for key, days in zip(PERIOD_KEYS, PERIOD_DAYS):
            btn = ctk.CTkButton(
                per_f, text=L.t(key), width=72, height=30,
                corner_radius=8, font=ctk.CTkFont(size=11),
                fg_color=COLORS["primary"] if days == self._days else COLORS["bg2"],
                text_color="white" if days == self._days else COLORS["text"],
                hover_color=COLORS["primary_dark"],
                command=lambda d=days: self._set_period(d))
            btn.pack(side="left", padx=3)
            self._per_btns[days] = btn

        self._stat_lbl = ctk.CTkLabel(self, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color=COLORS["text_muted"])
        self._stat_lbl.grid(row=1, column=0, sticky="w", padx=26, pady=(0, 4))

        # ── Tabelle ────────────────────────────────────────────────────────
        tbl_card = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                                 border_width=1, border_color=COLORS["border"])
        tbl_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 6))
        tbl_card.grid_columnconfigure(0, weight=1)
        self._build_tree(tbl_card)

        # ── Aktionsleiste ──────────────────────────────────────────────────
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 6))
        self._btn_edit = ctk.CTkButton(
            act, text="✏  Bearbeiten", width=140, height=34,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            corner_radius=8, font=ctk.CTkFont(size=12),
            state="disabled", command=self._open_edit)
        self._btn_edit.pack(side="left", padx=(0, 8))
        self._btn_del = ctk.CTkButton(
            act, text=L.t("btn_delete"), width=120, height=34,
            fg_color=COLORS["danger"], hover_color=COLORS["danger_dark"],
            corner_radius=8, font=ctk.CTkFont(size=12),
            state="disabled", command=self._delete_selected)
        self._btn_del.pack(side="left", padx=(0, 20))
        # Backup-Buttons rechts
        ctk.CTkButton(act, text="💾  Sicherung erstellen", width=170, height=34,
                       fg_color=COLORS["accent"], hover_color=COLORS["accent_dark"],
                       corner_radius=8, font=ctk.CTkFont(size=12),
                       command=self._backup).pack(side="right", padx=(8, 0))
        ctk.CTkButton(act, text="📂  Sicherung laden", width=155, height=34,
                       fg_color=COLORS["bg2"], text_color=COLORS["text"],
                       hover_color=COLORS["border"],
                       corner_radius=8, font=ctk.CTkFont(size=12),
                       command=self._restore).pack(side="right")
        self._act_status = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=11),
                                         text_color=COLORS["normal"])
        self._act_status.grid(row=4, column=0, sticky="w", padx=26, pady=(0, 4))

        # ── Edit-Panel (anfangs versteckt) ─────────────────────────────────
        self._edit_panel = ctk.CTkFrame(
            self, corner_radius=14, fg_color=COLORS["card"],
            border_width=2, border_color=COLORS["primary"])
        self._build_edit_panel(self._edit_panel)
        # Wird erst per _open_edit eingeblendet

        self.refresh()

    # ── Treeview ────────────────────────────────────────────────────────────
    def _build_tree(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("GC.Treeview",
                         background=COLORS["card"], fieldbackground=COLORS["card"],
                         foreground=COLORS["text"], rowheight=32,
                         font=("Segoe UI", 11))
        style.configure("GC.Treeview.Heading",
                         background=COLORS["primary"], foreground="white",
                         font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("GC.Treeview",
                  background=[("selected", COLORS["primary_light"])],
                  foreground=[("selected", COLORS["primary"])])

        cols = ("datum", "uhrzeit", "wert", "typ", "notiz", "quelle")
        self._tree = ttk.Treeview(parent, columns=cols, show="headings",
                                   style="GC.Treeview", selectmode="browse", height=14)
        heads  = [L.t("lbl_date"), L.t("lbl_time"), L.t("lbl_value"),
                  L.t("lbl_type"), L.t("lbl_note"), "Quelle"]
        widths = [110, 80, 120, 130, 220, 90]
        for col, h, w in zip(cols, heads, widths):
            self._tree.heading(col, text=h)
            self._tree.column(col, width=w, anchor="center" if col != "notiz" else "w")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        vsb.grid(row=0, column=1, sticky="ns", pady=8, padx=(0, 4))

        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._tree.bind(ev, lambda e: self._tree.yview_scroll(
                -1 if e.num == 4 else (1 if e.num == 5 else -int(e.delta / 60)), "units"))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda e: self._open_edit())

    # ── Edit-Panel aufbauen ─────────────────────────────────────────────────
    def _build_edit_panel(self, panel):
        panel.grid_columnconfigure(1, weight=1)
        pad = {"padx": 16, "pady": 5}
        LBL = {"font": ctk.CTkFont(size=11, weight="bold"),
               "text_color": COLORS["text_muted"], "anchor": "e"}

        ctk.CTkLabel(panel, text="✏  Eintrag bearbeiten",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=COLORS["primary"]
                      ).grid(row=0, column=0, columnspan=4, sticky="w",
                              padx=16, pady=(12, 4))
        ctk.CTkFrame(panel, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=12, pady=(0, 4))

        # Datum
        ctk.CTkLabel(panel, text=L.t("lbl_date"), **LBL).grid(
            row=2, column=0, sticky="e", **pad)
        self._e_date = ctk.CTkEntry(panel, font=ctk.CTkFont(size=12),
                                     fg_color=COLORS["bg"], width=120)
        self._e_date.grid(row=2, column=1, sticky="w", **pad)

        # Uhrzeit
        ctk.CTkLabel(panel, text=L.t("lbl_time"), **LBL).grid(
            row=2, column=2, sticky="e", **pad)
        self._e_time = ctk.CTkEntry(panel, font=ctk.CTkFont(size=12),
                                     fg_color=COLORS["bg"], width=90)
        self._e_time.grid(row=2, column=3, sticky="w", **pad)

        # Wert
        ctk.CTkLabel(panel, text=L.t("lbl_value"), **LBL).grid(
            row=3, column=0, sticky="e", **pad)
        val_f = ctk.CTkFrame(panel, fg_color="transparent")
        val_f.grid(row=3, column=1, sticky="w", **pad)
        self._e_val = ctk.CTkEntry(val_f, font=ctk.CTkFont(size=14, weight="bold"),
                                    fg_color=COLORS["bg"], width=110, height=36)
        self._e_val.pack(side="left")
        self._e_unit_lbl = ctk.CTkLabel(val_f, text=self._unit(),
                                          font=ctk.CTkFont(size=11),
                                          text_color=COLORS["text_muted"])
        self._e_unit_lbl.pack(side="left", padx=(6, 0))

        # Typ
        ctk.CTkLabel(panel, text=L.t("lbl_type"), **LBL).grid(
            row=3, column=2, sticky="e", **pad)
        self._e_typ = ctk.CTkOptionMenu(
            panel, values=[type_label(t) for t in MEASUREMENT_TYPES],
            font=ctk.CTkFont(size=11), width=150,
            fg_color=COLORS["bg"], text_color=COLORS["text"],
            button_color=COLORS["border"], button_hover_color=COLORS["primary_light"])
        self._e_typ.grid(row=3, column=3, sticky="w", **pad)

        # Notiz
        ctk.CTkLabel(panel, text=L.t("lbl_note"), **LBL).grid(
            row=4, column=0, sticky="e", **pad)
        self._e_note = ctk.CTkEntry(panel, font=ctk.CTkFont(size=12),
                                     fg_color=COLORS["bg"], placeholder_text="…")
        self._e_note.grid(row=4, column=1, columnspan=3, sticky="ew",
                           padx=(0, 16), pady=5)

        # Buttons
        btn_r = ctk.CTkFrame(panel, fg_color="transparent")
        btn_r.grid(row=5, column=0, columnspan=4, sticky="e", padx=16, pady=(4, 14))
        ctk.CTkButton(btn_r, text=L.t("btn_cancel"), width=100, height=32,
                       fg_color=COLORS["bg2"], text_color=COLORS["text"],
                       hover_color=COLORS["border"], corner_radius=8,
                       command=self._close_edit).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_r, text=L.t("btn_save"), width=120, height=32,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                       corner_radius=8, command=self._save_edit).pack(side="left")
        self._edit_status = ctk.CTkLabel(btn_r, text="",
                                          font=ctk.CTkFont(size=11),
                                          text_color=COLORS["normal"])
        self._edit_status.pack(side="left", padx=(10, 0))

    # ── Logik ───────────────────────────────────────────────────────────────
    def _set_period(self, days: int):
        self._days = days
        for d, btn in self._per_btns.items():
            btn.configure(fg_color=COLORS["primary"] if d == days else COLORS["bg2"],
                          text_color="white" if d == days else COLORS["text"])
        self.refresh()

    def refresh(self):
        self._selected_id = None
        self._btn_edit.configure(state="disabled")
        self._btn_del.configure(state="disabled")
        self._messungen = get_messungen(self._days, user_id=self._s.get("active_user_id",1))
        unit = self._unit()
        low  = self._s.get("target_low", 3.9)
        high = self._s.get("target_high", 7.8)
        self._tree.delete(*self._tree.get_children())
        for m in self._messungen:
            val = f"{wert_display(m.wert_mmol, unit)}  {unit}"
            tag = m.get_status(low, high)
            self._tree.insert("", "end", iid=str(m.id),
                               values=(format_date_de(m.datum), m.uhrzeit, val,
                                       type_label(m.typ), m.notiz, m.quelle),
                               tags=(tag,))
        self._tree.tag_configure("normal",    background="#F0FFF4")
        self._tree.tag_configure("low",       background="#FAF5FF")
        self._tree.tag_configure("very_low",  background="#FFF0F5")
        self._tree.tag_configure("high",      background="#FFFAF0")
        self._tree.tag_configure("very_high", background="#FFF5F5")
        self._stat_lbl.configure(text=f"{len(self._messungen)} Messungen  ·  {self._days} Tage")

    def _on_select(self, _=None):
        sel = self._tree.selection()
        if sel:
            self._selected_id = int(sel[0])
            self._btn_edit.configure(state="normal")
            self._btn_del.configure(state="normal")
        else:
            self._selected_id = None
            self._btn_edit.configure(state="disabled")
            self._btn_del.configure(state="disabled")

    def _get_selected_messung(self):
        if not self._selected_id:
            return None
        return next((m for m in self._messungen if m.id == self._selected_id), None)

    # ── Bearbeiten ──────────────────────────────────────────────────────────
    def _open_edit(self):
        m = self._get_selected_messung()
        if not m:
            return
        # Felder befüllen
        self._e_date.delete(0, "end"); self._e_date.insert(0, format_date_de(m.datum))
        self._e_time.delete(0, "end"); self._e_time.insert(0, m.uhrzeit)
        self._e_val.delete(0, "end")
        self._e_val.insert(0, wert_display(m.wert_mmol, self._unit()))
        self._e_unit_lbl.configure(text=self._unit())
        self._e_typ.set(type_label(m.typ))
        self._e_note.delete(0, "end"); self._e_note.insert(0, m.notiz)
        self._edit_status.configure(text="")
        self._edit_panel.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 14))
        self._edit_panel.lift()

    def _close_edit(self):
        self._edit_panel.grid_remove()
        self._edit_status.configure(text="")

    def _save_edit(self):
        m = self._get_selected_messung()
        if not m:
            return
        raw  = self._e_val.get().strip()
        mmol = parse_input(raw, self._unit())
        if not mmol:
            self._edit_status.configure(text=L.t("value_invalid"), text_color=COLORS["danger"])
            return
        datum = parse_date(self._e_date.get())
        if not datum:
            self._edit_status.configure(text="Ungültiges Datum", text_color=COLORS["danger"])
            return
        # Typ-Label → Key
        typ_labels = [type_label(t) for t in MEASUREMENT_TYPES]
        sel_lbl = self._e_typ.get()
        typ_key = MEASUREMENT_TYPES[typ_labels.index(sel_lbl)] if sel_lbl in typ_labels else "sonstige"

        updated = Messung(m.id, datum, self._e_time.get(), mmol, typ_key,
                          self._e_note.get().strip(), m.quelle)
        update_messung(updated)
        self._edit_status.configure(text=L.t("saved"), text_color=COLORS["normal"])
        self.refresh()
        self._refresh()
        self.after(1500, self._close_edit)

    # ── Löschen ─────────────────────────────────────────────────────────────
    def _delete_selected(self):
        m = self._get_selected_messung()
        if not m:
            return
        val_str = wert_display(m.wert_mmol, self._unit())
        if messagebox.askyesno(
                L.t("btn_delete"),
                f"{L.t('del_confirm')}\n\n"
                f"{format_date_de(m.datum)}  {m.uhrzeit}  –  {val_str} {self._unit()}"):
            self._close_edit()
            delete_messung(m.id)
            self.refresh()
            self._refresh()
            self._set_status(f"🗑  Eintrag gelöscht", COLORS["danger"])

    # ── Backup ──────────────────────────────────────────────────────────────
    def _backup(self):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP-Archiv", "*.zip")],
            initialfile=f"ZuckerBubi_Sicherung_{ts}.zip")
        if not path:
            return
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                if DB_PATH.exists():
                    zf.write(DB_PATH, "data/gluko.db")
                if SETTINGS_PATH.exists():
                    zf.write(SETTINGS_PATH, "data/settings.json")
            self._set_status(
                f"✓  Sicherung gespeichert: {os.path.basename(path)}", COLORS["normal"])
        except Exception as e:
            self._set_status(f"❌  {e}", COLORS["danger"])

    def _restore(self):
        path = filedialog.askopenfilename(
            filetypes=[("ZIP-Archiv", "*.zip")],
            title="Sicherung laden")
        if not path:
            return
        if not messagebox.askyesno(
                "Sicherung laden",
                "Alle aktuellen Daten werden durch die Sicherung ersetzt.\nFortfahren?"):
            return
        try:
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                if "data/gluko.db" not in names:
                    self._set_status("❌  Keine gültige Sicherungsdatei", COLORS["danger"])
                    return
                zf.extractall(str(DATA_DIR.parent))
            self._set_status("✓  Sicherung geladen – Daten wurden wiederhergestellt",
                              COLORS["normal"])
            self.refresh()
            self._refresh()
        except Exception as e:
            self._set_status(f"❌  {e}", COLORS["danger"])

    def _set_status(self, msg: str, color: str):
        self._act_status.configure(text=msg, text_color=color)
        self.after(5000, lambda: self._act_status.configure(text=""))

    def on_show(self):
        self.refresh()
