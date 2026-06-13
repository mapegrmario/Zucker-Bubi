# app.py – Hauptfenster mit sauberem Close-Handler
import customtkinter as ctk
from config import COLORS, APP_NAME, APP_VERSION, save_settings
import lang as L
from sidebar import Sidebar
from topbar import Topbar
from tab_dashboard import TabDashboard
from tab_eingabe import TabEingabe
from tab_uebersicht import TabUebersicht
from tab_bericht import TabBericht
from tab_verbindung import TabVerbindung
from tab_einstellungen import TabEinstellungen
from tab_hilfe import TabHilfe
from tab_ueber import TabUeber

TAB_ORDER = [
    ("dashboard",     TabDashboard),
    ("eingabe",       TabEingabe),
    ("uebersicht",    TabUebersicht),
    ("bericht",       TabBericht),
    ("verbindung",    TabVerbindung),
    ("einstellungen", TabEinstellungen),
    ("hilfe",         TabHilfe),
    ("ueber",         TabUeber),
]


class GlukoApp(ctk.CTk):
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry("1240x780")
        self.minsize(980, 640)
        self.configure(fg_color=COLORS["bg"])
        self._tabs: dict = {}
        self._active = None
        # Sauberer Close-Handler – verhindert "invalid command name" Fehler
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_layout()
        self.show_tab("dashboard")

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.topbar = Topbar(
            self, self.settings,
            on_sync=self._on_sync,
            on_lang_change=self._on_lang_change,
            on_user_change=self._on_user_change)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.sidebar = Sidebar(self, on_tab_change=self.show_tab)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        for name, cls in TAB_ORDER:
            try:
                tab = cls(self.content, self.settings, refresh_cb=self._global_refresh)
                tab.grid(row=0, column=0, sticky="nsew")
                tab.grid_remove()
                self._tabs[name] = tab
            except Exception as e:
                import logging
                logging.error(f"Tab '{name}' konnte nicht geladen werden: {e}")

    def show_tab(self, name: str):
        if self._active and self._active in self._tabs:
            self._tabs[self._active].grid_remove()
        if name not in self._tabs:
            return
        self._tabs[name].grid()
        if hasattr(self._tabs[name], "on_show"):
            try:
                self._tabs[name].on_show()
            except Exception:
                pass
        self.sidebar.set_active(name)
        self._active = name

    def _global_refresh(self):
        for tab in self._tabs.values():
            if hasattr(tab, "refresh"):
                try:
                    tab.refresh()
                except Exception:
                    pass

    def _on_user_change(self, user_id: int):
        self.settings["active_user_id"] = user_id
        save_settings(self.settings)
        self._global_refresh()
        if hasattr(self._tabs.get("einstellungen"), "refresh_users"):
            self._tabs["einstellungen"].refresh_users()

    def _on_sync(self):
        from bluetooth_manager import start_sync
        start_sync(self.settings, callback=self._on_bt_result)

    def _on_bt_result(self, success, msg: str):
        # Thread-sicher: immer im Hauptthread ausführen
        try:
            self.after(0, lambda: self._apply_bt(success, msg))
        except Exception:
            pass

    def _apply_bt(self, success, msg):
        try:
            self.topbar.set_bt_status(success, msg)
            if success:
                self._global_refresh()
        except Exception:
            pass

    def _on_lang_change(self, lang_code: str):
        L.set_lang(lang_code)
        self.settings["language"] = lang_code
        save_settings(self.settings)
        try:
            self.topbar.update_texts()
            self.sidebar.update_texts()
        except Exception:
            pass

    def _on_close(self):
        """Sauberes Beenden – verhindert 'invalid command name' nach dem Schließen."""
        try:
            save_settings(self.settings)
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
