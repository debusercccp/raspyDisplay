#!/usr/bin/env bash
# =============================================================================
# display-switch.sh — Switcha tra i servizi display via systemd
#
# Uso:
#   ./display-switch.sh              # menu interattivo (loop)
#   ./display-switch.sh classic      # passa a display_35.py
#   ./display-switch.sh ascii        # passa a displayASCII_35.py
#   ./display-switch.sh status       # mostra stato attuale
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
SERVICE_CLASSIC="tft-display.service"
SERVICE_ASCII="raspydisplay-ascii.service"

SCRIPT_CLASSIC="/home/noya/raspate/raspyDisplay/display_35.py"
SCRIPT_ASCII="/home/noya/raspate/raspyDisplay/displayASCII_35.py"
ART_FILE="/home/noya/Progettini/radioHead/thebends.txt"

SYSTEMD_DIR="/etc/systemd/system"

# =============================================================================
# COLORI
# =============================================================================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# =============================================================================
# HELPERS
# =============================================================================
info() { echo -e "${CYAN}[*]${RESET} $*"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $*"; }
warn() { echo -e "${YELLOW}[!]${RESET} $*"; }
die()  { echo -e "${RED}[✗]${RESET} $*" >&2; exit 1; }

# =============================================================================
# GENERA I FILE .service SE NON ESISTONO
# =============================================================================
create_services() {
    local svc_classic="$SYSTEMD_DIR/$SERVICE_CLASSIC"
    if [[ ! -f "$svc_classic" ]]; then
        info "Creo $svc_classic ..."
        sudo tee "$svc_classic" > /dev/null <<EOF
[Unit]
Description=RaspyDisplay — Dashboard TFT (display_35.py)
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User=noya
WorkingDirectory=/home/noya/raspate/raspyDisplay
ExecStart=/usr/bin/python3 ${SCRIPT_CLASSIC}
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        ok "Creato $SERVICE_CLASSIC"
    fi

    local svc_ascii="$SYSTEMD_DIR/$SERVICE_ASCII"
    if [[ ! -f "$svc_ascii" ]]; then
        info "Creo $svc_ascii ..."
        sudo tee "$svc_ascii" > /dev/null <<EOF
[Unit]
Description=RaspyDisplay — ASCII Art TFT (displayASCII_35.py)
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User=noya
WorkingDirectory=/home/noya/raspate/raspyDisplay
ExecStart=/usr/bin/python3 ${SCRIPT_ASCII} --art ${ART_FILE}
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        ok "Creato $SERVICE_ASCII"
    fi

    sudo systemctl daemon-reload
}

# =============================================================================
# STATUS
# =============================================================================
show_status() {
    echo -e "\n${BOLD}── Stato servizi display ──────────────────────────────${RESET}"
    for svc in "$SERVICE_CLASSIC" "$SERVICE_ASCII"; do
        local active enabled
        active=$(sudo systemctl is-active  "$svc" 2>/dev/null || echo "unknown")
        enabled=$(sudo systemctl is-enabled "$svc" 2>/dev/null || echo "unknown")
        if [[ "$active" == "active" ]]; then
            echo -e "  ${GREEN}●${RESET} ${BOLD}${svc}${RESET}  [${GREEN}${active}${RESET}] [${enabled}]"
        else
            echo -e "  ${RED}●${RESET} ${svc}  [${RED}${active}${RESET}] [${enabled}]"
        fi
    done
    echo -e "${BOLD}───────────────────────────────────────────────────────${RESET}\n"
}

# =============================================================================
# SWITCH
# =============================================================================
switch_to() {
    local target="$1"
    local stop_svc start_svc

    case "$target" in
        classic) stop_svc="$SERVICE_ASCII";   start_svc="$SERVICE_CLASSIC" ;;
        ascii)   stop_svc="$SERVICE_CLASSIC"; start_svc="$SERVICE_ASCII"   ;;
        *)       die "Target sconosciuto: '$target'. Usa 'classic' o 'ascii'." ;;
    esac

    create_services

    local currently_active
    currently_active=$(sudo systemctl is-active "$stop_svc" 2>/dev/null || echo "inactive")
    if [[ "$currently_active" == "active" ]]; then
        info "Fermo $stop_svc ..."
        sudo systemctl stop "$stop_svc"
        ok "Fermato."
    else
        info "$stop_svc non era attivo, skip."
    fi

    info "Avvio $start_svc ..."
    sudo systemctl start "$start_svc"
    sleep 1

    local new_state
    new_state=$(sudo systemctl is-active "$start_svc" 2>/dev/null || echo "failed")
    if [[ "$new_state" == "active" ]]; then
        ok "Switched → ${BOLD}${target}${RESET} (${start_svc} attivo)"
    else
        warn "Qualcosa è andato storto. Controlla con: sudo journalctl -u $start_svc -n 30"
    fi
}

