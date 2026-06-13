# tab_ueber.py – Über dieses Programm (mit Zucker Bubi Avatar)
import customtkinter as ctk
from PIL import Image as PILImage
from config import COLORS, APP_NAME, APP_VERSION, AUTHOR, EMAIL, AVATAR_PATH
import lang as L


class TabUeber(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # Avatar + App-Name zentriert
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, pady=(28,8))
        center.grid_columnconfigure(0, weight=1)

        if AVATAR_PATH.exists():
            try:
                img = ctk.CTkImage(PILImage.open(AVATAR_PATH), size=(160, 160))
                ctk.CTkLabel(center, image=img, text="").grid(row=0, column=0, pady=(0,10))
            except Exception:
                pass

        ctk.CTkLabel(center,
                      text=APP_NAME,
                      font=ctk.CTkFont(size=26, weight="bold"),
                      text_color=COLORS["primary"]
                      ).grid(row=1, column=0)
        ctk.CTkLabel(center,
                      text=f"Version {APP_VERSION}",
                      font=ctk.CTkFont(size=12),
                      text_color=COLORS["text_muted"]
                      ).grid(row=2, column=0, pady=(2,0))

        ctk.CTkLabel(center,
                      text="Blutzucker-Dokumentation & Auswertung",
                      font=ctk.CTkFont(size=13),
                      text_color=COLORS["text_muted"]
                      ).grid(row=3, column=0, pady=(4,0))

        # Trennlinie
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, sticky="ew", padx=40, pady=12)

        # Info-Karten
        info_blocks = [
            ("👤 Autor", [
                ("Name",    AUTHOR),
                ("E-Mail",  EMAIL),
                ("Lizenz",  "GNU General Public License v3 (GPLv3)"),
            ]),
            ("⚠  Haftungsausschluss", [
                ("", L.t("disclaimer") + "\n\n"
                    "Dieses Programm ist kein Medizinprodukt und ersetzt keine ärztliche Behandlung.\n"
                    "Alle Angaben ohne Gewähr. Der Autor übernimmt keine Haftung für "
                    "Entscheidungen, die auf Basis der angezeigten Daten getroffen werden."),
            ]),
            ("📦 Drittanbieter-Software", [
                ("", L.t("third_party") + "\n\n"
                    "• customtkinter  –  Tom Schimansky (MIT)\n"
                    "• matplotlib     –  Matplotlib Development Team (PSF/BSD)\n"
                    "• reportlab      –  ReportLab Inc. (BSD)\n"
                    "• bleak          –  Henrik Blidh (MIT)\n"
                    "• Pillow         –  Jeffrey A. Clark (HPND)"),
            ]),
        ]

        for i, (title, rows) in enumerate(info_blocks):
            card = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                                 border_width=1, border_color=COLORS["border"])
            card.grid(row=i+2, column=0, sticky="ew", padx=40, pady=6)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text=title,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          text_color=COLORS["primary"]
                          ).grid(row=0, column=0, columnspan=2, sticky="w",
                                 padx=16, pady=(12,4))
            ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).grid(
                row=1, column=0, columnspan=2, sticky="ew", padx=12)

            for j, (lbl, val) in enumerate(rows):
                if lbl:
                    ctk.CTkLabel(card, text=lbl + ":",
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color=COLORS["text_muted"], anchor="e"
                                  ).grid(row=j+2, column=0, sticky="ne",
                                         padx=(16,8), pady=(5,5))
                ctk.CTkLabel(card, text=val,
                              font=ctk.CTkFont(size=11),
                              text_color=COLORS["text"],
                              justify="left", wraplength=480, anchor="w"
                              ).grid(row=j+2, column=1, sticky="w",
                                     padx=(0,16), pady=(5,5))

            ctk.CTkFrame(card, height=8, fg_color="transparent").grid(
                row=99, column=0, columnspan=2)

        # Fußzeile
        ctk.CTkLabel(self,
                      text=f"© 2024 {AUTHOR}  ·  {EMAIL}",
                      font=ctk.CTkFont(size=10),
                      text_color=COLORS["text_muted"]
                      ).grid(row=99, column=0, pady=(16,20))

    def on_show(self): pass
