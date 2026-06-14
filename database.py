# database.py – SQLite Datenbankoperationen (Multi-User)
import sqlite3, logging, math
from datetime import date, timedelta
from typing import List, Optional
from config import DB_PATH, LOG_PATH
from models import Messung, Statistik, User

logging.basicConfig(
    filename=str(LOG_PATH), level=logging.ERROR,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        # Messungen-Tabelle
        c.execute("""CREATE TABLE IF NOT EXISTS messungen (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            datum     TEXT    NOT NULL,
            uhrzeit   TEXT    NOT NULL,
            wert_mmol REAL    NOT NULL,
            typ       TEXT    DEFAULT 'sonstige',
            notiz     TEXT    DEFAULT '',
            quelle    TEXT    DEFAULT 'manuell',
            user_id   INTEGER DEFAULT 1
        )""")
        # Benutzer-Tabelle
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            dob             TEXT DEFAULT '',
            patient_id      TEXT DEFAULT '',
            doctor_name     TEXT DEFAULT '',
            doctor_address  TEXT DEFAULT '',
            target_low      REAL DEFAULT 3.9,
            target_high     REAL DEFAULT 7.8,
            created         TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        # Migration: user_id zu messungen hinzufügen falls fehlt
        cols = [r[1] for r in c.execute("PRAGMA table_info(messungen)")]
        if "user_id" not in cols:
            c.execute("ALTER TABLE messungen ADD COLUMN user_id INTEGER DEFAULT 1")
        # Performance-Index (wichtig ab ~500 Einträgen)
        c.execute("""CREATE INDEX IF NOT EXISTS idx_m_datum_uid
                     ON messungen(datum, user_id)""")
        # Standard-Benutzer anlegen falls keine vorhanden
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            c.execute("INSERT INTO users (name) VALUES ('Standardbenutzer')")
        c.commit()

# ── Benutzer ─────────────────────────────────────────────────────────────────
def _row_to_user(r) -> User:
    return User(r["id"], r["name"], r["dob"], r["patient_id"],
                r["doctor_name"], r["doctor_address"],
                r["target_low"], r["target_high"])

def get_users() -> List[User]:
    with _conn() as c:
        return [_row_to_user(r) for r in c.execute("SELECT * FROM users ORDER BY id")]

def get_user(uid: int) -> Optional[User]:
    with _conn() as c:
        r = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return _row_to_user(r) if r else None

def add_user(u: User) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO users (name,dob,patient_id,doctor_name,doctor_address,"
            "target_low,target_high) VALUES (?,?,?,?,?,?,?)",
            (u.name, u.dob, u.patient_id, u.doctor_name, u.doctor_address,
             u.target_low, u.target_high))
        c.commit(); return cur.lastrowid

def update_user(u: User):
    with _conn() as c:
        c.execute(
            "UPDATE users SET name=?,dob=?,patient_id=?,doctor_name=?,"
            "doctor_address=?,target_low=?,target_high=? WHERE id=?",
            (u.name, u.dob, u.patient_id, u.doctor_name, u.doctor_address,
             u.target_low, u.target_high, u.id))
        c.commit()

def delete_user(uid: int):
    with _conn() as c:
        c.execute("DELETE FROM users WHERE id=?", (uid,))
        c.execute("DELETE FROM messungen WHERE user_id=?", (uid,))
        c.commit()

# ── Messungen ────────────────────────────────────────────────────────────────
def _row_to_m(r) -> Messung:
    return Messung(r["id"], r["datum"], r["uhrzeit"], r["wert_mmol"],
                   r["typ"], r["notiz"], r["quelle"])

def add_messung(m: Messung, user_id: int = 1) -> int:
    try:
        with _conn() as c:
            cur = c.execute(
                "INSERT INTO messungen (datum,uhrzeit,wert_mmol,typ,notiz,quelle,user_id)"
                " VALUES (?,?,?,?,?,?,?)",
                (m.datum, m.uhrzeit, m.wert_mmol, m.typ, m.notiz, m.quelle, user_id))
            c.commit(); return cur.lastrowid
    except Exception as e:
        logging.error(f"add_messung: {e}"); raise


def migrate_wrong_years() -> int:
    """
    Korrigiert durch den USB-Import falsch gespeicherte Jahreszahlen.
    Beispiel: 4026-06-13 → 2026-06-13  (war 2000 + cc*100 + yy statt cc*100 + yy)
    Gibt Anzahl der korrigierten Zeilen zurück.
    """
    try:
        with _conn() as c:
            r = c.execute(
                "UPDATE messungen SET datum = '20' || SUBSTR(datum, 3)"
                " WHERE datum LIKE '40%' OR datum LIKE '41%' OR datum LIKE '39%'")
            c.commit()
            n = r.rowcount
            if n > 0:
                logging.info(f"migrate_wrong_years: {n} Datensätze korrigiert")
            return n
    except Exception as e:
        logging.error(f"migrate_wrong_years: {e}"); return 0


def messung_exists(datum: str, uhrzeit: str, user_id: int = 1) -> bool:
    """Prüft ob eine Messung mit identischem Datum+Uhrzeit bereits vorhanden ist."""
    try:
        with _conn() as c:
            r = c.execute(
                "SELECT COUNT(*) FROM messungen WHERE datum=? AND uhrzeit=? AND user_id=?",
                (datum, uhrzeit, user_id)).fetchone()
            return r[0] > 0
    except Exception as e:
        logging.error(f"messung_exists: {e}"); return False

def update_messung(m: Messung):
    try:
        with _conn() as c:
            c.execute(
                "UPDATE messungen SET datum=?,uhrzeit=?,wert_mmol=?,typ=?,notiz=? WHERE id=?",
                (m.datum, m.uhrzeit, m.wert_mmol, m.typ, m.notiz, m.id))
            c.commit()
    except Exception as e:
        logging.error(f"update_messung: {e}"); raise

def delete_messung(id_: int):
    try:
        with _conn() as c:
            c.execute("DELETE FROM messungen WHERE id=?", (id_,)); c.commit()
    except Exception as e:
        logging.error(f"delete_messung: {e}"); raise

def get_today(user_id: int = 1) -> List[Messung]:
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM messungen WHERE datum=? AND user_id=? ORDER BY uhrzeit",
                (date.today().isoformat(), user_id)).fetchall()
            return [_row_to_m(r) for r in rows]
    except Exception as e:
        logging.error(f"get_today: {e}"); return []

