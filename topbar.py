# topbar.py – Obere Leiste mit Bluetooth-Sync, Benutzer-Wechsler und Sprachschalter
import customtkinter as ctk
from config import COLORS, APP_NAME, APP_VERSION, save_settings
from database import get_users
import lang as L


class Topbar(ctk.CTkFrame):
    def __init__(self, parent, settings: dict, on_sync, on_lang_change, on_user_change=None):
        super().__init__(parent, height=52, corner_radius=0,
                         fg_color=COLORS["card"])
        self.grid_propagate(False)
        self._on_sync = on_sync
        self._on_lang = on_lang_change
        self._on_user = on_user_change
        self._settings = settings
        self._status_var = ctk.StringVar(value="")
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)

        # Titel
        self._title = ctk.CTkLabel(
            self, text=L.t("app_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"])
        self._title.grid(row=0, column=0, padx=(20, 0), pady=10, sticky="w")

        # Status
        self._status_lbl = ctk.CTkLabel(
            self, textvariable=self._status_var,
            font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
        self._status_lbl.grid(row=0, column=1, padx=10, sticky="w")

        # Rechte Seite
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, padx=(0, 16), sticky="e")

        # Benutzer-Wechsler
        self._user_menu = ctk.CTkOptionMenu(
            right, values=self._user_names(),
            font=ctk.CTkFont(size=11), height=32, width=140,
            fg_color=COLORS["bg"], text_color=COLORS["text"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["primary_light"],
            corner_radius=8, command=self._on_user_select)
        self._user_menu.pack(side="left", padx=(0, 8))
        self._refresh_user_menu()

        # BT-Sync
        self._btn_sync = ctk.CTkButton(
            right, text=L.t("btn_sync"),
            font=ctk.CTkFont(size=12), height=32, width=195,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            corner_radius=16, command=self._on_sync_click)
        self._btn_sync.pack(side="left", padx=(0, 10))

        # Sprache
        self._lang_menu = ctk.CTkOptionMenu(
            right, values=["Deutsch", "English"],
            font=ctk.CTkFont(size=11), height=32, width=95,
            fg_color=COLORS["bg"], text_color=COLORS["text"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["primary_light"],
            corner_radius=8, command=self._on_lang_select)
        self._lang_menu.set("Deutsch" if self._settings.get("language","de")=="de" else "English")
        self._lang_menu.pack(side="left")

        # Trennlinie
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, columnspan=3, sticky="ew")

    def _user_names(self):
        try:
            return [u.display_name() for u in get_users()] or ["–"]
        except Exception:
            return ["–"]

    def _refresh_user_menu(self):
        names = self._user_names()
        self._user_menu.configure(values=names)
        try:
            from database import get_user
            uid = self._settings.get("active_user_id", 1)
            u = get_user(uid)
            if u:
                self._user_menu.set(u.display_name())
        except Exception:
            pass

    def _on_user_select(self, choice: str):
        try:
            users = get_users()
            u = next((x for x in users if x.display_name() == choice), None)
            if u:
                self._settings["active_user_id"] = u.id
                save_settings(self._settings)
                if self._on_user:
                    self._on_user(u.id)
        except Exception:
            pass

    def _on_sync_click(self):
        self._btn_sync.configure(state="disabled", text="⟳ Verbinde …")
        self._status_var.set(L.t("bt_scanning"))
        self._on_sync()

    def set_bt_status(self, success, msg: str):
        self._btn_sync.configure(state="normal", text=L.t("btn_sync"))
        color = COLORS["normal"] if success else COLORS["danger"]
        if success is None: color = COLORS["warning"]
        self._status_var.set(msg)
        self._status_lbl.configure(text_color=color)
        self.after(5000, lambda: self._status_var.set(""))

    def _on_lang_select(self, choice: str):
        self._on_lang("de" if choice == "Deutsch" else "en")

    def update_texts(self):
        self._title.configure(text=L.t("app_title"))
        self._btn_sync.configure(text=L.t("btn_sync"))

    def update_users(self):
        self._refresh_user_menu()
