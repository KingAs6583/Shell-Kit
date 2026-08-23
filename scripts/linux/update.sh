#!/usr/bin/env bash
# scripts/linux/update.sh — Full system update for Debian/Ubuntu
# Platform: Linux ONLY
# Usage: bash update.sh
# ─────────────────────────────────────────────────────────────

# Linux guard
if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Error: This script is Linux-only (requires apt)." >&2
    exit 1
fi

_GREEN='\033[0;32m'; _CYAN='\033[0;36m'; _BOLD='\033[1m'; _RST='\033[0m'

line() {
    local col; col=$(tput cols 2>/dev/null || echo 80)
    [ "$col" -gt 100 ] && printf '%0.s─' {1..120} || printf '%0.s─' {1..70}
    echo ""
}

line
printf "${_CYAN}${_BOLD}  System Update — $(date '+%Y-%m-%d %H:%M')${_RST}\n"
line

echo ""
printf "${_CYAN}[1/4] Fetching package lists...${_RST}\n"
sudo apt update

echo ""
printf "${_CYAN}[2/4] Upgrading packages...${_RST}\n"
sudo apt upgrade -y

echo ""
printf "${_CYAN}[3/4] Removing unused packages...${_RST}\n"
sudo apt autoremove -y

echo ""
printf "${_CYAN}[4/4] Cleaning package cache...${_RST}\n"
sudo apt autoclean

line
printf "${_GREEN}${_BOLD}  Update complete!${_RST}\n"
line
