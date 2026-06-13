#!/bin/bash
# ============================================================================
# Zucker Bubi – Analyse-Script
# Direktauswertung der SQLite-Datenbank ohne GUI
# Autor: Mario Peeß / Großenhain  |  mapegr@mailbox.org
# ============================================================================

# Farben
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB="$SCRIPT_DIR/data/gluko.db"
LOG="$SCRIPT_DIR/fehler.log"

# ── Prüfungen ────────────────────────────────────────────────────────────────
if ! command -v sqlite3 &>/dev/null; then
    echo -e "${RED}[FEHLER]${NC} sqlite3 nicht gefunden."
    echo "  → sudo apt install sqlite3  (Debian/Ubuntu/Mint)"
    echo "  → sudo dnf install sqlite   (Fedora)"
    exit 1
fi
if [ ! -f "$DB" ]; then
    echo -e "${RED}[FEHLER]${NC} Datenbank nicht gefunden: $DB"
    echo "  Starten Sie Zucker Bubi einmal, um die Datenbank anzulegen."
    exit 1
fi

# ── Argument: --user N ────────────────────────────────────────────────────────
USER_ID=1
DAYS=90
for i in "$@"; do
    case $i in
        --user=*) USER_ID="${i#*=}" ;;
        --days=*) DAYS="${i#*=}" ;;
        --help|-h)
            echo "Verwendung: $0 [--user=ID] [--days=N]"
            echo "  --user=1   Benutzer-ID (Standard: 1)"
            echo "  --days=90  Analysezeitraum in Tagen (Standard: 90)"
            sqlite3 "$DB" "SELECT id, name FROM users;" | \
                awk -F'|' '{printf "  Benutzer %s: %s\n", $1, $2}'
            exit 0 ;;
    esac
done

SINCE=$(date -d "$DAYS days ago" +%Y-%m-%d 2>/dev/null || \
        date -v-${DAYS}d +%Y-%m-%d 2>/dev/null)

# ── Header ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          🩸  Zucker Bubi – Analyse-Report               ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo -e "   Datum:     $(date '+%d.%m.%Y %H:%M')"
echo -e "   Zeitraum:  letzte ${CYAN}${DAYS}${NC} Tage (seit $SINCE)"

# Benutzer
USER_NAME=$(sqlite3 "$DB" "SELECT name FROM users WHERE id=$USER_ID;" 2>/dev/null)
if [ -z "$USER_NAME" ]; then
    echo -e "   ${RED}Benutzer-ID $USER_ID nicht gefunden.${NC}"
    echo -e "   Verfügbare Benutzer:"
    sqlite3 "$DB" "SELECT id, name FROM users;" | awk -F'|' '{printf "     ID %s: %s\n",$1,$2}'
    exit 1
fi
echo -e "   Benutzer: ${CYAN}${USER_NAME}${NC} (ID: $USER_ID)"
echo ""

# ── Basis-Statistik ──────────────────────────────────────────────────────────
echo -e "${BLUE}── Basis-Statistik ────────────────────────────────────────${NC}"

SQL_BASE="SELECT
    COUNT(*) as n,
    ROUND(AVG(wert_mmol),2) as avg_mmol,
    ROUND(AVG(wert_mmol)*18,0) as avg_mgdl,
    ROUND(MIN(wert_mmol),2) as min_mmol,
    ROUND(MAX(wert_mmol),2) as max_mmol,
    ROUND((AVG(wert_mmol)*18 + 46.7)/28.7, 1) as hba1c_est
FROM messungen
WHERE datum >= '$SINCE' AND user_id = $USER_ID;"

read N AVG_M AVG_D MIN_M MAX_M HBA1C <<< $(sqlite3 "$DB" "$SQL_BASE" | tr '|' ' ')

echo -e "   Messungen:        ${BOLD}$N${NC}"
if [ "$N" -gt 0 ] 2>/dev/null; then
    echo -e "   Ø Wert:           ${BOLD}${AVG_M} mmol/L${NC}  (${AVG_D} mg/dL)"
    echo -e "   Minimum:          ${MIN_M} mmol/L"
    echo -e "   Maximum:          ${MAX_M} mmol/L"

    # HbA1c einfärben
    HBA1C_INT=$(echo "$HBA1C" | cut -d'.' -f1)
    if   [ "$HBA1C_INT" -lt 7 ]; then HBA1C_COL="$GREEN"
    elif [ "$HBA1C_INT" -lt 8 ]; then HBA1C_COL="$YELLOW"
    else                               HBA1C_COL="$RED"; fi
    echo -e "   HbA1c (geschätzt): ${HBA1C_COL}${BOLD}${HBA1C} %${NC}"
else
    echo -e "   ${YELLOW}Keine Daten im gewählten Zeitraum.${NC}"
    exit 0
fi

# ── Zeit im Zielbereich (3.9–7.8 mmol/L) ─────────────────────────────────────
echo ""
echo -e "${BLUE}── Zeit im Zielbereich (3.9–7.8 mmol/L) ──────────────────${NC}"