def get_messungen(days: int = 30, since: str = None, user_id: int = 1) -> List[Messung]:
    try:
        if since is None:
            since = (date.today() - timedelta(days=days)).isoformat()
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM messungen WHERE datum>=? AND user_id=?"
                " ORDER BY datum DESC, uhrzeit DESC", (since, user_id)).fetchall()
            return [_row_to_m(r) for r in rows]
    except Exception as e:
        logging.error(f"get_messungen: {e}"); return []

def get_last_messung(user_id: int = 1) -> Optional[Messung]:
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT * FROM messungen WHERE user_id=?"
                " ORDER BY datum DESC, uhrzeit DESC LIMIT 1", (user_id,)).fetchone()
            return _row_to_m(row) if row else None
    except Exception as e:
        logging.error(f"get_last_messung: {e}"); return None

def calc_statistik(days: int, low: float = 3.9, high: float = 7.8,
                    user_id: int = 1) -> Statistik:
    ms = get_messungen(days, user_id=user_id)
    if not ms: return Statistik.empty()
    vals = [m.wert_mmol for m in ms]
    n = len(vals); avg = sum(vals)/n
    std = math.sqrt(sum((v-avg)**2 for v in vals)/n) if n > 1 else 0.0
    tir = sum(1 for v in vals if low <= v <= high)/n*100
    hba1c = (avg*18.0 + 46.7)/28.7
    return Statistik(n, round(avg,2), round(std,2), round(min(vals),2),
                     round(max(vals),2), round(tir,1), round(hba1c,1))
