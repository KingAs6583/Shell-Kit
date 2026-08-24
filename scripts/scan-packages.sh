#!/usr/bin/env bash
# scan-packages.sh -- Scan bash history for installed packages
# Zero startup delay: runs in background. Use pkgscan to force rescan.

set -uo pipefail

FOREGROUND=false

# Handle --cleanup flag
if [[ "${1:-}" == "--cleanup" ]]; then
    CACHE_FILE="${HOME}/.cache/installed-packages.txt"
    if [ -f "$CACHE_FILE" ]; then
        rm -f "$CACHE_FILE"
        echo "Deleted package list cache: $CACHE_FILE"
    else
        echo "No package list cache found."
    fi
    exit 0
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: scan-packages.sh [OPTIONS]"
    echo ""
    echo "Scan bash history for installed packages (apt, brew, pip, choco, etc.) and cache them."
    echo ""
    echo "Options:"
    echo "  --foreground  Run in foreground and print the package cache"
    echo "  --cleanup     Delete the package list cache file"
    echo "  -h, --help    Show this help message and exit"
    exit 0
fi
[[ "${1:-}" == "--foreground" ]] && FOREGROUND=true

HISTFILE_PATH="${HISTFILE:-$HOME/.bash_history}"
CACHE_DIR="$HOME/.cache"
CACHE_FILE="$CACHE_DIR/installed-packages.txt"

mkdir -p "$CACHE_DIR"

_GREEN='\033[0;32m'; _CYAN='\033[0;36m'; _YELLOW='\033[1;33m'; _RST='\033[0m'
log() { $FOREGROUND && printf "$1\n" || true; }

case "$(uname -s)" in
    MINGW*|CYGWIN*|MSYS*) PLATFORM="windows" ;;
    Linux*)               PLATFORM="linux"   ;;
    Darwin*)              PLATFORM="mac"     ;;
    *)                    PLATFORM="unknown" ;;
esac

log "${_CYAN}Scanning history: ${HISTFILE_PATH}${_RST}"

[ ! -f "$HISTFILE_PATH" ] && log "${_YELLOW}No history file: ${HISTFILE_PATH}${_RST}" && exit 0

TMPFILE=$(mktemp)

grep_history() {
    grep -E "$1" "$HISTFILE_PATH" 2>/dev/null | sed 's/^[[:space:]]*//' | grep -v '^#' | sort -u
}

extract_pkgs() {
    # Extract package names: skip first N words (cmd + subcommand), ignore flags
    grep_history "$1" | awk -v s="${2:-2}" '{for(i=s+1;i<=NF;i++) if($i !~ /^-/) print $i}' | sort -u
}

{
    if [[ "$PLATFORM" == "linux" || "$PLATFORM" == "mac" ]]; then
        APT=$(extract_pkgs '(apt|apt-get)[[:space:]]+(install)' 2)
        [ -n "$APT" ] && { echo "=== apt packages ==="; echo "$APT"; echo ""; }
        SNAP=$(extract_pkgs 'snap[[:space:]]+install' 2)
        [ -n "$SNAP" ] && { echo "=== snap packages ==="; echo "$SNAP"; echo ""; }
    fi
    if [[ "$PLATFORM" == "mac" || "$PLATFORM" == "linux" ]]; then
        BREW=$(extract_pkgs 'brew[[:space:]]+install' 2)
        [ -n "$BREW" ] && { echo "=== brew packages ==="; echo "$BREW"; echo ""; }
    fi
    if [[ "$PLATFORM" == "windows" ]]; then
        CHOCO=$(extract_pkgs 'choco[[:space:]]+install' 2)
        [ -n "$CHOCO" ] && { echo "=== choco packages ==="; echo "$CHOCO"; echo ""; }
        WINGET=$(extract_pkgs 'winget[[:space:]]+install' 2)
        [ -n "$WINGET" ] && { echo "=== winget packages ==="; echo "$WINGET"; echo ""; }
    fi
    PIP=$(extract_pkgs '(pip|pip3)[[:space:]]+(install)' 2)
    [ -n "$PIP" ] && { echo "=== pip packages ==="; echo "$PIP"; echo ""; }
    NPM_RAW=$(grep_history 'npm[[:space:]]+(install|i)[[:space:]].*(-g|--global)')
    if [ -n "$NPM_RAW" ]; then
        NPM_CLEAN=$(echo "$NPM_RAW" | awk '{for(i=3;i<=NF;i++) if($i !~ /^-/) print $i}' | sort -u | grep -v '^\s*$')
        [ -n "$NPM_CLEAN" ] && { echo "=== npm global packages ==="; echo "$NPM_CLEAN"; echo ""; }
    fi
    CARGO=$(extract_pkgs 'cargo[[:space:]]+install' 2)
    [ -n "$CARGO" ] && { echo "=== cargo packages ==="; echo "$CARGO"; echo ""; }
    echo "# Generated: $(date '+%Y-%m-%d %H:%M:%S') | Platform: $PLATFORM"
} > "$TMPFILE"

mv "$TMPFILE" "$CACHE_FILE"

if $FOREGROUND; then
    printf "${_GREEN}Package cache updated: ${CACHE_FILE}${_RST}\n\n"
    cat "$CACHE_FILE"
fi