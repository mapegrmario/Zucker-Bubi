#!/usr/bin/env python3
# main.py – Einstiegspunkt Zucker Bubi
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from config import load_settings, LOG_PATH
from database import init_db, migrate_wrong_years
import lang as L

logging.basicConfig(
    filename=str(LOG_PATH), level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(module)s: %(message)s"
)


def main():
    settings = load_settings()
    L.set_lang(settings.get("language", "de"))
    init_db()
    migrate_wrong_years()   # korrigiert Jahreszahlen aus altem USB-Bug

    # DPI-Scaling deaktivieren – verhindert "invalid command name check_dpi_scaling"
    # auf MX Linux / Debian mit Python 3.13 + Tk 8.6
    try:
        import customtkinter as ctk
        ctk.deactivate_automatic_dpi_awareness()
    except Exception:
        pass

    try:
        from app import GlukoApp
        app = GlukoApp(settings)
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception("Kritischer Fehler beim Start")
        print(f"[FEHLER] {e}")
        print(f"Details in: {LOG_PATH}")
        raise


if __name__ == "__main__":
    main()
