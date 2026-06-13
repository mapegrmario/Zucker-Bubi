# tab_hilfe.py – Hilfe-Sektion
import customtkinter as ctk
from config import COLORS
import lang as L

HELP_SECTIONS_DE = [
    ("🏠 Dashboard",
     "Das Dashboard zeigt Ihnen auf einen Blick alle wichtigen Kennzahlen:\n"
     "• Letzter gemessener Wert mit Farbkodierung\n"
     "• Tagesdurchschnitt und Wochendurchschnitt\n"
     "• Geschätzter HbA1c-Wert (Nathan-Formel)\n"
     "• Verlaufsgrafik der letzten 7 Tage\n"
     "• Heutige Messungen als farbige Karten"),

    ("✚ Eingabe",
     "Geben Sie Blutzuckerwerte manuell ein:\n"
     "• Datum und Uhrzeit wählen (oder 'Heute/Jetzt' nutzen)\n"
     "• Wert in mmol/L oder mg/dL eingeben (Einheit in Einstellungen)\n"
     "• Messtyp auswählen: Nüchtern, Vor/Nach dem Essen, Sonstige\n"
     "• Optionale Notiz hinzufügen\n"
     "Tipp: 1 mmol/L ≈ 18 mg/dL"),

    ("📋 Übersicht",
     "Alle gespeicherten Messungen im Überblick:\n"
     "• Zeitraum filtern: 7 / 14 / 30 / 90 Tage\n"
     "• Farbkodierung: Grün = Normal, Orange = Erhöht, Rot = Sehr hoch/niedrig\n"
     "• Messung auswählen und mit 'Löschen' entfernen\n"
     "• Tabelle mit Mausrad oder Scrollleiste scrollen"),

    ("📄 Arztbericht",
     "Professionellen PDF-Bericht für Ihren Arzt erstellen:\n"
     "• Zeitraum wählen (7–90 Tage)\n"
     "• Vorschau der Statistiken prüfen\n"
     "• 'PDF erstellen' klicken und Speicherort wählen\n"
     "Der Bericht enthält: Patientendaten, Statistik, Verlaufsgrafik, Messtabelle"),

    ("🔷 Bluetooth-Synchronisation",
     "Kompatible Geräte: Accu-Chek Guide, Contour Next, OneTouch u.v.m.\n\n"
     "Voraussetzungen:\n"
     "1. Gerät muss vorher über Systemeinstellungen → Bluetooth gekoppelt sein\n"
     "2. Bluetooth am Computer muss aktiviert sein\n"
     "3. Gerät in Reichweite halten\n\n"
     "Dann: Oben auf 'Gerät synchronisieren' klicken → automatische Suche startet.\n"
     "Bei Problemen: Gerät neu koppeln oder Werte manuell eingeben."),

    ("📐 Zielwerte",
     "Standard-Referenzwerte (Deutsche Diabetes Gesellschaft):\n"
     "• Nüchternwert: 3,9 – 7,0 mmol/L (70–126 mg/dL)\n"
     "• Nach dem Essen: < 7,8 mmol/L (< 140 mg/dL)\n"
     "• Hypoglykämie: < 3,9 mmol/L (< 70 mg/dL)\n"
     "• HbA1c Zielwert: < 7,0 % (individuell nach Arztempfehlung)\n\n"
     "Individuelle Zielwerte können in den Einstellungen angepasst werden."),
]

HELP_SECTIONS_EN = [
    ("🏠 Dashboard",
     "The dashboard shows all key metrics at a glance:\n"
     "• Last measured value with color coding\n"
     "• Daily and weekly averages\n"
     "• Estimated HbA1c (Nathan formula)\n"
     "• 7-day trend chart\n"
     "• Today's readings as color-coded cards"),

    ("✚ Entry",
     "Enter blood glucose values manually:\n"
     "• Choose date and time (or use 'Today/Now')\n"
     "• Enter value in mmol/L or mg/dL (set unit in Settings)\n"
     "• Select type: Fasting, Before/After Meal, Other\n"
     "• Add optional note\n"
     "Tip: 1 mmol/L ≈ 18 mg/dL"),

    ("📋 Overview",
     "All saved measurements at a glance:\n"
     "• Filter by period: 7 / 14 / 30 / 90 days\n"
     "• Color coding: Green = Normal, Orange = Elevated, Red = Very high/low\n"
     "• Select a row and delete it\n"
     "• Scroll with mouse wheel or scrollbar"),

    ("📄 Doctor Report",
     "Create a professional PDF report for your doctor:\n"
     "• Choose period (7–90 days)\n"
     "• Check statistics preview\n"
     "• Click 'Create PDF' and choose save location\n"
     "Report includes: patient data, statistics, trend chart, readings table"),

    ("🔷 Bluetooth Sync",
     "Compatible devices: Accu-Chek Guide, Contour Next, OneTouch and more.\n\n"
     "Requirements:\n"
     "1. Device must be paired via System Settings → Bluetooth first\n"
     "2. Bluetooth must be enabled on your computer\n"
     "3. Keep device nearby\n\n"
     "Then: Click 'Sync Device' at the top → automatic search starts.\n"
     "If issues arise: re-pair the device or enter values manually."),

    ("📐 Target Values",
     "Standard reference values (DDG guidelines):\n"
     "• Fasting: 3.9 – 7.0 mmol/L (70–126 mg/dL)\n"
     "• After meals: < 7.8 mmol/L (< 140 mg/dL)\n"
     "• Hypoglycemia: < 3.9 mmol/L (< 70 mg/dL)\n"
     "• HbA1c target: < 7.0 % (individual per doctor)\n\n"
     "Custom target values can be set in Settings."),
]


class TabHilfe(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=L.t("hilfe"),
                      font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, sticky="w", padx=24, pady=(20,4))

        intro = ctk.CTkLabel(self, text=L.t("help_intro"),
                              font=ctk.CTkFont(size=12),
                              text_color=COLORS["text_muted"],
                              justify="left", wraplength=700)
        intro.grid(row=1, column=0, sticky="w", padx=24, pady=(0,12))

        sections = HELP_SECTIONS_EN if L.get_lang() == "en" else HELP_SECTIONS_DE
        for i, (title, body) in enumerate(sections):
            card = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                                 border_width=1, border_color=COLORS["border"])
            card.grid(row=i+2, column=0, sticky="ew", padx=24, pady=5)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=title,
                          font=ctk.CTkFont(size=13, weight="bold"),
                          text_color=COLORS["primary"],
                          anchor="w"
                          ).grid(row=0, column=0, sticky="w", padx=16, pady=(12,4))
            ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).grid(
                row=1, column=0, sticky="ew", padx=12)
            ctk.CTkLabel(card, text=body,
                          font=ctk.CTkFont(size=11), justify="left",
                          text_color=COLORS["text"], wraplength=700, anchor="w"
                          ).grid(row=2, column=0, sticky="w", padx=16, pady=(6,14))

    def on_show(self): pass
