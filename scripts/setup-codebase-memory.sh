#!/usr/bin/env bash

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: setup-codebase-memory.sh [uninstall | OPTIONS]"
    echo ""
    echo "Install or uninstall codebase-memory-mcp."
    echo ""
    echo "Commands:"
    echo "  uninstall     Uninstall codebase-memory-mcp"
    echo ""
    echo "Options:"
    echo "  --ui          Install Graph UI version"
    echo "  --skip-config Only install binary"
    echo "  --dir PATH    Custom installation directory"
    echo "  -h, --help    Show this help message and exit"
    exit 0
fi

REPO="DeusData/codebase-memory-mcp"
INSTALL_URL="https://raw.githubusercontent.com/${REPO}/main/install.sh"
INSTALL_PS_URL="https://raw.githubusercontent.com/${REPO}/main/install.ps1"

# Handle uninstall
if [[ "${1:-}" == "uninstall" ]]; then
    if command -v codebase-memory-mcp >/dev/null 2>&1; then
        echo "Uninstalling codebase-memory-mcp..."
        codebase-memory-mcp uninstall
        echo "Uninstall complete."
    elif [[ -x "$HOME/.local/bin/codebase-memory-mcp" ]]; then
        echo "Uninstalling codebase-memory-mcp..."
        "$HOME/.local/bin/codebase-memory-mcp" uninstall
        echo "Uninstall complete."
    else
        echo "codebase-memory-mcp not found."
        exit 1
    fi
    exit 0
fi

# Log file in current directory
LOG_FILE="$(pwd)/setup-codebase-memory-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Optional flags:
#   --ui            Install Graph UI version
#   --skip-config   Only install binary
#   --dir PATH      Custom installation directory

ARGS=("$@")

OS="$(uname -s)"

echo "Detected OS: $OS"

case "$OS" in
    Linux|Darwin)
        if ! command -v curl >/dev/null 2>&1; then
            echo "Error: curl is required."
            exit 1
        fi

        echo "Installing codebase-memory-mcp..."
        curl -fsSL "$INSTALL_URL" | bash -s -- $@
        ;;

    MINGW*|MSYS*|CYGWIN*)
        if command -v powershell.exe >/dev/null 2>&1; then
            powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
                "iwr '$INSTALL_PS_URL' -OutFile install.ps1; ./install.ps1 $($ARGS)"
        else
            echo "Please run the Windows PowerShell installer:"
            echo ""
            echo "Invoke-WebRequest -Uri $INSTALL_PS_URL -OutFile install.ps1"
            echo ".\\install.ps1"
            exit 1
        fi
        ;;

    *)
        echo "Unsupported operating system: $OS"
        exit 1
        ;;
esac

echo
echo "Installation complete."
echo "Log saved to: $LOG_FILE"