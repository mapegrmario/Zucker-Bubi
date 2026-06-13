# config.py – Globale Konfiguration, Farben, Pfade
import json
from pathlib import Path

APP_NAME    = "Zucker Bubi"
APP_VERSION = "1.0.0"
AUTHOR      = "Mario Peeß / Großenhain"
EMAIL       = "mapegr@mailbox.org"

BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH     = DATA_DIR / "gluko.db"
LOG_PATH    = BASE_DIR / "fehler.log"
SETTINGS_PATH = DATA_DIR / "settings.json"
AVATAR_PATH = BASE_DIR / "Zucker_Bubi.png"

COLORS = {
    "primary":       "#2E86AB",
    "primary_dark":  "#1A6B8A",
    "primary_light": "#D6EEF5",
    "accent":        "#57CC99",
    "accent_dark":   "#38A169",
    "warning":       "#F6AD55",
    "danger":        "#FC8181",
    "danger_dark":   "#E53E3E",
    "bg":            "#EFF3F8",
    "bg2":           "#E4EAF2",
    "card":          "#FFFFFF",
    "sidebar":       "#1E2A3A",
    "sidebar_hover": "#2D3E52",
    "sidebar_active":"#2E86AB",
    "text":          "#1A202C",
    "text_muted":    "#718096",
    "border":        "#CBD5E0",
    "normal":        "#48BB78",
    "low":           "#9F7AEA",
    "very_low":      "#ED64A6",
    "high":          "#F6AD55",
    "very_high":     "#FC8181",
    "chart_line":    "#2E86AB",
    "chart_fill":    "#D6EEF5",
    "zone_ok":       "#C6F6D5",
    "zone_warn":     "#FEEBC8",
    "zone_danger":   "#FED7D7",
}

FONT = "Segoe UI"

# mmol/L Referenzwerte (intern immer mmol/L)
REF = {
    "very_low":  3.0,
    "low":       3.9,
    "normal_lo": 3.9,
    "normal_hi": 7.8,
    "high":      10.0,
}

MEASUREMENT_TYPES = ["nuchtern", "vor_essen", "nach_essen", "sonstige"]

TYPE_COLORS = {
    "nuchtern":   "#74B9FF",
    "vor_essen":  "#A29BFE",
    "nach_essen": "#F6AD55",
    "sonstige":   "#CBD5E0",
}

DEFAULT_SETTINGS = {
    "language":       "de",
    "unit":           "mmol/L",
    "active_user_id": 1,
    "theme":          "light",
    "bt_mac":         "",       # MAC-Adresse des BLE-Messgeräts (zB 2C:AB:33:EA:33:44)
}

def load_settings() -> dict:
    s = DEFAULT_SETTINGS.copy()
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH) as f:
                s.update(json.load(f))
        except Exception:
            pass
    return s

def save_settings(s: dict):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
