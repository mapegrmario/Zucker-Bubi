# usb_protocol.py – IEEE 11073 PHD USB-Protokoll (Accu-Chek Guide / Relion)
# Basiert auf dem getesteten accuchek_usb.py (Mario Peeß)
import struct, time, logging
from datetime import datetime
from config import LOG_PATH

logging.basicConfig(filename=str(LOG_PATH), level=logging.ERROR,
                    format="%(asctime)s %(levelname)s: %(message)s")

KNOWN_DEVICES = {
    (0x173a, 0x21d5): "Accu-Chek Guide",
    (0x173a, 0x21d7): "Accu-Chek (Alt)",
    (0x173a, 0x21d8): "Relion Platinum",
}

APDU_ASSOC_RESP   = 0xE300
APDU_PRESENTATION = 0xE700
APDU_RELEASE_REQ  = 0xE400
RESP_CONF_EV      = 0x0201
INVOKE_GET        = 0x0103
INVOKE_CACT       = 0x0107
EV_CONFIG         = 0x0D1C
EV_SEG_DATA       = 0x0D21
ACT_SEG_INFO      = 0x0C0D
ACT_SEG_TRIG      = 0x0C1C
MDC_PMSTORE       = 61


def _b16(v): return struct.pack('>H', v)
def _b32(v): return struct.pack('>I', v)
def _r16(d, o): return struct.unpack('>H', d[o:o+2])[0] if len(d) >= o+2 else 0
def _r32(d, o): return struct.unpack('>I', d[o:o+4])[0] if len(d) >= o+4 else 0
def _bcd(x):    return int(f"{x:02X}")


def find_device():
    """Sucht Accu-Chek USB-Gerät. Gibt (device, name) oder (None, None) zurück."""
    try:
        import usb.core
        for (vid, pid), name in KNOWN_DEVICES.items():
            d = usb.core.find(idVendor=vid, idProduct=pid)
            if d:
                return d, name
    except ImportError:
        pass
    return None, None


