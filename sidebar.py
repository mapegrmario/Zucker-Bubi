# sidebar.py – Linke Navigationsleiste
import customtkinter as ctk
from PIL import Image as PILImage
from config import COLORS, AVATAR_PATH, APP_NAME
import lang as L

NAV_ITEMS = [
    ("dashboard",   "🏠", "dashboard"),
    ("eingabe",     "✚",  "eingabe"),
    ("uebersicht",  "📋", "uebersicht"),
    ("bericht",     "📄", "bericht"),
    ("verbindung",  "🔌", "verbindung"),
    ("einstellungen","⚙", "einstellungen"),
    ("hilfe",       "❓", "hilfe"),
    ("ueber",       "ℹ",  "ueber"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_tab_change):
        super().__init__(parent,
                         width=200, corner_radius=0,
                         fg_color=COLORS["sidebar"])
        self.grid_propagate(False)
        self._cb  = on_tab_change
        self._btns = {}
        self._active = None
        self._build()

    def _build(self):
        self.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)

        # Logo / Avatar
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(18, 10), padx=12, sticky="ew")

        if AVATAR_PATH.exists():
            try:
                img = ctk.CTkImage(PILImage.open(AVATAR_PATH), size=(48, 48))
                ctk.CTkLabel(logo_frame, image=img, text="").pack(side="left", padx=(4,8))
            except Exception:
                pass

        ctk.CTkLabel(
            logo_frame, text=APP_NAME, font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF", wraplength=120, justify="left"
        ).pack(side="left", fill="x")

        # Trennlinie
        ctk.CTkFrame(self, height=1, fg_color=COLORS["sidebar_hover"]).grid(
            row=1, column=0, sticky="ew", padx=12, pady=(0,6))

        # Nav-Buttons
        for idx, (key, icon, tab) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {L.t(key)}",
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLORS["sidebar_hover"],
                text_color="#D0DCE8",
                corner_radius=8,
                height=40,
                command=lambda t=tab: self._cb(t)
            )
            btn.grid(row=idx + 2, column=0, padx=10, pady=2, sticky="ew")
            self._btns[tab] = btn

    def set_active(self, tab: str):
        if self._active and self._active in self._btns:
            self._btns[self._active].configure(
                fg_color="transparent", text_color="#D0DCE8")
        if tab in self._btns:
            self._btns[tab].configure(
                fg_color=COLORS["sidebar_active"], text_color="#FFFFFF")
        self._active = tab

    def update_texts(self):
        for idx, (key, icon, tab) in enumerate(NAV_ITEMS):
            if tab in self._btns:
                self._btns[tab].configure(text=f"  {icon}  {L.t(key)}")
