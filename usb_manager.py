# usb_manager.py – USB-Import via pyusb (Pure Python, kein Binary nötig)
import subprocess, os, logging, threading
from pathlib import Path
from typing import Callable, Optional
from config import LOG_PATH

logging.basicConfig(filename=str(LOG_PATH), level=logging.ERROR,
                    format="%(asctime)s %(levelname)s: %(message)s")

# udev-Regeln mit Accu-Chek Vendor-IDs (173a)
UDEV_RULE = (
    '# Zucker Bubi – Accu-Chek USB Messgeräte\n'
    'SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d5",'
    ' MODE="0666", GROUP="plugdev"\n'
    'SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d7",'
    ' MODE="0666", GROUP="plugdev"\n'
    'SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d8",'
    ' MODE="0666", GROUP="plugdev"\n'
    'SUBSYSTEM=="usb", ATTR{idVendor}=="04b4", MODE="0666", GROUP="plugdev"\n'
    'SUBSYSTEM=="usb", ATTR{idVendor}=="0a21", MODE="0666", GROUP="plugdev"\n'
)
UDEV_PATH = Path("/etc/udev/rules.d/99-glucose-usb.rules")


def is_pyusb_available() -> bool:
    """Prüft ob pyusb installiert ist."""
    try:
        import usb.core  # noqa
        return True
    except ImportError:
        return False


def is_udev_configured() -> bool:
    return UDEV_PATH.exists()


def check_usb_device() -> Optional[str]:
    """Prüft ob ein Accu-Chek Gerät per USB angeschlossen ist."""
    try:
        r = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if any(k.lower() in line.lower()
                   for k in ["173a", "Roche", "ACCU-CHEK", "AccuChek", "04b4", "0a21"]):
                return line.strip()
        return None
    except Exception as e:
        logging.error(f"check_usb_device: {e}")
        return None


def setup_udev_rules(sudo_password: str = "") -> tuple[bool, str]:
    """Richtet udev-Regeln ein (einmalig, erfordert sudo)."""
    try:
        rule_esc = UDEV_RULE.replace("'", "'\\''")
        cmd = (f"printf '{rule_esc}' > {UDEV_PATH} && "
               f"udevadm control --reload-rules && udevadm trigger")
        kw = dict(capture_output=True, text=True, timeout=15)
        if sudo_password:
            r = subprocess.run(["sudo", "-S", "bash", "-c", cmd],
                               input=sudo_password + "\n", **kw)
        else:
            r = subprocess.run(["sudo", "bash", "-c", cmd], **kw)
        if r.returncode != 0:
            return False, r.stderr[:200]
        subprocess.run(["sudo", "-n", "usermod", "-aG", "plugdev",
                        os.environ.get("USER", "")], timeout=5)
        return True, "✓ udev-Regeln eingerichtet"
    except Exception as e:
        return False, str(e)


def _import_data(data: list, user_id: int, callback: Callable):
    """Importiert geparste Messwerte in die DB – überspringt Duplikate."""
    from database import add_messung, messung_exists
    from models import Messung

    imported = skipped = dupes = 0
    for entry in data:
        try:
            ts     = str(entry.get("timestamp", ""))
            datum  = ts[:10]; uhrzeit = ts[11:16]
            mmol   = round(float(entry.get("mmol_L") or
                                 float(entry.get("mg_dL", 0)) / 18.0), 3)
            if mmol <= 0:
                skipped += 1; continue
            if messung_exists(datum, uhrzeit, user_id):
                dupes += 1; continue
            add_messung(Messung(None, datum, uhrzeit, mmol,
                                "sonstige", "USB-Import", "usb"), user_id)
            imported += 1
        except Exception as e:
            logging.error(f"_import_data: {e}"); skipped += 1

    msg = f"✓  {imported} neu importiert"
    if dupes:   msg += f"  ({dupes} bereits vorhanden)"
    if skipped: msg += f"  ({skipped} übersprungen)"
    callback(msg, True)


def read_usb(callback: Callable[[str, bool], None],
             user_id: int = 1, sudo_password: str = ""):
    """Liest Messungen via USB aus und importiert sie in die DB."""
    def _run():
        if not is_pyusb_available():
            callback("❌  pyusb nicht installiert\n"
                     "→ install.sh erneut ausführen oder:\n"
                     "  pip install pyusb --break-system-packages", False)
            return

        from usb_protocol import find_device, connect_device, download
        import usb.util

        dev, name = find_device()
        if not dev:
            callback("❌  Kein Accu-Chek Gerät gefunden\n"
                     "→ USB-Kabel anschließen + 'Datenübertragung' am Gerät aktivieren\n"
                     "→ Falls noch nicht: '🔧 udev einrichten' klicken", False)
            return

        callback(f"⟳  {name} erkannt – starte Protokoll …", None)
        try:
            ep_i, ep_o = connect_device(dev)

            def _progress(seg, total):
                callback(f"⟳  Segment {seg} gelesen – {total} Messwerte bisher …", None)

            data = download(dev, ep_i, ep_o, progress_cb=_progress)
        except Exception as e:
            logging.error(f"read_usb download: {e}")
            callback(f"❌  Protokollfehler: {e}\n\n"
                     "Lösung A: '🔧 udev einrichten' klicken,\n"
                     "  danach Gerät abstecken + neu einstecken\n\n"
                     "Lösung B: Passwort eingeben und erneut versuchen", False)
            return
        finally:
            try: usb.util.dispose_resources(dev)
            except Exception: pass

        if not data:
            callback("❌  Keine Messwerte im Gerät", False); return

        callback(f"⟳  {len(data)} Einträge – importiere …", None)
        _import_data(data, user_id, callback)

    threading.Thread(target=_run, daemon=True).start()


