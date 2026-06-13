#!/bin/bash
# ============================================================================
# Zucker Bubi – Installationsscript
# Unterstützt: Ubuntu, Linux Mint, LMDE, Fedora, openSUSE, Arch, MX Linux
# Autor: Mario Peeß / Großenhain  |  mapegr@mailbox.org
# ============================================================================
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[FEHLER]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Zucker Bubi"
INSTALL_DIR="$HOME/ZuckerBubi"
BACKUP_DIR="$HOME/ZuckerBubi_Backup_$(date +%Y%m%d_%H%M%S)"

# ── Distro erkennen ──────────────────────────────────────────────────────────
detect_distro() {
    if   command -v apt    &>/dev/null; then echo "apt"
    elif command -v dnf    &>/dev/null; then echo "dnf"
    elif command -v zypper &>/dev/null; then echo "zypper"
    elif command -v pacman &>/dev/null; then echo "pacman"
    else echo "unknown"; fi
}

# ── Systemabhängigkeiten ─────────────────────────────────────────────────────
install_deps() {
    local PM=$1
    info "Installiere Systemabhängigkeiten ($PM) …"
    case $PM in
        apt)
            sudo apt update -qq
            sudo apt install -y \
                python3 python3-venv python3-pip python3-tk \
                python3-usb libusb-1.0-0 libusb-1.0-0-dev \
                libbluetooth-dev bluez \
                sqlite3 2>/dev/null || true ;;
        dnf)
            sudo dnf install -y \
                python3 python3-pip python3-tkinter \
                python3-pyusb libusb1 libusb1-devel \
                bluez bluez-libs-devel \
                sqlite 2>/dev/null || true ;;
        zypper)
            sudo zypper install -y \
                python3 python3-pip python3-tk \
                python3-pyusb libusb-1_0-0 libusb-1_0-devel \
                bluez libbluetooth3 \
                sqlite3 2>/dev/null || true ;;
        pacman)
            sudo pacman -Sy --noconfirm \
                python python-pip tk \
                python-pyusb libusb \
                bluez \
                sqlite 2>/dev/null || true ;;
    esac
    ok "Systemabhängigkeiten installiert"
}

# ── udev-Regeln für USB-Messgeräte ───────────────────────────────────────────
setup_udev() {
    info "Richte udev-Regeln für Accu-Chek USB + Bluetooth ein …"
    sudo bash -c 'cat > /etc/udev/rules.d/99-glucose-usb.rules << EOF
# Zucker Bubi – Accu-Chek USB Messgeräte (Roche / Relion)
SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d5", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d7", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="173a", ATTR{idProduct}=="21d8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04b4", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0a21", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="22b9", MODE="0666", GROUP="plugdev"
EOF' 2>/dev/null || warn "udev USB-Regeln konnten nicht gesetzt werden"
    sudo udevadm control --reload-rules 2>/dev/null || true
    sudo udevadm trigger               2>/dev/null || true
    sudo usermod -aG plugdev  "$USER"  2>/dev/null || true
    sudo usermod -aG bluetooth "$USER" 2>/dev/null || true
    ok "udev-Regeln gesetzt + Gruppen konfiguriert"
    warn "→ Abmelden und neu anmelden damit Gruppenrechte wirken!"
}

# ── Python-Umgebung und Pakete ───────────────────────────────────────────────
install_venv() {
    local TARGET="$1"
    info "Richte Python venv ein …"
    python3 -m venv "$TARGET/venv"
    "$TARGET/venv/bin/pip" install --upgrade pip -q
    "$TARGET/venv/bin/pip" install -r "$TARGET/requirements.txt" -q
    ok "Python-Pakete installiert (inkl. pyusb + bleak)"
}

# ── pyusb über pip sicherstellen (falls Systempaket fehlt) ───────────────────
ensure_pyusb() {
    local TARGET="$1"
    if ! "$TARGET/venv/bin/python" -c "import usb.core" &>/dev/null; then
        info "pyusb im venv nicht gefunden – installiere …"
        "$TARGET/venv/bin/pip" install pyusb -q
        ok "pyusb installiert"
    fi
}

# ── Start-Script ─────────────────────────────────────────────────────────────
create_start_script() {
    local TARGET="$1"
    cat > "$TARGET/start.sh" << EOF
#!/bin/bash
cd "$TARGET"
venv/bin/python main.py "\$@"
EOF
    chmod +x "$TARGET/start.sh"
}

# ── Desktop-Verknüpfung ──────────────────────────────────────────────────────
create_desktop() {
    local TARGET="$1"
    info "Erstelle Desktop-Verknüpfung …"
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/zucker-bubi.desktop" << EOF
[Desktop Entry]
Name=Zucker Bubi
GenericName=Blutzucker Manager
Comment=Blutzucker-Dokumentation und Auswertung
Exec=$TARGET/start.sh
Icon=$TARGET/Zucker_Bubi.png
Terminal=false
Type=Application
Categories=Health;Medical;
StartupWMClass=zucker-bubi
EOF
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    ok "Desktop-Verknüpfung erstellt"
}

