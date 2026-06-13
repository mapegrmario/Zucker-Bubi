# user_manager.py – Benutzerverwaltungs-Panel (inline, kein extra Fenster)
import customtkinter as ctk
from config import COLORS
from database import get_users, add_user, update_user, delete_user, get_user
from models import User
import lang as L


class UserManagerPanel(ctk.CTkFrame):
    """Einbettbares Panel für Benutzerverwaltung (z.B. in Einstellungen)."""

    def __init__(self, parent, settings: dict, on_user_change: callable):
        super().__init__(parent, corner_radius=14, fg_color=COLORS["card"],
                          border_width=1, border_color=COLORS["border"])
        self._s = settings
        self._on_change = on_user_change
        self._selected_uid = settings.get("active_user_id", 1)
        self._edit_mode = False
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="👥  Benutzer",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=COLORS["primary"]
                      ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12,4))
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # Benutzer-Liste
        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=6)
        self._list_frame.grid_columnconfigure(0, weight=1)

        # Neue Benutzer Button
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=2, sticky="e", padx=16, pady=(0,6))
        ctk.CTkButton(btn_row, text="＋ Neuer Benutzer", width=150, height=30,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                       corner_radius=8, font=ctk.CTkFont(size=11),
                       command=self._new_user).pack(side="left")
        self._status = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=10),
                                     text_color=COLORS["normal"])
        self._status.pack(side="left", padx=(8,0))

        # Editierformular (anfangs versteckt)
        self._form = ctk.CTkFrame(self, corner_radius=10,
                                   fg_color=COLORS["bg"], border_width=1,
                                   border_color=COLORS["primary"])
        self._build_form(self._form)
        self._form.grid(row=4, column=0, columnspan=2, sticky="ew",
                         padx=12, pady=(0,12))
        self._form.grid_remove()

        self._refresh_list()

    def _build_form(self, f):
        f.grid_columnconfigure(1, weight=1)
        LBL = {"font": ctk.CTkFont(size=11), "text_color": COLORS["text_muted"], "anchor": "e"}
        fields = [
            ("name",    "Name *"),
            ("dob",     "Geburtsdatum"),
            ("pid",     "Patienten-ID"),
            ("doc",     "Arztname"),
            ("addr",    "Praxisadresse"),
        ]
        self._fvars = {}
        for i, (key, lbl) in enumerate(fields):
            ctk.CTkLabel(f, text=lbl, **LBL).grid(row=i, column=0, sticky="e",
                                                    padx=(10,6), pady=3)
            var = ctk.StringVar()
            ctk.CTkEntry(f, textvariable=var, font=ctk.CTkFont(size=11),
                          fg_color=COLORS["card"], height=28
                          ).grid(row=i, column=1, sticky="ew", padx=(0,10), pady=3)
            self._fvars[key] = var

        # Zielbereich
        ctk.CTkLabel(f, text="Ziel min", **LBL).grid(row=5, column=0, sticky="e",
                                                       padx=(10,6), pady=3)
        tf = ctk.CTkFrame(f, fg_color="transparent")
        tf.grid(row=5, column=1, sticky="w", padx=(0,10), pady=3)
        self._fvars["tlo"] = ctk.StringVar(value="3.9")
        self._fvars["thi"] = ctk.StringVar(value="7.8")
        ctk.CTkEntry(tf, textvariable=self._fvars["tlo"], width=70,
                      font=ctk.CTkFont(size=11), fg_color=COLORS["card"], height=28
                      ).pack(side="left", padx=(0,4))
        ctk.CTkLabel(tf, text="max", font=ctk.CTkFont(size=10),
                      text_color=COLORS["text_muted"]).pack(side="left", padx=(0,4))
        ctk.CTkEntry(tf, textvariable=self._fvars["thi"], width=70,
                      font=ctk.CTkFont(size=11), fg_color=COLORS["card"], height=28
                      ).pack(side="left")

        btn_r = ctk.CTkFrame(f, fg_color="transparent")
        btn_r.grid(row=6, column=0, columnspan=2, sticky="e", padx=10, pady=(4,10))
        ctk.CTkButton(btn_r, text="Abbrechen", width=90, height=28,
                       fg_color=COLORS["bg2"], text_color=COLORS["text"],
                       hover_color=COLORS["border"], corner_radius=6,
                       command=lambda: self._form.grid_remove()
                       ).pack(side="left", padx=(0,6))
        ctk.CTkButton(btn_r, text="Speichern", width=100, height=28,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                       corner_radius=6, command=self._save_form
                       ).pack(side="left")
        self._edit_uid = None

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        users = get_users()
        active = self._s.get("active_user_id", 1)
        for i, u in enumerate(users):
            row = ctk.CTkFrame(self._list_frame, corner_radius=8,
                                fg_color=COLORS["primary_light"] if u.id == active
                                else COLORS["bg"],
                                border_width=1,
                                border_color=COLORS["primary"] if u.id == active
                                else COLORS["border"])
            row.grid(row=i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)

            # Aktiv-Indicator
            ctk.CTkLabel(row, text="●" if u.id == active else "○",
                          font=ctk.CTkFont(size=14),
                          text_color=COLORS["primary"] if u.id == active
                          else COLORS["text_muted"]
                          ).grid(row=0, column=0, padx=(10,6), pady=6)
            ctk.CTkLabel(row, text=u.display_name(),
                          font=ctk.CTkFont(size=12, weight="bold" if u.id == active else "normal"),
                          text_color=COLORS["primary"] if u.id == active else COLORS["text"],
                          anchor="w"
                          ).grid(row=0, column=1, sticky="w")

            btn_f = ctk.CTkFrame(row, fg_color="transparent")
            btn_f.grid(row=0, column=2, padx=8)
            ctk.CTkButton(btn_f, text="Wählen", width=70, height=26,
                           fg_color=COLORS["accent"] if u.id != active else COLORS["border"],
                           hover_color=COLORS["accent_dark"], corner_radius=6,
                           font=ctk.CTkFont(size=10),
                           command=lambda uid=u.id: self._activate(uid)
                           ).pack(side="left", padx=2)
            ctk.CTkButton(btn_f, text="✏", width=32, height=26,
                           fg_color=COLORS["primary_light"], text_color=COLORS["primary"],
                           hover_color=COLORS["border"], corner_radius=6,
                           command=lambda uid=u.id: self._edit_user(uid)
                           ).pack(side="left", padx=2)
            if len(users) > 1:
                ctk.CTkButton(btn_f, text="🗑", width=32, height=26,
                               fg_color=COLORS["danger"], hover_color=COLORS["danger_dark"],
                               corner_radius=6,
                               command=lambda uid=u.id: self._del_user(uid)
                               ).pack(side="left", padx=2)

    def _activate(self, uid: int):
        self._s["active_user_id"] = uid
        from config import save_settings
        save_settings(self._s)
        self._refresh_list()
        self._on_change(uid)
        self._set_status(f"✓ Benutzer gewechselt")

    def _new_user(self):
        self._edit_uid = None
        for var in self._fvars.values():
            var.set("")
        self._fvars["tlo"].set("3.9"); self._fvars["thi"].set("7.8")
        self._form.grid()

    def _edit_user(self, uid: int):
        u = get_user(uid)
        if not u: return
        self._edit_uid = uid
        self._fvars["name"].set(u.name); self._fvars["dob"].set(u.dob)
        self._fvars["pid"].set(u.patient_id); self._fvars["doc"].set(u.doctor_name)
        self._fvars["addr"].set(u.doctor_address)
        self._fvars["tlo"].set(str(u.target_low)); self._fvars["thi"].set(str(u.target_high))
        self._form.grid()

    def _save_form(self):
        name = self._fvars["name"].get().strip()
        if not name:
            self._set_status("❌ Name erforderlich", COLORS["danger"]); return
        try:
            tlo = float(self._fvars["tlo"].get().replace(",","."))
            thi = float(self._fvars["thi"].get().replace(",","."))
        except ValueError:
            tlo, thi = 3.9, 7.8
        u = User(self._edit_uid, name, self._fvars["dob"].get(),
                 self._fvars["pid"].get(), self._fvars["doc"].get(),
                 self._fvars["addr"].get(), tlo, thi)
        if self._edit_uid:
            update_user(u)
        else:
            add_user(u)
        self._form.grid_remove()
        self._refresh_list()
        self._set_status("✓ Gespeichert")

    def _del_user(self, uid: int):
        import tkinter.messagebox as mb
        if mb.askyesno("Löschen", "Benutzer und alle Messungen löschen?"):
            if uid == self._s.get("active_user_id", 1):
                self._set_status("❌ Aktiven Benutzer nicht löschbar", COLORS["danger"])
                return
            delete_user(uid)
            self._refresh_list()
            self._set_status("✓ Gelöscht")

    def _set_status(self, msg: str, color: str = None):
        self._status.configure(text=msg,
                                text_color=color or COLORS["normal"])
        self.after(3000, lambda: self._status.configure(text=""))

    def refresh(self):
        self._refresh_list()