def connect_device(dev):
    """Initialisiert USB-Verbindung. Gibt (ep_in, ep_out) zurück."""
    import usb.util
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except Exception:
        pass
    dev.set_configuration()
    usb.util.claim_interface(dev, 0)
    dev.set_interface_altsetting(0, 0)
    cfg  = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    _dir = usb.util.endpoint_direction
    ep_o = usb.util.find_descriptor(
        intf, custom_match=lambda e:
        _dir(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
    ep_i = usb.util.find_descriptor(
        intf, custom_match=lambda e:
        _dir(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
    return ep_i, ep_o


def _pdu(inner: bytes) -> bytes:
    """Verpackt Payload in APDU_PRESENTATION-Rahmen."""
    n = len(inner)
    return bytes(_b16(APDU_PRESENTATION) + _b16(n + 2) + _b16(n) + inner)


def _assoc_resp() -> bytes:
    return bytes(
        _b16(APDU_ASSOC_RESP) + _b16(44) + _b16(0x0003) + _b16(20601) +
        _b16(38) + _b32(0x80000002) + _b16(0x8000) + _b32(0x80000000) +
        _b32(0) + _b32(0x80000000) + _b16(8) + _b32(0x12345678) +
        _b32(0) + _b32(0) + _b32(0) + _b16(0))


def _find_pmstore(data: bytes) -> int:
    offset = 24
    count  = _r16(data, offset); offset += 4
    for _ in range(count):
        if len(data) < offset + 8: break
        cls  = _r16(data, offset)
        hndl = _r16(data, offset + 2)
        sz   = _r16(data, offset + 6)
        if cls in (MDC_PMSTORE, 250):
            return hndl
        offset += 8 + sz
    return 0


def _parse_segment(data: bytes, base: int = 30) -> list:
    """Parst Messeinträge aus einem PMSTORE-Segment-Datenpaket."""
    nb = _r16(data, base)
    entries = []; offset = base
    for _ in range(nb):
        if len(data) < offset + 18: break
        cc = _bcd(data[6 + offset]); yy = _bcd(data[7 + offset])
        mm = _bcd(data[8 + offset]); dd = _bcd(data[9 + offset])
        hh = _bcd(data[10 + offset]); mn = _bcd(data[11 + offset])
        vv = _r16(data, 14 + offset); ss = _r16(data, 16 + offset)
        if ss == 0:
            try:
                entries.append(dict(year=cc * 100 + yy,          # cc=20,yy=26 → 2026
                                    month=mm, day=dd, hour=hh, minute=mn, val=vv))
            except Exception: pass
        offset += 12
    return entries


def download(dev, ep_i, ep_o, progress_cb=None) -> list:
    """
    Lädt alle Messwerte via IEEE 11073 PHD vom Gerät.
    Gibt Liste von dicts zurück: {timestamp, epoch, mg_dL, mmol_L}
    """
    dev.ctrl_transfer(0x80, 0x00, 0, 0, 2, 5000); time.sleep(1.5)
    raw = None
    for _ in range(3):
        try: raw = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=8000)); break
        except Exception: time.sleep(1.0)
    if not raw or len(raw) < 10:
        raise RuntimeError("Kein Pairing Request empfangen")

    ep_o.write(_assoc_resp(), timeout=5000)
    raw  = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=5000))
    iid  = _r16(raw, 6)
    hndl = _find_pmstore(raw)
    if not hndl: raise RuntimeError("PMSTORE Handle nicht gefunden")

    # Config ACK
    pl = (_b16(iid) + _b16(RESP_CONF_EV) + _b16(14) + _b16(0) + _b32(0) +
          _b16(EV_CONFIG) + _b16(4) + _b16(0x4000) + _b16(0))
    ep_o.write(_pdu(bytes(pl)), timeout=5000)
    # GET
    pl = _b16(iid + 1) + _b16(INVOKE_GET) + _b16(6) + _b16(0) + _b32(0)
    ep_o.write(_pdu(bytes(pl)), timeout=5000)
    raw = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=5000))
    iid = _r16(raw, 6)
    # SEG GET INFO
    pl = (_b16(iid + 1) + _b16(INVOKE_CACT) + _b16(12) + _b16(hndl) +
          _b16(ACT_SEG_INFO) + _b16(6) + _b16(1) + _b16(2) + _b16(0))
    ep_o.write(_pdu(bytes(pl)), timeout=5000)
    raw = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=5000))
    iid = _r16(raw, 6)
    # SEG TRIG XFER
    pl = (_b16(iid + 1) + _b16(INVOKE_CACT) + _b16(8) + _b16(hndl) +
          _b16(ACT_SEG_TRIG) + _b16(2) + _b16(0))
    ep_o.write(_pdu(bytes(pl)), timeout=5000)
    time.sleep(1.5)
    raw = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=8000))
    iid = _r16(raw, 6)

    measurements = []; seg = 0
    while True:
        try: raw = bytes(dev.read(ep_i.bEndpointAddress, 1024, timeout=10000))
        except Exception: break
        if len(raw) < 32: break
        status = raw[32]; iid = _r16(raw, 6)
        for e in _parse_segment(raw, 30):
            try:
                dt = datetime(e['year'], e['month'], e['day'], e['hour'], e['minute'])
                measurements.append({"timestamp": dt.strftime("%Y-%m-%d %H:%M"),
                                     "epoch":     int(dt.timestamp()),
                                     "mg_dL":     e['val'],
                                     "mmol_L":    round(e['val'] / 18.0, 3)})
            except Exception as ex: logging.error(f"usb_parse: {ex}")
        if progress_cb: progress_cb(seg + 1, len(measurements))
        # Segment ACK
        u0 = _r32(raw, 22); u1 = _r32(raw, 26); u2 = _r16(raw, 30)
        pl = (_b16(iid) + _b16(RESP_CONF_EV) + _b16(22) + _b16(hndl) +
              _b32(0xFFFFFFFF) + _b16(EV_SEG_DATA) + _b16(12) +
              _b32(u0) + _b32(u1) + _b16(u2) + _b16(0x0080))
        ep_o.write(_pdu(bytes(pl)), timeout=5000)
        if status & 0x40: break
        seg += 1
    # Release
    try:
        ep_o.write(bytes(_b16(APDU_RELEASE_REQ) + _b16(2) + _b16(0)), timeout=3000)
        dev.read(ep_i.bEndpointAddress, 64, timeout=2000)
    except Exception: pass
    return measurements
