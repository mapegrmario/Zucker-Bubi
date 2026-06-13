# bluetooth_manager.py – Direktverbindung per MAC, Event-basiertes Warten (kein Sleep-Loop)
import asyncio, threading, logging
from typing import Callable, Optional
from config import LOG_PATH

logging.basicConfig(filename=str(LOG_PATH), level=logging.ERROR,
                    format="%(asctime)s %(levelname)s: %(message)s")

BG_SERVICE_UUID = "00001808-0000-1000-8000-00805f9b34fb"
BG_MEAS_UUID    = "00002a18-0000-1000-8000-00805f9b34fb"
RACP_UUID       = "00002a52-0000-1000-8000-00805f9b34fb"


# ── Decoder (1:1 Port aus accuchek_bluetooth.py) ──────────────────────────────

def decode_sfloat(value_bytes: bytes) -> Optional[float]:
    raw      = int.from_bytes(value_bytes, byteorder="little")
    mantissa = raw & 0x0FFF
    exponent = (raw >> 12) & 0x0F
    if exponent >= 8:    exponent -= 16
    if mantissa >= 2048: mantissa -= 4096
    if mantissa == 0x07FF: return None
    if mantissa == 0x0800: return None
    return mantissa * (10 ** exponent)


def decode_glucose_measurement(data: bytes) -> Optional[dict]:
    """Decodiert Glucose Measurement Characteristic 0x2A18 vollständig."""
    if len(data) < 11: return None
    offset = 0
    flags  = data[offset]; offset += 1
    time_offset_present   = (flags & 0x01) != 0
    type_location_present = (flags & 0x02) != 0
    sensor_status_present = (flags & 0x08) != 0

    sequence = int.from_bytes(data[offset:offset+2], byteorder="little"); offset += 2
    year   = int.from_bytes(data[offset:offset+2], byteorder="little")
    month  = data[offset+2]; day    = data[offset+3]
    hour   = data[offset+4]; minute = data[offset+5]; second = data[offset+6]
    offset += 7

    if time_offset_present and offset + 2 <= len(data):
        offset += 2

    glucose_mg_dl = None
    if offset + 2 <= len(data):
        raw = decode_sfloat(data[offset:offset+2])
        if raw is not None:
            glucose_mg_dl = raw
        offset += 2

    if sensor_status_present and offset < len(data): offset += 1
    if type_location_present  and offset < len(data): offset += 1

    if not glucose_mg_dl or glucose_mg_dl <= 0: return None
    try:
        from datetime import datetime
        dt = datetime(year, month, day, hour, minute, second)
        return {"sequence": sequence,
                "datum":    dt.strftime("%Y-%m-%d"),
                "uhrzeit":  dt.strftime("%H:%M"),
                "mg_dL":    int(glucose_mg_dl),
                "mmol_L":   round(glucose_mg_dl / 18.0, 3)}
    except Exception as e:
        logging.error(f"decode date: {e}"); return None


# ── Scan ──────────────────────────────────────────────────────────────────────

async def _scan_async(timeout: float = 10.0) -> list:
    from bleak import BleakScanner
    KNOWN = ["Accu-Chek", "Contour", "OneTouch", "FreeStyle",
             "GlucoMen", "Beurer", "MyStar", "iBGStar"]
    found = []
    devs = await BleakScanner.discover(timeout=timeout, return_adv=True)
    for dev, adv in devs.values():
        name  = (dev.name or "").strip()
        uuids = [u.lower() for u in (adv.service_uuids or [])]
        if BG_SERVICE_UUID in uuids or \
                any(k.lower() in name.lower() for k in KNOWN):
            found.append((dev.address, name or dev.address))
    return found


def scan_devices(result_cb: Callable[[list], None]):
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:   result_cb(loop.run_until_complete(_scan_async()))
        except Exception as e:
            logging.error(f"scan: {e}"); result_cb([])
        finally: loop.close()
    threading.Thread(target=_run, daemon=True).start()


# ── Sync – Event-basiert, kein Sleep-Loop ─────────────────────────────────────

