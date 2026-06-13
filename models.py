# models.py – Datenmodelle
from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class User:
    id: Optional[int]
    name: str
    dob: str = ""
    patient_id: str = ""
    doctor_name: str = ""
    doctor_address: str = ""
    target_low: float = 3.9
    target_high: float = 7.8

    def display_name(self) -> str:
        return self.name or f"Benutzer {self.id}"


@dataclass
class Messung:
    id: Optional[int]
    datum: str        # YYYY-MM-DD
    uhrzeit: str      # HH:MM
    wert_mmol: float  # intern immer mmol/L
    typ: str          # nuchtern|vor_essen|nach_essen|sonstige
    notiz: str = ""
    quelle: str = "manuell"   # manuell | bluetooth

    @property
    def wert_mgdl(self) -> int:
        return round(self.wert_mmol * 18.0)

    def get_wert(self, unit: str) -> float:
        if unit == "mg/dL":
            return float(self.wert_mgdl)
        return round(self.wert_mmol, 1)

    def get_wert_str(self, unit: str) -> str:
        if unit == "mg/dL":
            return str(self.wert_mgdl)
        return f"{self.wert_mmol:.1f}".replace(".", ",")

    def get_status(self, low: float = 3.9, high: float = 7.8) -> str:
        v = self.wert_mmol
        if v < 3.0:   return "very_low"
        if v < low:   return "low"
        if v <= high: return "normal"
        if v <= 10.0: return "high"
        return "very_high"

    @classmethod
    def from_mgdl(cls, id, datum, uhrzeit, wert_mgdl: float,
                  typ="sonstige", notiz="", quelle="manuell"):
        return cls(id, datum, uhrzeit, round(wert_mgdl / 18.0, 2), typ, notiz, quelle)


@dataclass
class Statistik:
    count: int
    avg: float        # mmol/L
    std: float
    min_val: float
    max_val: float
    tir_pct: float    # % Zeit im Zielbereich
    hba1c: float      # geschätzter HbA1c

    @classmethod
    def empty(cls):
        return cls(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def avg_str(self, unit: str) -> str:
        if unit == "mg/dL":
            return f"{round(self.avg * 18)}"
        return f"{self.avg:.1f}".replace(".", ",")

    def min_str(self, unit: str) -> str:
        if unit == "mg/dL":
            return f"{round(self.min_val * 18)}"
        return f"{self.min_val:.1f}".replace(".", ",")

    def max_str(self, unit: str) -> str:
        if unit == "mg/dL":
            return f"{round(self.max_val * 18)}"
        return f"{self.max_val:.1f}".replace(".", ",")


def parse_input(raw: str, unit: str) -> Optional[float]:
    """Eingabestring → mmol/L oder None bei Fehler"""
    try:
        val = float(raw.replace(",", ".").strip())
        if val <= 0:
            return None
        if unit == "mg/dL":
            return round(val / 18.0, 2)
        return round(val, 2)
    except (ValueError, AttributeError):
        return None
