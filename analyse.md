# Zucker Bubi – Technische Analyse & Architektur

**Version:** 1.0.0  
**Autor:** Mario Peeß / Großenhain  
**Lizenz:** GPLv3  

---

## 1. Programmarchitektur

### Modulübersicht

| Datei | Funktion | Zeilen (ca.) |
|---|---|---|
| `main.py` | Einstiegspunkt, Init | 30 |
| `config.py` | Konstanten, Farben, Pfade, Settings-I/O | 75 |
| `lang.py` | DE/EN Übersetzungs-Dictionary + Accessor | 95 |
| `models.py` | Datenklassen (Messung, Statistik, parse_input) | 65 |
| `database.py` | SQLite CRUD + Statistik-Berechnung | 90 |
| `utils.py` | Statusfarben, Formatierung, Hilfsfunktionen | 65 |
| `bluetooth_manager.py` | BLE-Scan + IEEE-11073 SFLOAT-Parser | 90 |
| `chart_utils.py` | Matplotlib: Dashboard-Chart + PDF-Chart | 95 |
| `pdf_generator.py` | ReportLab: PDF-Dokument aufbauen | 85 |
| `pdf_content.py` | ReportLab: Tabellen, TIR-Balken | 90 |
| `app.py` | CTk-Hauptfenster, Tab-Routing | 85 |
| `sidebar.py` | Linke Navigationsleiste | 80 |
| `topbar.py` | Obere Leiste (BT-Button, Sprache) | 80 |
| `dashboard_cards.py` | Runde Canvas-Statistik-Karten | 95 |
| `tab_dashboard.py` | Dashboard-Tab | 90 |
| `tab_eingabe.py` | Manuelle Eingabe | 95 |
| `tab_uebersicht.py` | Messwert-Tabelle mit ttk.Treeview | 95 |
| `tab_bericht.py` | Arztbericht-UI + PDF-Export | 90 |
| `tab_einstellungen.py` | Einstellungen (Patient, Arzt, Einheit) | 90 |
| `tab_hilfe.py` | Hilfe-Texte DE/EN | 85 |
| `tab_ueber.py` | Über-Seite mit Avatar | 80 |

**Gesamt:** ~21 Python-Dateien, ~1.750 Zeilen Code

---

## 2. Datenbankschema

```sql
CREATE TABLE messungen (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    datum     TEXT    NOT NULL,   -- YYYY-MM-DD
    uhrzeit   TEXT    NOT NULL,   -- HH:MM
    wert_mmol REAL    NOT NULL,   -- intern immer mmol/L
    typ       TEXT    DEFAULT 'sonstige',
    notiz     TEXT    DEFAULT '',
    quelle    TEXT    DEFAULT 'manuell'   -- manuell | bluetooth
);
```

**Datei:** `data/gluko.db` (SQLite 3)

---

## 3. Einheitenkonvertierung

Alle Werte werden intern in **mmol/L** gespeichert.

```
mg/dL → mmol/L:  wert / 18.0
mmol/L → mg/dL:  round(wert * 18)
```

Referenzwerte (DDG-Leitlinien):

| Status | mmol/L | mg/dL |
|---|---|---|
| Sehr niedrig | < 3,0 | < 54 |
| Niedrig | 3,0–3,9 | 54–70 |
| Normal (Nüchtern) | 3,9–5,5 | 70–100 |
| Zielbereich | 3,9–7,8 | 70–140 |
| Erhöht | 7,8–10,0 | 140–180 |
| Sehr hoch | > 10,0 | > 180 |

---

## 4. HbA1c-Schätzung (Nathan-Formel)

```
eAG (mg/dL) = 28,7 × HbA1c − 46,7
→ HbA1c (%) = (Durchschnitt_mg/dL + 46,7) / 28,7
```

**Hinweis:** Dies ist eine Schätzung auf Basis der gespeicherten Einzelmessungen.
Ein klinischer HbA1c aus Blutentnahme ist genauer.

---

## 5. Bluetooth (BLE) – Technische Details

**Protokoll:** Bluetooth Blood Glucose Profile (BGP, Bluetooth SIG)

| UUID | Funktion |
|---|---|
| `0x1808` | Blood Glucose Service |
| `0x2A18` | Blood Glucose Measurement (Notify) |
| `0x2A52` | Record Access Control Point (RACP) |

**RACP-Kommando für alle Records:** `0x01 0x01`

**IEEE-11073 SFLOAT-Parser:**
- Byte 0: Flags (Bit 2: Einheit – 0=kg/L, 1=mol/L)
- Bytes 1-2: Mantisse (12 Bit) + Exponent (4 Bit)
- Konvertierung: `value = mantissa * 10^exponent`

**Kompatible Geräte (getestet/dokumentiert):**
- Accu-Chek Guide (Roche) ✓ BLE
- Contour Next One (Ascensia) ✓ BLE
- OneTouch Verio Reflect ✓ BLE
- FreeStyle Libre 2 (Abbott) – erfordert NFC, kein BGP

---

## 6. PDF-Bericht – Inhalt

1. Header: Zucker-Bubi-Avatar + Patientenname + Datum
2. Arztinformation
3. Statistik-Tabelle: n, Ø, Min, Max, Stabw
4. TIR-Balken: Zeit im Zielbereich (%)
5. Verlaufsgrafik (matplotlib → PNG → eingebettet)
6. Messwert-Tabelle (max. 60 Zeilen, farbkodiert)
7. Footer: Erstellt mit Zucker Bubi · Autor: Mario Peeß · Disclaimer

---

## 7. Farbschema

| Farbe | Hex | Verwendung |
|---|---|---|
| Primary | `#2E86AB` | Buttons, Akzente, Sidebar-Aktiv |
| Accent | `#57CC99` | Normal/OK-Zustand |
| Warning | `#F6AD55` | Erhöhte Werte |
| Danger | `#FC8181` | Sehr hohe/niedrige Werte |
| Sidebar | `#1E2A3A` | Navigationsleiste |
| Background | `#EFF3F8` | App-Hintergrund |
| Card | `#FFFFFF` | Karten-Hintergrund |

---

## 8. Bekannte Einschränkungen

- Bluetooth BLE erfordert systemseitiges Pairing vor der Synchronisation
- FreeStyle Libre nutzt NFC statt BLE → nicht unterstützt
- HbA1c ist Schätzwert, kein klinischer Laborwert
- PDF-Export max. 60 Messzeilen (Seitenformat A4)
- Sprachänderung gilt erst nach Neustart vollständig (Tabs nicht live-reload)

---

## 9. Dateisystem-Layout

```
ZuckerBubi/
├── main.py
├── app.py
├── config.py
├── lang.py
├── models.py
├── database.py
├── utils.py
├── bluetooth_manager.py
├── chart_utils.py
├── pdf_generator.py
├── pdf_content.py
├── sidebar.py
├── topbar.py
├── dashboard_cards.py
├── tab_dashboard.py
├── tab_eingabe.py
├── tab_uebersicht.py
├── tab_bericht.py
├── tab_einstellungen.py
├── tab_hilfe.py
├── tab_ueber.py
├── Zucker_Bubi.png
├── fehler.log          ← automatisch erstellt
├── requirements.txt
├── install.sh
├── analyse.md
├── readme.md
└── data/
    ├── gluko.db        ← SQLite Datenbank
    └── settings.json   ← Einstellungen
```
