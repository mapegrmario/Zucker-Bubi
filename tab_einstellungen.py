# tab_einstellungen.py – Einstellungen mit integrierter Benutzerverwaltung
import customtkinter as ctk
from config import COLORS, save_settings
from user_manager import UserManagerPanel
import lang as L


class TabEinstellungen(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._refresh = refresh_cb
        self._vars = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=L.t("einstellungen"),
                      font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 10))

        # Benutzerverwaltung
        self._user_panel = UserManagerPanel(
            self, self._s, on_user_change=self._on_user_change)
        self._user_panel.grid(row=1, column=0, sticky="ew", padx=24, pady=6)

        # Einheit & Zielbereich
        self._build_section(2, f"📐  {L.t('unit_lbl')} & {L.t('target_range')}", [
            ("unit",   L.t("unit_lbl"), "unit"),
        ])

        # Sprache
        self._build_section(3, f"🌐  {L.t('language')}", [
            ("language", L.t("language"), "lang"),
        ])

        # Speichern
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.grid(row=4, column=0, sticky="e", padx=24, pady=(8, 24))
        ctk.CTkButton(btn_f, text=L.t("btn_save"), width=150, height=38,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                       corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._save).pack(side="left", padx=(0, 10))
        self._status = ctk.CTkLabel(btn_f, text="", font=ctk.CTkFont(size=11),
                                     text_color=COLORS["normal"])
        self._status.pack(side="left")

    def _build_section(self, row: int, title: str, fields: list):
        card = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=0, sticky="ew", padx=24, pady=6)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=title,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=COLORS["primary"]
                      ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 4))
        ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 4))
        LBL = {"font": ctk.CTkFont(size=12), "text_color": COLORS["text_muted"], "anchor": "e"}
        for i, (key, lbl, wtype) in enumerate(fields):
            ctk.CTkLabel(card, text=lbl, **LBL).grid(
                row=i+2, column=0, sticky="e", padx=(16, 8), pady=8)
            if wtype == "unit":
                var = ctk.StringVar(value=self._s.get(key, "mmol/L"))
                w = ctk.CTkSegmentedButton(card, values=["mmol/L", "mg/dL"],
                                            variable=var, font=ctk.CTkFont(size=12),
                                            selected_color=COLORS["primary"],
                                            selected_hover_color=COLORS["primary_dark"])
            elif wtype == "lang":
                var = ctk.StringVar(
                    value="Deutsch" if self._s.get(key, "de") == "de" else "English")
                w = ctk.CTkSegmentedButton(card, values=["Deutsch", "English"],
                                            variable=var, font=ctk.CTkFont(size=12),
                                            selected_color=COLORS["primary"],
                                            selected_hover_color=COLORS["primary_dark"])
            else:
                var = ctk.StringVar(value=str(self._s.get(key, "")))
                w = ctk.CTkEntry(card, textvariable=var, font=ctk.CTkFont(size=12),
                                  fg_color=COLORS["bg"], height=34, corner_radius=8)
            w.grid(row=i+2, column=1, sticky="w", padx=(0, 16), pady=8)
            self._vars[key] = (var, wtype)

    def _save(self):
        for key, (var, wtype) in self._vars.items():
            val = var.get().strip()
            if wtype == "lang":
                self._s[key] = "de" if val == "Deutsch" else "en"
                L.set_lang(self._s[key])
            else:
                self._s[key] = val
        save_settings(self._s)
        self._status.configure(text=L.t("saved"), text_color=COLORS["normal"])
        self._refresh()
        self.after(3000, lambda: self._status.configure(text=""))

    def _on_user_change(self, uid: int):
        self._s["active_user_id"] = uid
        self._refresh()

    def refresh_users(self):
        if hasattr(self, "_user_panel"):
            self._user_panel.refresh()

    def on_show(self):
        pass
