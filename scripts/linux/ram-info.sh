#!/usr/bin/env bash
# scripts/linux/ram-info.sh — RAM details for Linux
# Platform: Linux ONLY
# Usage: bash ram-info.sh
# ─────────────────────────────────────────────────────────────

[[ "$(uname -s)" != "Linux" ]] && { echo "Linux only." >&2; exit 1; }

_CYAN='\033[0;36m'; _BOLD='\033[1m'; _RST='\033[0m'
_line() { printf '%0.s─' {1..60}; echo ""; }

printf "\n${_CYAN}${_BOLD}RAM Information${_RST}\n"
_line

printf "\n${_CYAN}Memory Usage (free -h):${_RST}\n"
free -h

printf "\n${_CYAN}/proc/meminfo summary:${_RST}\n"
grep -E "^(MemTotal|MemFree|MemAvailable|Cached|SwapTotal|SwapFree):" /proc/meminfo | \
    awk '{printf "  %-20s %8s %s\n", $1, $2, $3}'

if command -v dmidecode &>/dev/null; then
    printf "\n${_CYAN}RAM Hardware (dmidecode):${_RST}\n"
    sudo dmidecode --type 17 2>/dev/null | \
        grep -E "(Size:|Type:|Speed:|Manufacturer:|Part Number:|Form Factor:|Locator:)" | \
        grep -v "No Module" | \
        awk '{printf "  %-20s %s\n", $1, substr($0, index($0,$2))}'
fi
echo ""
