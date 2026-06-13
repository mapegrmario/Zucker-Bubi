# 🩸 Zucker Bubi

**Blutzucker-Dokumentation & Auswertung für Linux**

> Autor: Mario Peeß / Großenhain · mapegr@mailbox.org  
> Lizenz: GNU General Public License v3 (GPLv3)  
> Version: 1.0.0

---

## Übersicht

Zucker Bubi ist ein persönliches Blutzucker-Dokumentationsprogramm für Linux.  
Es ermöglicht die manuelle Eingabe und Bluetooth-Synchronisation von Blutzuckerwerten,
zeigt statistische Auswertungen und erstellt professionelle PDF-Berichte für den Arzt.

---

## Installation

```bash
chmod +x install.sh
./install.sh
```

Das Script erkennt automatisch Ubuntu, Linux Mint, LMDE, Fedora, openSUSE und Arch Linux.

### Manuelle Installation

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

### Systemvoraussetzungen

- Python 3.10+
- Tkinter (`python3-tk`)
- Bluetooth (für Gerätesync): `bluez`, `libbluetooth-dev`

---

## Erste Schritte

1. **Programm starten** → `./start.sh` oder Menü → "Zucker Bubi"
2. **Einstellungen** öffnen → Patientendaten und Arztinformation eintragen
3. **Einheit wählen**: mmol/L oder mg/dL
4. **Erste Messung eingeben**: Tab "Eingabe" → Wert eingeben → Speichern
5. **Dashboard** zeigt sofort die aktuellen Statistiken

---

## Bluetooth-Synchronisation

### Voraussetzungen
- Gerät muss über **Systemeinstellungen → Bluetooth** gekoppelt sein
- Bluetooth am Computer aktiviert

### Ablauf
1. Messgerät einschalten und in Reichweite halten
2. In Zucker Bubi: Oben auf **"Gerät synchronisieren"** klicken
3. Automatische Suche startet (bis zu 10 Sekunden)
4. Gefundene Werte werden automatisch gespeichert

### Kompatible Geräte
| Gerät | Verbindung | Status |
|---|---|---|
| Accu-Chek Guide | Bluetooth LE | ✓ |
| Accu-Chek Active | Bluetooth LE | ✓ |
| Contour Next One | Bluetooth LE | ✓ |
| OneTouch Verio | Bluetooth LE | ✓ |
| FreeStyle Libre 2 | NFC (nicht BLE) | ✗ |

---

## Einheiten

| Einheit | Beispielwert | Umrechnung |
|---|---|---|
| mmol/L | 5,5 | Standard Europa |
| mg/dL | 99 | Standard USA |

`1 mmol/L ≈ 18 mg/dL`

---

## Arztbericht (PDF)

Der Bericht enthält:
- Patientendaten und Arztinformation
- Statistik: Anzahl, Durchschnitt, Min, Max, Standardabweichung
- Geschätzter HbA1c (Nathan-Formel)
- Zeit im Zielbereich (TIR)
- Verlaufsgrafik
- Vollständige Messwert-Tabelle (farbkodiert)

**Erstellen:** Tab "Arztbericht" → Zeitraum wählen → "PDF erstellen"

---

## Farbkodierung

| Farbe | Bedeutung | mmol/L | mg/dL |
|---|---|---|---|
| 🟢 Grün | Normal / Zielbereich | 3,9–7,8 | 70–140 |
| 🟡 Orange | Erhöht | 7,8–10,0 | 140–180 |
| 🔴 Rot | Sehr hoch | > 10,0 | > 180 |
| 🟣 Lila | Niedrig | 3,0–3,9 | 54–70 |
| 🩷 Pink | Sehr niedrig | < 3,0 | < 54 |

---

## Datenschutz

Alle Daten werden **ausschließlich lokal** gespeichert.  
Kein Internet-Zugriff, keine Cloud, keine Übertragung an Dritte.

Datenbankdatei: `data/gluko.db` (SQLite)

---

## Haftungsausschluss

Dieses Programm dient **nur zur persönlichen Dokumentation** und ersetzt keine  
ärztliche Beratung, Diagnose oder Behandlung. Alle Angaben ohne Gewähr.  
Medizinische Entscheidungen treffen Sie bitte gemeinsam mit Ihrem Arzt.

---

## Drittanbieter

- **customtkinter** – Tom Schimansky (MIT)
- **matplotlib** – Matplotlib Development Team (PSF/BSD)
- **reportlab** – ReportLab Inc. (BSD)
- **bleak** – Henrik Blidh (MIT)
- **Pillow** – Jeffrey A. Clark (HPND)

---

© 2024 Mario Peeß / Großenhain · mapegr@mailbox.org · Zucker Bubi v1.0.0
