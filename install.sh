#!/usr/bin/env bash
# install.sh — Install shell-kit dotfiles via symlinks (or copies on Windows without dev mode)
# Usage: bash install.sh

set -uo pipefail

PROFILE="desktop"
# Auto-detect if running inside an SSH session
if [ -n "${SSH_CONNECTION:-}" ] || [ -n "${SSH_CLIENT:-}" ] || [ -n "${SSH_TTY:-}" ]; then
    PROFILE="server"
fi

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)
            PROFILE="server"
            shift
            ;;
        --desktop)
            PROFILE="desktop"
            shift
            ;;
        -h|--help)
            echo "Usage: install.sh [OPTIONS]"
            echo ""
            echo "Install shell-kit dotfiles via symlinks (or copies on Windows without dev mode)."
            echo ""
            echo "Options:"
            echo "  --server      Install only server-compatible configurations (skips desktop-only files)"
            echo "  --desktop     Install all configurations (default, unless SSH session is detected)"
            echo "  -h, --help    Show this help message and exit"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO_DIR/manifest.json"

_GREEN='\033[0;32m'
_YELLOW='\033[1;33m'
_RED='\033[0;31m'
_CYAN='\033[0;36m'
_BOLD='\033[1m'
_RST='\033[0m'

# Detect platform
case "$(uname -s)" in
    MINGW*|CYGWIN*|MSYS*) PLATFORM="windows" ;;
    Linux*)               PLATFORM="linux"   ;;
    Darwin*)              PLATFORM="mac"     ;;
    *)                    PLATFORM="unknown" ;;
esac

printf "${_CYAN}${_BOLD}shell-kit installer${_RST}\n"
printf "${_CYAN}Platform: ${PLATFORM}${_RST}\n"
printf "${_CYAN}Profile:  ${PROFILE}${_RST}\n"
printf "${_CYAN}Repo:     ${REPO_DIR}${_RST}\n\n"

# Check if symlinks work on Windows (requires Developer Mode)
CAN_SYMLINK=true
if [ "$PLATFORM" = "windows" ]; then
    TESTLINK="$HOME/.shell-kit-symlink-test"
    TESTTARGET="$REPO_DIR/manifest.json"
    ln -sf "$TESTTARGET" "$TESTLINK" 2>/dev/null && rm -f "$TESTLINK" || CAN_SYMLINK=false
    if ! $CAN_SYMLINK; then
        printf "${_YELLOW}[WARNING] Symlinks unavailable (Windows Developer Mode may be off).${_RST}\n"
        printf "${_YELLOW}          Falling back to file copies. Enable Developer Mode for symlinks.${_RST}\n\n"
    fi
fi

install_file() {
    local src="$1"       # full path in repo
    local target="$2"    # full path at destination
    local executable="${3:-false}"

    # Expand ~ manually
    target="${target/#\~/$HOME}"

    local target_dir
    target_dir="$(dirname "$target")"
    mkdir -p "$target_dir"

    # Backup if exists and is not already our symlink
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        mv "$target" "${target}.bak"
        printf "  ${_YELLOW}[BACKUP] Backed up: ${target}.bak${_RST}\n"
    elif [ -L "$target" ]; then
        rm -f "$target"
    fi

    if $CAN_SYMLINK; then
        ln -sf "$src" "$target"
        printf "  ${_GREEN}[LINKED] Linked:   $(basename "$target")${_RST}  →  $src\n"
    else
        cp "$src" "$target"
        printf "  ${_GREEN}[COPIED] Copied:   $(basename "$target")${_RST}\n"
    fi

    if [ "$executable" = "true" ]; then
        chmod +x "$target" 2>/dev/null || true
    fi
}

# Ensure ~/.local/bin is in PATH
mkdir -p "$HOME/.local/bin"

# Read manifest and install each file
# We parse JSON manually (no jq needed — pure bash)
if command -v python3 &>/dev/null; then
    # Use python3 to parse JSON if available
    INSTALL_LINES_RAW=$(python3 - "$MANIFEST" "$PLATFORM" "$REPO_DIR" "$PROFILE" <<'PYEOF' | tr -d '\r'
import sys, json

manifest_path, platform, repo_dir, profile = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

with open(manifest_path) as f:
    manifest = json.load(f)

for entry in manifest["files"]:
    src = entry["src"]
    targets = entry.get("targets", {})
    executable = str(entry.get("executable", False)).lower()
    target = targets.get(platform) or targets.get("linux")
    entry_profile = entry.get("profile", "both")
    
    # Skip desktop-only files in server installations
    if profile == "server" and entry_profile == "desktop":
        continue
        
    if target:
        print(f"{repo_dir}/{src}|{target}|{executable}")
PYEOF
)
    mapfile -t INSTALL_LINES <<< "$INSTALL_LINES_RAW"
    for line in "${INSTALL_LINES[@]:-}"; do
        IFS='|' read -r src target executable <<< "$line"
        install_file "$src" "$target" "$executable"
    done
else
    # Fallback: hardcoded from manifest
    install_file "$REPO_DIR/bash/.bashrc"           "~/.bashrc"                        false
    install_file "$REPO_DIR/bash/.bash_profile"     "~/.bash_profile"                  false
    install_file "$REPO_DIR/bash/.bash_function"    "~/.bash_function"                 false
    install_file "$REPO_DIR/bash/.profile"          "~/.profile"                       false
    install_file "$REPO_DIR/scripts/history-clean.sh"         "~/.local/bin/history-clean.sh"         true
    install_file "$REPO_DIR/scripts/setup-codebase-memory.sh" "~/.local/bin/setup-codebase-memory.sh" true
    install_file "$REPO_DIR/scripts/scan-packages.sh"         "~/.local/bin/scan-packages.sh"         true
fi

printf "\n${_GREEN}${_BOLD}[OK] Installation complete!${_RST}\n"
printf "  Open a new terminal to apply changes.\n\n"