# ── Programmdateien kopieren (KEINE Daten überschreiben) ─────────────────────
copy_program_files() {
    local SRC="$1"
    local DST="$2"
    info "Kopiere Programmdateien nach $DST …"
    mkdir -p "$DST"
    cp "$SRC"/*.py  "$DST/" 2>/dev/null || true
    cp "$SRC"/*.md  "$DST/" 2>/dev/null || true
    cp "$SRC"/*.txt "$DST/" 2>/dev/null || true
    cp "$SRC"/*.sh  "$DST/" 2>/dev/null || true
    cp "$SRC/Zucker_Bubi.png" "$DST/" 2>/dev/null || true
    mkdir -p "$DST/data"
    # Altes C++-Binary entfernen (nicht mehr benötigt – pyusb übernimmt)
    [ -f "$DST/accuchek_bin" ] && rm -f "$DST/accuchek_bin" && \
        info "Altes accuchek_bin entfernt (pyusb-Implementierung aktiv)"
    ok "Programmdateien kopiert"
}

# ── Frische Installation ─────────────────────────────────────────────────────
fresh_install() {
    copy_program_files "$SCRIPT_DIR" "$INSTALL_DIR"
    install_venv "$INSTALL_DIR"
    ensure_pyusb "$INSTALL_DIR"
    create_start_script "$INSTALL_DIR"
    create_desktop "$INSTALL_DIR"
}

# ── Update (Daten bleiben erhalten) ──────────────────────────────────────────
do_update() {
    info "Update-Modus: Daten und Einstellungen bleiben erhalten"

    if [ -d "$INSTALL_DIR/data" ] && [ "$(ls -A "$INSTALL_DIR/data" 2>/dev/null)" ]; then
        info "Sichere Daten nach $BACKUP_DIR/data …"
        mkdir -p "$BACKUP_DIR"
        cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/" 2>/dev/null || true
        ok "Datensicherung: $BACKUP_DIR/data"
    fi

    copy_program_files "$SCRIPT_DIR" "$INSTALL_DIR"

    if [ -f "$INSTALL_DIR/venv/bin/python" ]; then
        info "Aktualisiere Python-Pakete …"
        "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
        ok "Python-Pakete aktualisiert"
    else
        install_venv "$INSTALL_DIR"
    fi
    ensure_pyusb "$INSTALL_DIR"
    create_start_script "$INSTALL_DIR"
    create_desktop "$INSTALL_DIR"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Hauptablauf
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║         Zucker Bubi – Installation               ║${NC}"
echo -e "${BOLD}║         Autor: Mario Peeß / Großenhain           ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

PM=$(detect_distro)
if [ "$PM" = "unknown" ]; then
    warn "Paketmanager nicht erkannt – überspringe System-Deps"
else
    install_deps "$PM"
fi

# ── Installationsart ─────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  Bestehende Installation gefunden:               ║${NC}"
    echo -e "${CYAN}║  $INSTALL_DIR${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  [1] Update   – Programmdateien erneuern, Daten BEHALTEN (empfohlen)"
    echo "  [2] Neuinstallation – Alles löschen und neu installieren"
    echo "  [3] Abbrechen"
    echo ""
    read -p "Wahl [1/2/3]: " -n 1 -r CHOICE; echo ""
    case $CHOICE in
        1) do_update ;;
        2)
            warn "ACHTUNG: Alle Daten werden gelöscht!"
            read -p "Wirklich fortfahren? (j/n): " -n 1 -r CONFIRM; echo
            if [[ $CONFIRM =~ ^[Jj]$ ]]; then
                if [ -d "$INSTALL_DIR/data" ]; then
                    mkdir -p "$BACKUP_DIR"
                    cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/" 2>/dev/null || true
                    ok "Daten gesichert: $BACKUP_DIR"
                fi
                rm -rf "$INSTALL_DIR"
                fresh_install
            else
                info "Abgebrochen."; exit 0
            fi ;;
        *) info "Abgebrochen."; exit 0 ;;
    esac
else
    fresh_install
fi

setup_udev

# ── Abschluss ────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  ${GREEN}✓  Installation abgeschlossen!${NC}${BOLD}                 ║${NC}"
echo -e "${BOLD}║                                                  ║${NC}"
echo -e "${BOLD}║  USB:       Gerät einstecken + '📥 USB auslesen' ║${NC}"
echo -e "${BOLD}║  Bluetooth: Koppeln + 'Jetzt synchronisieren'   ║${NC}"
echo -e "${BOLD}║                                                  ║${NC}"
echo -e "${BOLD}║  Start: ${CYAN}$INSTALL_DIR/start.sh${NC}${BOLD}    ║${NC}"
echo -e "${BOLD}║  Oder:  'Zucker Bubi' im Menü suchen            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

read -p "Jetzt starten? (j/n): " -n 1 -r; echo
[[ $REPLY =~ ^[Jj]$ ]] && "$INSTALL_DIR/start.sh"