TIR=$(sqlite3 "$DB" "
SELECT ROUND(100.0 * SUM(CASE WHEN wert_mmol>=3.9 AND wert_mmol<=7.8 THEN 1 ELSE 0 END)/COUNT(*),1)
FROM messungen WHERE datum>='$SINCE' AND user_id=$USER_ID;")
TAR_LO=$(sqlite3 "$DB" "
SELECT ROUND(100.0 * SUM(CASE WHEN wert_mmol<3.9 THEN 1 ELSE 0 END)/COUNT(*),1)
FROM messungen WHERE datum>='$SINCE' AND user_id=$USER_ID;")
TAR_HI=$(sqlite3 "$DB" "
SELECT ROUND(100.0 * SUM(CASE WHEN wert_mmol>7.8 THEN 1 ELSE 0 END)/COUNT(*),1)
FROM messungen WHERE datum>='$SINCE' AND user_id=$USER_ID;")

TIR_INT=$(echo "$TIR" | cut -d'.' -f1)
if   [ "$TIR_INT" -ge 70 ]; then TIR_COL="$GREEN"
elif [ "$TIR_INT" -ge 50 ]; then TIR_COL="$YELLOW"
else                               TIR_COL="$RED"; fi

echo -e "   Im Ziel:  ${TIR_COL}${BOLD}${TIR} %${NC}"
echo -e "   Niedrig:  ${TAR_LO} %  (< 3.9 mmol/L)"
echo -e "   Erhöht:   ${TAR_HI} %  (> 7.8 mmol/L)"

# ASCII-Balken für TIR
BAR_LEN=40
FILLED=$(echo "$TIR_INT * $BAR_LEN / 100" | bc 2>/dev/null || echo 0)
EMPTY=$((BAR_LEN - FILLED))
printf "   ["
printf "${GREEN}%${FILLED}s${NC}" | tr ' ' '█'
printf "%${EMPTY}s" | tr ' ' '░'
printf "]  ${TIR}%%\n"

# ── Verteilung nach Typ ───────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}── Messungen nach Typ ─────────────────────────────────────${NC}"
sqlite3 "$DB" "
SELECT typ, COUNT(*), ROUND(AVG(wert_mmol),2)
FROM messungen WHERE datum>='$SINCE' AND user_id=$USER_ID
GROUP BY typ ORDER BY COUNT(*) DESC;" | \
while IFS='|' read -r typ cnt avg; do
    printf "   %-20s %4s Messungen   Ø %s mmol/L\n" "$typ" "$cnt" "$avg"
done

# ── Wochentags-Analyse ────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}── Durchschnitt nach Wochentag ────────────────────────────${NC}"
sqlite3 "$DB" "
SELECT
    CASE CAST(strftime('%w',datum) AS INTEGER)
        WHEN 0 THEN 'So' WHEN 1 THEN 'Mo' WHEN 2 THEN 'Di'
        WHEN 3 THEN 'Mi' WHEN 4 THEN 'Do' WHEN 5 THEN 'Fr' WHEN 6 THEN 'Sa'
    END as wt,
    ROUND(AVG(wert_mmol),2)
FROM messungen WHERE datum>='$SINCE' AND user_id=$USER_ID
GROUP BY strftime('%w',datum) ORDER BY strftime('%w',datum);" | \
while IFS='|' read -r wt avg; do
    printf "   %s  %s mmol/L\n" "$wt" "$avg"
done

# ── Auffällige Werte ──────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}── Auffällige Werte ───────────────────────────────────────${NC}"

HIGH_N=$(sqlite3 "$DB" "SELECT COUNT(*) FROM messungen WHERE wert_mmol>10.0 AND datum>='$SINCE' AND user_id=$USER_ID;")
LOW_N=$(sqlite3 "$DB"  "SELECT COUNT(*) FROM messungen WHERE wert_mmol<3.9  AND datum>='$SINCE' AND user_id=$USER_ID;")

[ "$HIGH_N" -gt 0 ] && echo -e "   ${RED}⚠  Sehr hoch (>10,0):  $HIGH_N Messungen${NC}" || \
                        echo -e "   ${GREEN}✓  Keine sehr hohen Werte${NC}"
[ "$LOW_N"  -gt 0 ] && echo -e "   ${YELLOW}⚠  Niedrig (<3,9):     $LOW_N Messungen${NC}"  || \
                        echo -e "   ${GREEN}✓  Keine niedrigen Werte${NC}"

# Letzte 5 Messungen
echo ""
echo -e "${BLUE}── Letzte 5 Messungen ─────────────────────────────────────${NC}"
sqlite3 "$DB" "
SELECT datum, uhrzeit, ROUND(wert_mmol,1), typ, notiz
FROM messungen WHERE user_id=$USER_ID
ORDER BY datum DESC, uhrzeit DESC LIMIT 5;" | \
while IFS='|' read -r dat uhr val typ notiz; do
    printf "   %s %s  %s mmol/L  [%s]" "$dat" "$uhr" "$val" "$typ"
    [ -n "$notiz" ] && printf "  %s" "$notiz"
    printf "\n"
done

# ── Fehler-Log ───────────────────────────────────────────────────────────────
if [ -f "$LOG" ] && [ -s "$LOG" ]; then
    ERR_N=$(wc -l < "$LOG")
    echo ""
    echo -e "${BLUE}── Fehler-Log ($ERR_N Einträge) ────────────────────────────${NC}"
    tail -5 "$LOG" | while read -r line; do echo "   $line"; done
fi

echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════════${NC}"
echo -e "  Weitere Optionen: $0 --help"
echo ""
