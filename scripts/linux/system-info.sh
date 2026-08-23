#!/usr/bin/env bash
# scripts/linux/system-info.sh — Hardware info via dmidecode
# Platform: Linux ONLY
# Usage: bash system-info.sh [type]
#   Types: 1=system 4=cpu 17=ram 2=baseboard 3=chassis 0=bios
# ─────────────────────────────────────────────────────────────

[[ "$(uname -s)" != "Linux" ]] && { echo "Linux only." >&2; exit 1; }

_CYAN='\033[0;36m'; _BOLD='\033[1m'; _RST='\033[0m'
type="${1:-1}"

printf "\n${_CYAN}${_BOLD}System Info (dmidecode type ${type})${_RST}\n"
printf '%0.s─' {1..60}; echo ""

if ! command -v dmidecode &>/dev/null; then
    echo "dmidecode not found. Install: sudo apt install dmidecode"
    exit 1
fi

sudo dmidecode --type "$type"
echo ""
echo "Other types: 0=bios  1=system  2=baseboard  3=chassis  4=cpu  17=ram"