async def _do_sync(settings: dict, callback: Callable):
    import lang as L
    try:
        from bleak import BleakClient
    except ImportError:
        callback(False, L.t("bt_no_bleak")); return

    mac = settings.get("bt_mac", "").strip().upper()
    if not mac or len(mac) != 17:
        callback(False,
                 "❌  Keine MAC-Adresse gespeichert.\n"
                 "→  '🔍 Gerät suchen' klicken, dann MAC wählen."); return

    callback(None, f"⟳  Verbinde mit {mac} …\n"
             "   (Pairing-Dialog bestätigen, falls er erscheint)")

    measurements: list = []
    seen_seq:     set  = set()
    done          = asyncio.Event()   # ← wird gesetzt wenn Transfer fertig ist

    def _on_disconnect(_client):
        """Gerät hat Verbindung beendet (nach Datentransfer normal → kein Fehler)."""
        logging.info("BLE: Gerät hat Verbindung getrennt")
        done.set()   # sauber beenden, nicht als Fehler werten

    def _on_measurement(_, data: bytes):
        m = decode_glucose_measurement(data)
        if m and m["sequence"] not in seen_seq:
            seen_seq.add(m["sequence"])
            measurements.append(m)

    def _on_racp(_, data: bytes):
        """
        RACP Response Code 0x06 = Übertragung abgeschlossen.
        Byte 0: 0x06 (Response Code Op)
        Byte 1: 0x00 (Null Operator)
        Byte 2: 0x01 (Report Stored Records)
        Byte 3: 0x01 (Success) / 0x06 (No records found)
        """
        if data and data[0] == 0x06:
            done.set()   # RACP signalisiert Fertigmeldung

    # Verbindung manuell verwalten (kein Context Manager) → sauberes Disconnect
    client = BleakClient(mac, timeout=30.0,
                         disconnected_callback=_on_disconnect)
    try:
        await client.connect()
    except Exception as e:
        logging.error(f"BLE connect: {e}")
        callback(False,
                 f"❌  Verbindung fehlgeschlagen: {e}\n\n"
                 "• Gerät einschalten + Bluetooth aktiv?\n"
                 "• Gerät neu pairen: erst entkoppeln, dann erneut versuchen\n"
                 "• Abstand < 1 m?"); return

    callback(None, f"⟳  Verbunden – empfange Daten von {mac} …")

    try:
        # Glucose Service + RACP Characteristic suchen
        racp_char = None
        for svc in client.services:
            if svc.uuid.lower() == BG_SERVICE_UUID:
                racp_char = svc.get_characteristic(RACP_UUID)
                break

        if not racp_char:
            callback(False, "❌  Kein Glucose Service auf diesem Gerät.\n"
                     "   Falsches Gerät oder Profil nicht aktiv?")
            return

        await client.start_notify(BG_MEAS_UUID, _on_measurement)
        await client.start_notify(racp_char.handle, _on_racp)   # handle, nicht UUID!

        # RACP: alle gespeicherten Datensätze senden
        await client.write_gatt_char(racp_char.handle,
                                     bytes([0x01, 0x01]), response=True)

        # Warten auf: RACP-Fertigmeldung ODER Gerät trennt ODER 60s Timeout
        # → kein asyncio.sleep → kein reconnect-Loop
        try:
            await asyncio.wait_for(done.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            pass   # Timeout ist OK – nehmen was angekommen ist

    except Exception as e:
        logging.error(f"BLE transfer: {e}")
        callback(False, f"❌  Übertragungsfehler: {e}"); return
    finally:
        # Sauber trennen wenn noch verbunden
        if client.is_connected:
            try:
                await client.stop_notify(BG_MEAS_UUID)
            except Exception: pass
            try:
                await client.disconnect()
            except Exception: pass

    if not measurements:
        callback(False,
                 "❌  Keine Messwerte empfangen.\n"
                 "→  Gerät einschalten und erneut versuchen"); return

    measurements.sort(key=lambda x: x["sequence"])

    from database import add_messung, messung_exists
    from models import Messung

    uid = settings.get("active_user_id", 1)
    imported = dupes = 0
    for m in measurements:
        if messung_exists(m["datum"], m["uhrzeit"], uid):
            dupes += 1; continue
        add_messung(Messung(None, m["datum"], m["uhrzeit"],
                            m["mmol_L"], "sonstige", "", "bluetooth"), uid)
        imported += 1

    msg = f"✓  {imported} Messwerte importiert"
    if dupes: msg += f"  ({dupes} bereits vorhanden, übersprungen)"
    callback(True, msg)


def start_sync(settings: dict, callback: Callable):
    """BLE-Sync in separatem Thread – einmalig, kein Auto-Retry."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_do_sync(settings, callback))
        except Exception as e:
            logging.error(f"start_sync: {e}")
            callback(False, f"❌  {e}")
        finally:
            loop.close()
    threading.Thread(target=_run, daemon=True).start()
