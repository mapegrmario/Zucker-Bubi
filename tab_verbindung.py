# tab_verbindung.py – Verbindungsassistent (USB pyusb + BT direkte MAC-Verbindung)
import customtkinter as ctk
import tkinter.filedialog as fd
import subprocess, threading
from config import COLORS, save_settings
from usb_manager import (is_pyusb_available, is_udev_configured, check_usb_device,
                          setup_udev_rules, read_usb, import_csv, UDEV_PATH)
from bluetooth_manager import start_sync, scan_devices
import lang as L


class TabVerbindung(ctk.CTkScrollableFrame):
    def __init__(self, parent, settings: dict, refresh_cb):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self._s = settings
        self._refresh = refresh_cb
        self._build()

    def _uid(self): return self._s.get("active_user_id", 1)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="🔌  Verbindungsassistent",
                      font=ctk.CTkFont(size=18, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(self,
                      text="USB-Kabel oder Bluetooth – importieren Sie Ihre Messwerte direkt.",
                      font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]
                      ).grid(row=1, column=0, sticky="w", padx=26, pady=(0, 12))
        self._build_usb_section(2)
        self._build_bt_section(3)
        self._build_csv_section(4)

    # ── Hilfsmethode ──────────────────────────────────────────────────────────
    def _make_card(self, title: str, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, corner_radius=14, fg_color=COLORS["card"],
                             border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=6)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=title,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=COLORS["primary"]
                      ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).grid(
            row=1, column=0, sticky="ew", padx=12, pady=(0, 2))
        return card

    # ── USB ───────────────────────────────────────────────────────────────────
    def _build_usb_section(self, row: int):
        card = self._make_card("🔌  USB-Kabel (Accu-Chek Guide / Relion)", row)
        status_f = ctk.CTkFrame(card, fg_color="transparent")
        status_f.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 0))
        self._usb_pyusb_lbl = ctk.CTkLabel(status_f, text="", font=ctk.CTkFont(size=11))
        self._usb_pyusb_lbl.pack(anchor="w", pady=1)
        self._usb_udev_lbl  = ctk.CTkLabel(status_f, text="", font=ctk.CTkFont(size=11))
        self._usb_udev_lbl.pack(anchor="w", pady=1)
        self._usb_dev_lbl   = ctk.CTkLabel(status_f, text="", font=ctk.CTkFont(size=11))
        self._usb_dev_lbl.pack(anchor="w", pady=1)

        ctk.CTkLabel(card,
                      text="Anleitung:\n"
                           "1. Gerät per USB-Kabel anschließen\n"
                           "2. Am Gerät: Menü → PC-Verbindung → 'Datenübertragung'\n"
                           "3. '🔧 udev einrichten' (einmalig, erfordert sudo)\n"
                           "4. Gerät abstecken und neu einstecken\n"
                           "5. '📥 USB auslesen' – fertig!",
                      font=ctk.CTkFont(size=11), justify="left",
                      text_color=COLORS["text"], anchor="w"
                      ).grid(row=3, column=0, sticky="w", padx=20, pady=(8, 4))

        pw_frame = ctk.CTkFrame(card, corner_radius=8, fg_color=COLORS["bg"],
                                 border_width=1, border_color=COLORS["border"])
        pw_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 2))
        pw_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(pw_frame, text="🔑  sudo-Passwort (nur für udev-Einrichtung):",
                      font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"]
                      ).grid(row=0, column=0, padx=(10, 6), pady=6)
        self._sudo_pw = ctk.CTkEntry(pw_frame, show="●", height=28,
                                      placeholder_text="Leer lassen wenn passwortlos",
                                      font=ctk.CTkFont(size=11), fg_color=COLORS["card"])
        self._sudo_pw.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=6)

        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=5, column=0, sticky="w", padx=16, pady=(8, 6))
        self._usb_read_btn = None
        for txt, fg, tc, cmd in [
            ("🔍 Status",          COLORS["bg2"],     COLORS["text"],  self._usb_check),
            ("🔧 udev einrichten", COLORS["bg2"],     COLORS["text"],  self._udev_setup),
            ("📥 USB auslesen",    COLORS["primary"], "white",         self._usb_read),
        ]:
            b = ctk.CTkButton(btn_f, text=txt, height=32, corner_radius=8,
                               fg_color=fg, text_color=tc,
                               hover_color=COLORS["primary_dark"] if tc == "white"
                               else COLORS["border"],
                               font=ctk.CTkFont(size=11), command=cmd)
            b.pack(side="left", padx=(0, 6))
            if txt.startswith("📥"): self._usb_read_btn = b

        self._usb_result = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11),
                                         text_color=COLORS["normal"],
                                         wraplength=680, justify="left")
        self._usb_result.grid(row=6, column=0, sticky="w", padx=20, pady=(4, 14))

    # ── Bluetooth ─────────────────────────────────────────────────────────────
    def _build_bt_section(self, row: int):
        card = self._make_card("🔷  Bluetooth BLE (Accu-Chek Guide / kompatibel)", row)

        # MAC-Adresse Eingabe
        mac_frame = ctk.CTkFrame(card, corner_radius=8, fg_color=COLORS["bg"],
                                  border_width=1, border_color=COLORS["border"])
        mac_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 4))
        mac_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(mac_frame, text="📡  MAC-Adresse:",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color=COLORS["text"]
                      ).grid(row=0, column=0, padx=(12, 8), pady=8)
        self._mac_entry = ctk.CTkEntry(
            mac_frame, height=30, font=ctk.CTkFont(size=12, family="monospace"),
            fg_color=COLORS["card"], placeholder_text="XX:XX:XX:XX:XX:XX")
        self._mac_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        saved_mac = self._s.get("bt_mac", "")
        if saved_mac:
            self._mac_entry.insert(0, saved_mac)
        ctk.CTkButton(mac_frame, text="💾 Speichern", width=90, height=30,
                       fg_color=COLORS["accent"], hover_color=COLORS["accent_dark"],
                       text_color="white", corner_radius=8,
                       font=ctk.CTkFont(size=11),
                       command=self._save_mac
                       ).grid(row=0, column=2, padx=(0, 12), pady=8)

        # Gerätliste (Scan-Ergebnis)
        list_frame = ctk.CTkFrame(card, fg_color="transparent")
        list_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 4))
        list_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(list_frame,
                      text="Gefundene Geräte (nach Scan):",
                      font=ctk.CTkFont(size=10),
                      text_color=COLORS["text_muted"]
                      ).grid(row=0, column=0, sticky="w", padx=4)
        self._device_var = ctk.StringVar(value="")
        self._device_menu = ctk.CTkOptionMenu(
            list_frame, variable=self._device_var,
            values=["– noch kein Scan –"], width=420, height=30,
            fg_color=COLORS["bg2"], button_color=COLORS["primary"],
            button_hover_color=COLORS["primary_dark"],
            font=ctk.CTkFont(size=11),
            command=self._on_device_select)
        self._device_menu.grid(row=1, column=0, sticky="w", padx=4, pady=(2, 4))

        ctk.CTkLabel(card,
                      text="Anleitung:\n"
                           "1. '🔍 Gerät suchen' → Bluetooth am Gerät einschalten und warten\n"
                           "2. Gerät aus der Liste wählen → MAC wird automatisch eingetragen\n"
                           "3. '⟳ Synchronisieren' klicken\n"
                           "4. Pairing-Dialog am Desktop bestätigen (erscheint beim ersten Mal)\n"
                           "5. Gerät sendet alle Messwerte automatisch (ca. 60 Sek.)",
                      font=ctk.CTkFont(size=11), justify="left",
                      text_color=COLORS["text"], anchor="w"
                      ).grid(row=4, column=0, sticky="w", padx=20, pady=(4, 6))

        # Diagnose-Labels
        self._bt_diag: dict = {}
        diag_f = ctk.CTkFrame(card, fg_color="transparent")
        diag_f.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 4))
        for key, lbl in [("bt_service", "Bluetooth-Dienst aktiv"),
                          ("bt_bleak",   "bleak-Bibliothek installiert")]:
            w = ctk.CTkLabel(diag_f, text=f"○  {lbl}",
                              font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"])
            w.pack(anchor="w", padx=8, pady=1)
            self._bt_diag[key] = w
        # Duplikat-Schutz – immer aktiv
        ctk.CTkLabel(diag_f,
                      text="✓  Duplikat-Schutz aktiv: nur neue Datum+Uhrzeit-Kombinationen werden importiert",
                      font=ctk.CTkFont(size=11), text_color=COLORS["normal"]
                      ).pack(anchor="w", padx=8, pady=1)

        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=6, column=0, sticky="w", padx=16, pady=(4, 6))
        self._bt_scan_btn = ctk.CTkButton(
            btn_f, text="🔍 Gerät suchen", height=32, width=140,
            fg_color=COLORS["bg2"], text_color=COLORS["text"],
            hover_color=COLORS["border"], corner_radius=8,
            font=ctk.CTkFont(size=11), command=self._bt_scan)
        self._bt_scan_btn.pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_f, text="🔧 Diagnose", height=32, width=110,
                       fg_color=COLORS["bg2"], text_color=COLORS["text"],
                       hover_color=COLORS["border"], corner_radius=8,
                       font=ctk.CTkFont(size=11),
                       command=self._bt_diagnose).pack(side="left", padx=(0, 8))
        self._bt_sync_btn = ctk.CTkButton(
            btn_f, text="⟳  Synchronisieren", height=32, width=170,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
            corner_radius=8, font=ctk.CTkFont(size=11), command=self._bt_sync)
        self._bt_sync_btn.pack(side="left")

        self._bt_result = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11),
                                        text_color=COLORS["normal"],
                                        wraplength=680, justify="left")
        self._bt_result.grid(row=7, column=0, sticky="w", padx=20, pady=(4, 14))

    # ── CSV ───────────────────────────────────────────────────────────────────
    def _build_csv_section(self, row: int):
        card = self._make_card("📁  CSV-Import (universell)", row)
        ctk.CTkLabel(card,
                      text="Importiert CSV-Dateien (Accu-Chek Connect, MySugr, FreeStyle LibreView u.a.)\n"
                           "Bereits vorhandene Messungen werden automatisch übersprungen.",
                      font=ctk.CTkFont(size=11), justify="left",
                      text_color=COLORS["text"], anchor="w"
                      ).grid(row=2, column=0, sticky="w", padx=20, pady=(8, 4))
        btn_f = ctk.CTkFrame(card, fg_color="transparent")
        btn_f.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 12))
        ctk.CTkButton(btn_f, text="📂 CSV-Datei wählen", height=32, width=170,
                       fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"],
                       corner_radius=8, font=ctk.CTkFont(size=11),
                       command=self._csv_import).pack(side="left", padx=(0, 8))
        self._csv_result = ctk.CTkLabel(btn_f, text="", font=ctk.CTkFont(size=11),
                                         text_color=COLORS["normal"])
        self._csv_result.pack(side="left")

    # ── USB Logik ─────────────────────────────────────────────────────────────
    def _usb_check(self):
        ok_pyusb = is_pyusb_available()
        ok_udev  = is_udev_configured()
        dev      = check_usb_device()

        def _lbl(ok, y, n): return (f"✓  {y}", COLORS["normal"]) if ok \
            else (f"✗  {n}", COLORS["danger"])

        t, c = _lbl(ok_pyusb, "pyusb installiert",
                    "pyusb fehlt → install.sh ausführen")
        self._usb_pyusb_lbl.configure(text=t, text_color=c)
        t, c = _lbl(ok_udev, f"udev-Regeln vorhanden ({UDEV_PATH.name})",
                    "udev-Regeln fehlen → '🔧 udev einrichten' klicken")
        self._usb_udev_lbl.configure(text=t, text_color=c)
        self._usb_dev_lbl.configure(
            text=f"✓  Gerät: {dev}" if dev else
                 "○  Kein USB-Gerät erkannt (Kabel + Übertragungsmodus prüfen)",
            text_color=COLORS["normal"] if dev else COLORS["text_muted"])

    def _udev_setup(self):
        self._usb_result.configure(text="⟳  Schreibe udev-Regeln …",
                                    text_color=COLORS["text_muted"])
        pw = self._sudo_pw.get().strip()
        def _run():
            ok, msg = setup_udev_rules(pw)
            full = ("✓  udev-Regeln gesetzt\n→  Gerät abstecken und NEU einstecken!"
                    if ok else f"❌  {msg}")
            self.after(0, lambda: self._usb_result.configure(
                text=full, text_color=COLORS["normal"] if ok else COLORS["danger"]))
            if ok: self.after(0, self._usb_check)
        threading.Thread(target=_run, daemon=True).start()

    def _usb_read(self):
        if self._usb_read_btn:
            self._usb_read_btn.configure(state="disabled", text="⏳ Lese …")
        read_usb(lambda msg, ok: self.after(0, lambda: self._on_usb_read(msg, ok)),
                 user_id=self._uid())

    def _on_usb_read(self, msg, ok):
        if self._usb_read_btn:
            self._usb_read_btn.configure(state="normal", text="📥 USB auslesen")
        col = COLORS["normal"] if ok else (COLORS["warning"] if ok is None
                                            else COLORS["danger"])
        self._usb_result.configure(text=msg, text_color=col)
        if ok: self._refresh()

    # ── Bluetooth Logik ───────────────────────────────────────────────────────
    def _save_mac(self):
        mac = self._mac_entry.get().strip().upper()
        self._s["bt_mac"] = mac
        save_settings(self._s)
        self._bt_result.configure(
            text=f"✓  MAC gespeichert: {mac}" if mac else "MAC gelöscht",
            text_color=COLORS["normal"])

    def _on_device_select(self, choice: str):
        """Trägt MAC aus Dropdown in das Eingabefeld ein."""
        if " – " in choice:
            mac = choice.split(" – ")[0].strip()
            self._mac_entry.delete(0, "end")
            self._mac_entry.insert(0, mac)

    def _bt_scan(self):
        self._bt_scan_btn.configure(state="disabled", text="⟳ Scanne …")
        self._bt_result.configure(text="🔍  Scan läuft (10 Sek.) …",
                                   text_color=COLORS["text_muted"])
        def _on_result(devices: list):
            self.after(0, lambda: self._on_scan_done(devices))
        scan_devices(_on_result)

    def _on_scan_done(self, devices: list):
        self._bt_scan_btn.configure(state="normal", text="🔍 Gerät suchen")
        if not devices:
            self._bt_result.configure(
                text="○  Keine Glucose-Geräte gefunden.\n"
                     "→  Bluetooth am Gerät einschalten (Taste halten) und erneut scannen.",
                text_color=COLORS["warning"]); return
        labels = [f"{mac} – {name}" for mac, name in devices]
        self._device_menu.configure(values=labels)
        self._device_var.set(labels[0])
        self._on_device_select(labels[0])
        self._bt_result.configure(
            text=f"✓  {len(devices)} Gerät(e) gefunden. MAC eingetragen – '💾 Speichern' klicken.",
            text_color=COLORS["normal"])

    def _bt_diagnose(self):
        def chk(key, ok, yes, no):
            sym = "✓" if ok else "✗"
            self._bt_diag[key].configure(
                text=f"{sym}  {yes if ok else no}",
                text_color=COLORS["normal"] if ok else COLORS["danger"])

        # BT-Dienst prüfen: 3 Methoden, cross-distro (systemd, SysV, OpenRC)
        import os
        bt_ok = False
        bt_fail = "Bluetooth inaktiv – bluetoothctl / rfkill prüfen"

        # Methode 1: /sys/class/bluetooth/ – zuverlässigste Prüfung (hardware-unabhängig)
        try:
            hci = [d for d in os.listdir("/sys/class/bluetooth/") if d.startswith("hci")]
            if hci:
                bt_ok = True
        except Exception:
            pass

        # Methode 2: bluetoothctl show (falls sysfs leer)
        if not bt_ok:
            try:
                r = subprocess.run(["bluetoothctl", "show"],
                                   capture_output=True, text=True, timeout=5)
                if "Controller" in r.stdout:
                    bt_ok = True
            except Exception:
                pass

        # Methode 3: hciconfig als letzter Fallback
        if not bt_ok:
            try:
                r = subprocess.run(["hciconfig"], capture_output=True, text=True, timeout=5)
                if "hci" in r.stdout:
                    bt_ok = True
            except Exception:
                pass

        chk("bt_service", bt_ok, "Bluetooth aktiv", bt_fail)

        try:
            import bleak  # noqa
            chk("bt_bleak", True, "bleak installiert", "")
        except ImportError:
            chk("bt_bleak", False, "", "bleak fehlt – install.sh ausführen")

    def _bt_sync(self):
        mac = self._mac_entry.get().strip().upper()
        if mac:
            self._s["bt_mac"] = mac
        self._bt_sync_btn.configure(state="disabled", text="⟳ Verbinde …")
        self._bt_result.configure(text="⟳  Starte Verbindung …",
                                   text_color=COLORS["text_muted"])
        start_sync(self._s, callback=lambda ok, msg:
                   self.after(0, lambda: self._on_bt(ok, msg)))

    def _on_bt(self, ok, msg):
        # Nur bei finalem Ergebnis (ok=True/False) Button wieder freigeben
        if ok is not None:
            self._bt_sync_btn.configure(state="normal", text="⟳  Synchronisieren")
        col = (COLORS["normal"]    if ok is True  else
               COLORS["danger"]    if ok is False else
               COLORS["text_muted"])          # ok=None → Fortschritt
        self._bt_result.configure(text=msg, text_color=col)
        if ok is True:
            self._refresh()

    # ── CSV ───────────────────────────────────────────────────────────────────
    def _csv_import(self):
        path = fd.askopenfilename(filetypes=[("CSV", "*.csv"), ("Alle", "*.*")])
        if not path: return
        try:
            imp, skip = import_csv(path, self._uid(), self._s.get("unit", "mmol/L"))
            self._csv_result.configure(
                text=f"✓  {imp} importiert, {skip} übersprungen",
                text_color=COLORS["normal"])
            self._refresh()
        except Exception as e:
            self._csv_result.configure(text=f"❌  {e}", text_color=COLORS["danger"])

    def on_show(self):
        self._bt_diagnose()
        self._usb_check()