def _csv_parse_date(raw: str) -> str:
    """Konvertiert DD.MM.YYYY oder D.M.YYYY → YYYY-MM-DD. Lässt YYYY-MM-DD durch."""
    raw = raw.strip().strip('"')
    if len(raw) >= 8 and '.' in raw:
        parts = raw.split('.')
        if len(parts) == 3:
            dd, mm, yyyy = parts[0].zfill(2), parts[1].zfill(2), parts[2][:4]
            return f"{yyyy}-{mm}-{dd}"
    return raw[:10]


def _csv_find_columns(headers: list) -> tuple:
    """
    Findet Datum-, Zeit- und Wert-Spalte automatisch.
    Gibt (datum_col, zeit_col, wert_col, einheit) zurück.
    """
    datum_col = zeit_col = wert_col = None
    einheit   = "mmol/L"

    for h in headers:
        hl = h.lower()
        # Datum
        if datum_col is None and any(k in hl for k in ["datum", "date"]):
            datum_col = h
        # Zeit / Uhrzeit
        if zeit_col is None and any(k in hl for k in ["zeit", "uhrzeit", "time"]):
            zeit_col = h
        # Wert: mmol
        if wert_col is None and "mmol" in hl and any(
                k in hl for k in ["blutzucker", "glukose", "glucose",
                                   "messung", "wert", "value", "mmol/l"]):
            wert_col = h; einheit = "mmol/L"
        # Wert: mg/dL
        if wert_col is None and any(k in hl for k in ["mg/dl", "mg_dl"]):
            wert_col = h; einheit = "mg/dL"

    # Letzte Fallbacks für einfache Spaltennamen
    for h in headers:
        if datum_col is None and h.lower() == "datum":   datum_col = h
        if zeit_col  is None and h.lower() in ("zeit", "uhrzeit", "time"): zeit_col = h
        if wert_col  is None and h.lower() in ("wert", "value", "glucose"): wert_col = h

    return datum_col, zeit_col, wert_col, einheit


def import_csv(path: str, user_id: int, unit: str) -> tuple[int, int]:
    """
    Universeller CSV-Import.
    Unterstützt: mySugr, Accu-Chek Connect, FreeStyle LibreView, generische CSVs.
    Erkennt automatisch: Spaltenbezeichnungen, Datumsformat (DD.MM.YYYY / YYYY-MM-DD),
    Dezimalzeichen (Komma / Punkt) und Einheit (mmol/L / mg/dL).
    """
    from database import add_messung, messung_exists
    from models import Messung, parse_input
    import csv

    imported = skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader     = csv.DictReader(f)
        headers    = reader.fieldnames or []
        datum_col, zeit_col, wert_col, auto_unit = _csv_find_columns(headers)

        if not wert_col:
            logging.error(f"import_csv: keine Wert-Spalte in {headers}")
            raise ValueError(
                f"Keine Wert-Spalte gefunden.\n"
                f"Spalten in der Datei: {', '.join(headers[:8])}")

        # Einheit: explizit aus Spaltennamen bevorzugen
        use_unit = auto_unit

        for row in reader:
            try:
                raw = row.get(wert_col, "").strip().strip('"')
                if not raw:
                    skipped += 1; continue

                mmol = parse_input(raw.replace(",", "."), use_unit)
                if not mmol or mmol <= 0:
                    skipped += 1; continue

                raw_datum = row.get(datum_col or "", "").strip().strip('"')
                datum = _csv_parse_date(raw_datum) if raw_datum else ""
                if len(datum) != 10:
                    skipped += 1; continue

                raw_zeit = row.get(zeit_col or "", "00:00").strip().strip('"')
                uhrzeit  = raw_zeit[:5] if raw_zeit else "00:00"

                if messung_exists(datum, uhrzeit, user_id):
                    skipped += 1; continue

                notiz = row.get("Notiz", row.get("note", ""))[:100]
                add_messung(Messung(None, datum, uhrzeit, mmol,
                                   "sonstige", notiz, "csv"), user_id)
                imported += 1
            except Exception as e:
                logging.error(f"import_csv row: {e}"); skipped += 1

    return imported, skipped
