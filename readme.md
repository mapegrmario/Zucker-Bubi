# 🩸 Zucker Bubi

**Blutzucker-Dokumentation & Auswertung für Linux**

> Autor: Mario Peeß / Großenhain · mapegr@mailbox.org  
> Lizenz: GNU General Public License v3 (GPLv3)  
> Version: 1.0.0

---

## Inhaltsverzeichnis

1. [Über das Programm](#über-das-programm)
2. [Funktionen](#funktionen)
3. [Systemvoraussetzungen](#systemvoraussetzungen)
4. [Installation](#installation)
5. [Erste Schritte](#erste-schritte)
6. [Bluetooth-Synchronisation](#bluetooth-synchronisation)
7. [USB-Import (Accu-Chek)](#usb-import-accu-chek)
8. [CSV-Import](#csv-import)
9. [Manuelle Eingabe](#manuelle-eingabe)
10. [Dashboard & Statistiken](#dashboard--statistiken)
11. [Arztbericht (PDF)](#arztbericht-pdf)
12. [Mehrere Benutzer](#mehrere-benutzer)
13. [Datensicherung & Wiederherstellung](#datensicherung--wiederherstellung)
14. [Farbkodierung](#farbkodierung)
15. [Einheiten](#einheiten)
16. [Datenschutz](#datenschutz)
17. [Fehlerbehebung](#fehlerbehebung)
18. [Haftungsausschluss](#haftungsausschluss)
19. [Drittanbieter](#drittanbieter)

---

## Über das Programm

Zucker Bubi ist ein persönliches Blutzucker-Dokumentationsprogramm für Linux-Desktop-Systeme.  
Es richtet sich an Menschen mit Diabetes, die ihre Messwerte komfortabel erfassen,
auswerten und für den Arztbesuch aufbereiten möchten.

**Kernprinzip:** Alle Daten bleiben lokal auf Ihrem Rechner – kein Internet,
keine Cloud, keine Weitergabe an Dritte.

Getestet auf: Ubuntu, Linux Mint, Linux Mint LMDE, MX Linux, Fedora, openSUSE, Arch Linux.

---

## Funktionen

| Funktion | Beschreibung |
|---|---|
| 📥 USB-Import | Direkte Datenübertragung vom Accu-Chek Guide / Relion via Kabel |
| 🔷 Bluetooth BLE | Drahtlose Synchronisation kompatibler Messgeräte |
| 📁 CSV-Import | Unterstützt mySugr, Accu-Chek Connect, FreeStyle LibreView u.a. |
| ✏️ Manuelle Eingabe | Schnelle Eingabe mit Typ, Notiz und Zeitstempel |
| 📊 Dashboard | Live-Statistiken, 7-Tage-Verlauf, Tages-Übersicht |
| 📋 Übersicht | Vollständige Messhistorie, sortierbar, bearbeitbar, löschbar |
| 📄 PDF-Bericht | Professioneller Arztbericht mit Grafik und Statistiken |
| 👥 Multi-User | Mehrere Benutzerprofile mit individuellen Zielwerten |
| 💾 Backup | ZIP-Sicherung und Wiederherstellung der gesamten Datenbank |
| 🌐 Zweisprachig | Vollständige Deutsch- und Englischunterstützung |

---

## Systemvoraussetzungen

- **Betriebssystem:** Linux (Ubuntu 22.04+, Mint 21+, LMDE 6+, MX Linux 23+, Fedora 39+, Arch, openSUSE Leap 15.5+)
- **Python:** 3.10 oder neuer
- **Tkinter:** `python3-tk` (Systempaket)
- **Bluetooth (optional):** BlueZ, `libbluetooth-dev`
- **USB (optional):** `libusb-1.0-0`, udev-Regeln (werden automatisch eingerichtet)
- **Festplatte:** ca. 50 MB (inkl. Python-Umgebung)

---

## Installation

### Automatisch (empfohlen)

```bash
chmod +x install.sh
./install.sh
```

Das Installationsskript erkennt automatisch den Paketmanager (`apt`, `dnf`, `zypper`, `pacman`)
und installiert alle benötigten Systemabhängigkeiten:

- Python-Bibliotheken (customtkinter, matplotlib, reportlab, bleak, **pyusb**, Pillow)
- USB-Bibliotheken (`libusb`, `python3-usb`)
- Bluetooth-Dienst (`bluez`)
- udev-Regeln für Accu-Chek USB-Geräte
- Desktop-Verknüpfung

**Wichtig nach der Installation:** Einmal ab- und neu anmelden, damit die Gruppenrechte
(`plugdev`, `bluetooth`) wirksam werden.

Bei einer **bestehenden Installation** bietet das Script:
- **Update** – Programmdateien erneuern, Daten bleiben erhalten *(empfohlen)*
- **Neuinstallation** – alles löschen (Datensicherung wird automatisch angelegt)

### Manuell

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

### Programm starten

```bash
~/ZuckerBubi/start.sh
```

Oder: Anwendungsmenü → „Zucker Bubi"

---

## Erste Schritte

1. **Programm starten** → `~/ZuckerBubi/start.sh`
2. **Einstellungen** öffnen (Sidebar) → Patientendaten und Arztinformation eintragen
3. **Einheit wählen:** mmol/L *(Europa-Standard)* oder mg/dL
4. **Zielbereich** festlegen: Standard 3,9–7,8 mmol/L (70–140 mg/dL)
5. **Daten importieren** oder manuell eingeben
6. **Dashboard** zeigt sofort die aktuellen Statistiken

---

## Bluetooth-Synchronisation

### Kompatible Geräte

| Gerät | Protokoll | Status |
|---|---|---|
| Accu-Chek Guide | Bluetooth LE (Glucose Profile) | ✓ Getestet |
| Accu-Chek Active | Bluetooth LE | ✓ Kompatibel |
| Accu-Chek Aviva | Bluetooth LE | ✓ Kompatibel |
| Contour Next One | Bluetooth LE | ✓ Kompatibel |
| OneTouch Verio Reflect | Bluetooth LE | ✓ Kompatibel |
| FreeStyle Libre 2 | NFC (kein BLE) | ✗ |

### Ersteinrichtung

1. Tab **„Verbindung"** öffnen
2. **„🔍 Gerät suchen"** klicken – Bluetooth am Messgerät einschalten und warten
3. Gerät aus der gefundenen Liste auswählen → MAC-Adresse wird eingetragen
4. **„💾 Speichern"** klicken

### Synchronisation

1. Messgerät einschalten
2. **„⟳ Synchronisieren"** klicken
3. Beim ersten Mal erscheint ein **Pairing-Dialog** am Desktop → bestätigen
   *(Das Gerät zeigt dabei einen Code – diesen im Dialog eintragen)*
4. Übertragung dauert ca. 30–60 Sekunden
5. Nur neue Messwerte werden importiert – bereits vorhandene werden übersprungen

**Hinweis:** Die MAC-Adresse bleibt gespeichert. Beim Kauf eines neuen Geräts
gleicher Art einfach „🔍 Gerät suchen" erneut ausführen und die neue MAC speichern.
Bereits importierte Daten bleiben erhalten.

### Diagnose

Falls die Verbindung fehlschlägt: Tab „Verbindung" → **„🔧 Diagnose"** zeigt den Status
von Bluetooth-Dienst und bleak-Bibliothek.

---

## USB-Import (Accu-Chek)

### Kompatible Geräte

| Gerät | USB-ID | Status |
|---|---|---|
| Accu-Chek Guide | 173a:21d5 | ✓ Getestet |
| Accu-Chek (Ältere Modelle) | 173a:21d7 | ✓ Kompatibel |
| Relion Platinum | 173a:21d8 | ✓ Kompatibel |

### Einmalige Einrichtung (udev-Regeln)

Damit das Gerät ohne root-Rechte ausgelesen werden kann, müssen einmalig
udev-Regeln eingerichtet werden:

1. Tab **„Verbindung"** → USB-Bereich
2. Sudo-Passwort eingeben *(oder leer lassen bei passwortlosem sudo)*
3. **„🔧 udev einrichten"** klicken
4. Gerät abstecken und neu einstecken

### Daten auslesen

1. Accu-Chek per USB-Kabel anschließen
2. Am Gerät: **Menü → PC-Verbindung → Datenübertragung** aktivieren
3. **„📥 USB auslesen"** klicken
4. Übertragung läuft automatisch (IEEE 11073 PHD Protokoll)
5. Nur neue Messwerte werden importiert

**Kein C++-Binary nötig** – die Kommunikation erfolgt direkt über `pyusb` in Python.

---

## CSV-Import

Zucker Bubi erkennt automatisch das Spaltenformat der importierten Datei.

### Unterstützte Formate

| Programm | Datum-Format | Wert-Spalte |
|---|---|---|
| **mySugr** | `09.06.2026` | `Blutzuckermessung (mmol/L)` |
| **Accu-Chek Connect** | `YYYY-MM-DD` | `mg/dL` / `mmol/L` |
| **FreeStyle LibreView** | variabel | `Historic Glucose` |
| **Generisch** | DD.MM.YYYY oder YYYY-MM-DD | `Wert`, `value`, `glucose` |

### Import durchführen

1. Tab **„Verbindung"** → Abschnitt „CSV-Import"
2. **„📂 CSV-Datei wählen"** klicken
3. Datei auswählen → Import startet automatisch
4. Das Ergebnis zeigt: `✓ 247 importiert (312 bereits vorhanden, übersprungen)`

**Duplikat-Schutz:** Bereits vorhandene Messungen (gleicher Datum+Uhrzeit-Stempel)
werden niemals doppelt importiert.

---

## Manuelle Eingabe

1. Tab **„Eingabe"** öffnen
2. **Datum** und **Uhrzeit** eintragen *(„Heute" / „Jetzt"-Buttons für schnelle Eingabe)*
3. **Wert** eingeben – kompatibel mit Punkt und Komma als Dezimaltrennzeichen
4. **Messtyp** wählen: Nüchtern / Vor dem Essen / Nach dem Essen / Sonstige
5. Optional: **Notiz** eintragen
6. **„Speichern"** klicken

**Hinweis:** Wird für einen Zeitpunkt bereits ein Eintrag erkannt, erscheint eine
Warnung. Ein zweites Klicken speichert trotzdem (kein Hard-Block).

---

## Dashboard & Statistiken

Das Dashboard zeigt auf einen Blick:

| Karte | Beschreibung |
|---|---|
| **Letzter Wert** | Aktuellste Messung mit Datum und Uhrzeit |
| **Tages-Ø** | Durchschnitt der heutigen Messungen |
| **7-Tage-Ø** | Wochendurchschnitt |
| **30-Tage-Ø** | Monatsdurchschnitt |
| **HbA1c (est.)** | Geschätzter Langzeitwert (Nathan-Formel) |

### Verlaufsgrafik

Die **7-Tage-Grafik** zeigt den täglichen Durchschnittswert mit farbigen Zielbereichen:
- Grün: Zielbereich (individuell einstellbar)
- Orange: Erhöht
- Rot/Pink: Hypoglykämie-Bereiche

### Messungen heute

Unterhalb der Grafik werden alle heutigen Einzelmessungen als farbkodierte Karten angezeigt.

---

## Arztbericht (PDF)

### Inhalt des Berichts

- **Deckblatt** mit Patientendaten und Arztinformation
- **Statistik-Übersicht:** Anzahl, Ø-Wert, Min, Max, Standardabweichung, HbA1c, TIR
- **Verlaufsgrafik** (gewählter Zeitraum)
- **Vollständige Messwert-Tabelle** (farbkodiert nach Status)

### Erstellen

1. Tab **„Arztbericht"** öffnen
2. Zeitraum wählen: 7 / 14 / 30 / 90 Tage
3. Vorschau der Statistiken prüfen
4. **„📄 PDF erstellen"** klicken → Speicherort wählen

*Patientendaten und Arztinformation werden aus den Einstellungen übernommen.*

### HbA1c-Schätzung

Die HbA1c-Schätzung basiert auf der **Nathan-Formel (DCCT)**:

```
HbA1c (%) = (Ø-Glukose [mg/dL] + 46,7) / 28,7
```

Diese Schätzung ist ein Orientierungswert und ersetzt keine Labormessung.

---

## Mehrere Benutzer

Zucker Bubi unterstützt mehrere Benutzerprofile – ideal für Familien oder
wenn das Programm auf einem gemeinsam genutzten Computer läuft.

### Benutzer anlegen

1. Tab **„Einstellungen"** → Abschnitt „Benutzer"
2. **„+ Neuer Benutzer"** klicken → Name eingeben
3. Patientendaten, Arztinformation und persönlichen Zielbereich eintragen

### Zwischen Benutzern wechseln

Über das **Benutzer-Dropdown** in der oberen Leiste – alle Ansichten und
Statistiken wechseln sofort zum gewählten Profil.

### Datentrennung

Jeder Benutzer hat eine vollständig getrennte Messhistorie.
Bluetooth- und USB-Importe werden immer dem aktuell aktiven Benutzer zugeordnet.

---

## Datensicherung & Wiederherstellung

### Sicherung erstellen

Tab **„Übersicht"** → **„💾 Sicherung erstellen"**

Erzeugt eine ZIP-Datei mit:
- `data/gluko.db` – alle Messdaten
- `data/settings.json` – Einstellungen und Benutzerprofile

### Sicherung wiederherstellen

Tab **„Übersicht"** → **„📂 Sicherung laden"** → ZIP-Datei auswählen

**Achtung:** Die aktuelle Datenbank wird vollständig ersetzt.
Vor dem Laden wird eine automatische Sicherung angelegt.

### Manuelle Sicherung

Die Datenbankdatei kann auch manuell gesichert werden:

```bash
cp ~/ZuckerBubi/data/gluko.db ~/Backup/gluko_$(date +%Y%m%d).db
```

---

## Farbkodierung

| Farbe | Bedeutung | mmol/L | mg/dL |
|---|---|---|---|
| 🟢 Grün | Zielbereich | 3,9–7,8 | 70–140 |
| 🟡 Orange | Erhöht | 7,8–10,0 | 140–180 |
| 🔴 Rot | Sehr hoch | > 10,0 | > 180 |
| 🟣 Lila | Niedrig | 3,0–3,9 | 54–70 |
| 🩷 Pink | Sehr niedrig | < 3,0 | < 54 |

*Die Grenzen 3,9 und 7,8 mmol/L entsprechen dem ADA-Standard und können*  
*unter Einstellungen → Zielbereich individuell angepasst werden.*

---

## Einheiten

| Einheit | Typischer Bereich | Region |
|---|---|---|
| mmol/L | 3,9 – 7,8 | Europa, Australien, Kanada |
| mg/dL | 70 – 140 | USA, Deutschland (ältere Geräte) |

**Umrechnung:** `1 mmol/L × 18 = mg/dL`

Die Einheit wird unter **Einstellungen → Einheit** geändert und gilt für
alle Ansichten und den PDF-Bericht. Intern werden alle Werte immer in mmol/L gespeichert.

---

## Datenschutz

- ✓ Alle Daten werden **ausschließlich lokal** gespeichert
- ✓ **Kein Internetzugriff** – das Programm kommuniziert nur mit dem Messgerät
- ✓ **Keine Cloud, keine Server, keine Telemetrie**
- ✓ Die Datenbank liegt unter `~/ZuckerBubi/data/gluko.db` (SQLite)
- ✓ Das Programm kann vollständig **offline** verwendet werden

---

## Fehlerbehebung

### Bluetooth: „Verbindung fehlgeschlagen"

```
• Bluetooth-Dienst prüfen:  systemctl status bluetooth
• Gerät entkoppeln und neu koppeln
• Bluetooth-Dienst neu starten:  sudo systemctl restart bluetooth
• Gerät auf Werkseinstellungen zurücksetzen (Handbuch beachten)
• Abstand reduzieren (< 1 m)
```

### USB: „Kein Gerät gefunden"

```
• udev-Regeln einrichten: Tab Verbindung → "🔧 udev einrichten"
• Gerät abstecken und neu einstecken
• Am Gerät: Menü → PC-Verbindung → Datenübertragung aktivieren
• Gruppenrechte prüfen:  groups $USER  (muss "plugdev" enthalten)
• Nach Gruppenänderung: abmelden und neu anmelden
```

### CSV-Import: „Keine Wert-Spalte gefunden"

```
• Spaltenbezeichnungen der Datei prüfen (erste Zeile)
• Unterstützte Spalten: mg/dL, mmol/L, Wert, value, glucose,
  Blutzuckermessung (mmol/L)
• Encoding-Problem: Datei als UTF-8 speichern
• Trennzeichen: Komma oder Semikolon werden erkannt
```

### Programm startet nicht

```bash
# Fehlerprotokoll prüfen:
cat ~/ZuckerBubi/fehler.log

# Python-Version prüfen (min. 3.10):
python3 --version

# Pakete neu installieren:
~/ZuckerBubi/venv/bin/pip install -r ~/ZuckerBubi/requirements.txt
```

### Jahr wird falsch angezeigt (z. B. 4026 statt 2026)

Das Programm korrigiert diesen Fehler aus einer früheren Version automatisch
beim Start. Falls die Korrektur noch nicht angewendet wurde:

```bash
cd ~/ZuckerBubi && venv/bin/python -c "from database import migrate_wrong_years; print(migrate_wrong_years(), 'Einträge korrigiert')"
```

---

## Projektstruktur

```
ZuckerBubi/
├── main.py                 # Einstiegspunkt
├── app.py                  # Hauptfenster
├── config.py               # Konfiguration, Farben, Pfade
├── database.py             # SQLite-Datenbankoperationen
├── models.py               # Datenmodelle (Messung, User, Statistik)
├── lang.py                 # Übersetzungen DE/EN
├── utils.py                # Hilfsfunktionen
├── sidebar.py              # Navigation
├── topbar.py               # Obere Leiste
├── tab_dashboard.py        # Dashboard-Tab
├── tab_eingabe.py          # Manuelle Eingabe
├── tab_uebersicht.py       # Messhistorie
├── tab_bericht.py          # PDF-Bericht
├── tab_verbindung.py       # Bluetooth & USB
├── tab_einstellungen.py    # Einstellungen
├── tab_hilfe.py            # Hilfe
├── tab_ueber.py            # Über das Programm
├── bluetooth_manager.py    # BLE-Synchronisation (bleak)
├── usb_manager.py          # USB-Import (pyusb)
├── usb_protocol.py         # IEEE 11073 PHD Protokoll
├── dashboard_cards.py      # Statistik-Karten
├── chart_utils.py          # Matplotlib-Diagramme
├── pdf_generator.py        # PDF-Erstellung (reportlab)
├── user_manager.py         # Benutzerverwaltung
├── install.sh              # Installationsskript
├── requirements.txt        # Python-Abhängigkeiten
├── Zucker_Bubi.png         # Programm-Logo
└── data/
    ├── gluko.db            # SQLite-Datenbank (wird beim Start angelegt)
    └── settings.json       # Einstellungen
```

---

## Haftungsausschluss

Dieses Programm dient **ausschließlich zur persönlichen Dokumentation** von Blutzuckerwerten
und ersetzt in keinem Fall ärztliche Beratung, Diagnose oder Behandlung.

Die Berechnungen (HbA1c-Schätzung, Statistiken) sind Orientierungswerte ohne Gewähr.
Medizinische Entscheidungen treffen Sie bitte ausschließlich in Absprache mit Ihrem Arzt.

Der Autor übernimmt keine Haftung für Schäden, die durch die Nutzung dieses Programms
entstehen könnten.

---

## Drittanbieter

| Bibliothek | Autor / Organisation | Lizenz |
|---|---|---|
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Tom Schimansky | MIT |
| [matplotlib](https://matplotlib.org) | Matplotlib Development Team | PSF / BSD |
| [reportlab](https://www.reportlab.com) | ReportLab Inc. | BSD |
| [bleak](https://github.com/hbldh/bleak) | Henrik Blidh | MIT |
| [pyusb](https://github.com/pyusb/pyusb) | PyUSB contributors | BSD |
| [Pillow](https://python-pillow.org) | Jeffrey A. Clark (Alex) | HPND |
| [SQLite](https://sqlite.org) | D. Richard Hipp | Public Domain |

---

## Lizenz

```
Zucker Bubi – Blutzucker-Dokumentation für Linux
Copyright (C) 2025 Mario Peeß / Großenhain

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
```

Vollständiger Lizenztext: https://www.gnu.org/licenses/gpl-3.0.html

---

*© 2025 Mario Peeß / Großenhain · mapegr@mailbox.org*  
*Zucker Bubi v1.0.0 · GNU General Public License v3*