# =============================================================================
# ENABLE / DISABLE
# =============================================================================
enable_autostart() {
    local svc
    case "$1" in
        classic) svc="$SERVICE_CLASSIC" ;;
        ascii)   svc="$SERVICE_ASCII"   ;;
        *)       die "Usa 'classic' o 'ascii'." ;;
    esac
    create_services
    sudo systemctl enable "$svc"
    ok "Autostart abilitato per $svc"
}

disable_autostart() {
    local svc
    case "$1" in
        classic) svc="$SERVICE_CLASSIC" ;;
        ascii)   svc="$SERVICE_ASCII"   ;;
        *)       die "Usa 'classic' o 'ascii'." ;;
    esac
    sudo systemctl disable "$svc" 2>/dev/null || true
    ok "Autostart disabilitato per $svc"
}

# =============================================================================
# MENU INTERATTIVO — loop finché non si esce con q
# =============================================================================
interactive_menu() {
    while true; do
        clear
        echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
        echo -e "${BOLD}║      display-switch — raspyDisplay   ║${RESET}"
        echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"

        show_status

        echo -e "  ${CYAN}1)${RESET} Passa a  ${BOLD}Classic${RESET}   (display_35.py)"
        echo -e "  ${CYAN}2)${RESET} Passa a  ${BOLD}ASCII${RESET}     (displayASCII_35.py)"
        echo -e "  ${CYAN}3)${RESET} Ferma entrambi"
        echo -e "  ${CYAN}4)${RESET} Abilita autostart Classic"
        echo -e "  ${CYAN}5)${RESET} Abilita autostart ASCII"
        echo -e "  ${CYAN}6)${RESET} Disabilita autostart entrambi"
        echo -e "  ${CYAN}7)${RESET} Log Classic  (ultimi 40)"
        echo -e "  ${CYAN}8)${RESET} Log ASCII    (ultimi 40)"
        echo -e "  ${CYAN}q)${RESET} Esci\n"

        read -rp "Scelta: " choice
        echo

        case "$choice" in
            1) switch_to classic ;;
            2) switch_to ascii ;;
            3)
                info "Fermo entrambi..."
                sudo systemctl stop "$SERVICE_CLASSIC" "$SERVICE_ASCII" 2>/dev/null || true
                ok "Fermati."
                ;;
            4) enable_autostart classic ;;
            5) enable_autostart ascii ;;
            6) disable_autostart classic; disable_autostart ascii ;;
            7) sudo journalctl -u "$SERVICE_CLASSIC" -n 40 --no-pager ;;
            8) sudo journalctl -u "$SERVICE_ASCII"   -n 40 --no-pager ;;
            q|Q) echo "Uscita."; exit 0 ;;
            *) warn "Scelta non valida." ;;
        esac

        echo
        read -rp "Premi invio per continuare..." _
    done
}

# =============================================================================
# MAIN
# =============================================================================
case "${1:-}" in
    classic|ascii) switch_to "$1" ;;
    status)        create_services; show_status ;;
    enable)        enable_autostart "${2:-classic}" ;;
    disable)       disable_autostart "${2:-classic}" ;;
    --help|-h)
        echo "Uso: $0 [classic|ascii|status|enable <target>|disable <target>]"
        echo "     $0   → menu interattivo"
        ;;
    "") interactive_menu ;;
    *)  die "Argomento sconosciuto: '$1'. Usa --help." ;;
esac
